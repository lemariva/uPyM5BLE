# test of printing multiple fonts to the ILI9341 on an M5Stack using H/W SP
# MIT License; Copyright (c) 2017 Jeffrey N. Magee
import time
import random
import struct
import bluetooth
from machine import Pin, SPI
from micropython import const
from ble_advertising import advertising_payload

import m5stack
from uPySensors.ili934xnew import ILI9341, color565
from uPySensors.mpu9250 import MPU9250

import uPySensors.fonts.tt24 as tt24

_IRQ_CENTRAL_CONNECT                 = const(1 << 0)
_IRQ_CENTRAL_DISCONNECT              = const(1 << 1)

_DEVICE_UUID = bluetooth.UUID(0x180A)

_IMU_UUID = bluetooth.UUID('d9d55001-0525-4e5c-be77-afada8e04e14')
_ACCEL_CHAR = (bluetooth.UUID('d9d55002-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_READ,)
_MAG_CHAR = (bluetooth.UUID('d9d55003-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_READ,)
_GYRO_CHAR = (bluetooth.UUID('d9d55004-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_READ,)
_TEMP_CHAR = (bluetooth.UUID('d9d55005-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_READ|bluetooth.FLAG_NOTIFY,)
_IMU_SERVICES = (_IMU_UUID, (_ACCEL_CHAR, _MAG_CHAR, _GYRO_CHAR, _TEMP_CHAR,),)

_KEYS_UUID = bluetooth.UUID('d9d55010-0525-4e5c-be77-afada8e04e14')
_KEYS_CHAR = (bluetooth.UUID('d9d55011-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_READ|bluetooth.FLAG_NOTIFY,)
_KEYS_SERVICES = (_KEYS_UUID, (_KEYS_CHAR,),)

_DISPLAY_UUID = bluetooth.UUID('d9d55015-0525-4e5c-be77-afada8e04e14')
_DISPLAY_ON_CHAR = (bluetooth.UUID('d9d55016-0525-4e5c-be77-afada8e04e14'), bluetooth.FLAG_WRITE,)
_DISPLAY_SERVICES = (_DISPLAY_UUID, (_DISPLAY_ON_CHAR,),)

SERVICES =  (_IMU_SERVICES, _KEYS_SERVICES, _DISPLAY_SERVICES)

_ADV_APPEARANCE_MPU9250 = const(1088)

class M5StackBLE:
    def __init__(self, ble, name='mpy-m5stack'):
        self._ble = ble
        self._ble.active(True)
        self._ble.irq(handler=self._irq)
        
        ((self._handle_accel, self._handle_mag, self._handle_gyro, self._handle_temp), 
            (self._handle_keys,),
            (self._handle_display,),) = self._ble.gatts_register_services(SERVICES)

        self._connections = set()
        self._payload = advertising_payload(name=name, services=[_DEVICE_UUID], appearance=_ADV_APPEARANCE_MPU9250)
        self._advertise()

    def _irq(self, event, data):
        # Track connections so we can send notifications.
        if event == _IRQ_CENTRAL_CONNECT:
            conn_handle, _, _, = data
            self._connections.add(conn_handle)
        elif event == _IRQ_CENTRAL_DISCONNECT:
            conn_handle, _, _, = data
            self._connections.remove(conn_handle)
            # Start advertising again to allow a new connection.
            self._advertise()

    def update_data(self, accel, mag, gyro, temp, keys, notify=False):
        # Write the local value, ready for a central to read.
        accel_data = struct.pack('@hhh', int(accel.x * 100), int(accel.y * 100), int(accel.z * 100))
        mag_data = struct.pack('@iii', int(mag.x * 100), int(mag.y * 100), int(mag.z * 100))
        gyro_data = struct.pack('@iii', int(gyro.x * 100), int(gyro.y * 100), int(gyro.z * 100))
        temp_data = struct.pack('@h', int(temp * 100))
        keys_data = struct.pack('@hhh', int(keys[0]), int(keys[1]), int(keys[2]))
        self._ble.gatts_write(self._handle_accel, accel_data)
        self._ble.gatts_write(self._handle_mag, mag_data)
        self._ble.gatts_write(self._handle_gyro, gyro_data)
        self._ble.gatts_write(self._handle_temp, temp_data)
        self._ble.gatts_write(self._handle_keys, keys_data)
        # Read data from central
        display_data = self._ble.gatts_read(self._handle_display)
        display_data = int.from_bytes(display_data, "big")

        if notify:
            for conn_handle in self._connections:
                # Notify connected centrals to issue a read.
                self._ble.gatts_notify(conn_handle, self._handle_temp)
                self._ble.gatts_notify(conn_handle, self._handle_keys)

        return display_data        

    def _advertise(self, interval_us=500000):
        self._ble.gap_advertise(interval_us, adv_data=self._payload)

## Display
power = Pin(m5stack.TFT_LED_PIN, Pin.OUT)
power.value(1)
spi = SPI(2, baudrate=40000000, 
        miso=Pin(m5stack.TFT_MISO_PIN), 
        mosi=Pin(m5stack.TFT_MOSI_PIN),
        sck=Pin(m5stack.TFT_CLK_PIN))

display = ILI9341(spi,
        cs=Pin(m5stack.TFT_CS_PIN),
        dc=Pin(m5stack.TFT_DC_PIN),
        rst=Pin(m5stack.TFT_RST_PIN),
        w=240,
        h=320,
        r=6,
        font=tt24)

display.erase()
display.set_pos(0,0)

## MPU9250
sensor = MPU9250(-1, dev_pin=(m5stack.MPU9250_SCL_PIN, m5stack.MPU9250_SDA_PIN))
sensor.accel_range = 0
sensor.gyro_range = 1
sensor.filter_range = 1

## BLUETOOTH
ble = bluetooth.BLE()
ble_module = M5StackBLE(ble)

# KEYS
key_a = Pin(m5stack.BUTTON_A_PIN, Pin.IN)
key_b = Pin(m5stack.BUTTON_B_PIN, Pin.IN)
key_c = Pin(m5stack.BUTTON_C_PIN, Pin.IN)

while True:
    # Read acceleration
    
    accel = sensor.accel
    mag = sensor.mag
    gyro = sensor.gyro
    temp = sensor.temperature
    keys = (key_a.value(), key_b.value(), key_c.value())
    display_on = ble_module.update_data(accel, mag, gyro, temp, keys, True)
    power.value(display_on)

    if(display_on == 1):
        display.set_pos(0,0)
        display.print("Accelerometer:")
        display.set_pos(0,30)
        display_text = "x:%0.3f, y:%0.3f, z:%0.3f" % (accel.x, accel.y, accel.z)
        display.print(display_text)
        display.set_pos(0,60)
        display.print("Magnetometer:")
        display.set_pos(0,90)
        display_text = "x:%0.1f, y:%0.1f, z:%0.1f" % (mag.x, mag.y, mag.z)
        display.print(display_text)
        display.print("Gyroscope:")
        display.set_pos(0,120)
        display_text = "x:%0.1f, y:%0.1f, z:%0.1f" % (gyro.x, gyro.y, gyro.z)
        display.print(display_text)
    
    time.sleep_ms(1)



