# uPyM5BLE
This project is about using the BLE module of an M5Stack running MicroPython. 

The [M5Stack official](https://github.com/m5stack/M5Stack_MicroPython) and [LoBo](https://github.com/loboris/MicroPython_ESP32_psRAM_LoBo/) MicroPython stacks still do not support BLE. However, the [official firmware version](http://micropython.org/download#esp32) built with ESP-IDF v4.x has support for BLE (but no for LAN or PPP). 

This project is a code example, which reads the IMU information (in my case an [MPU9250](https://www.invensense.com/products/motion-tracking/9-axis/mpu-9250/) -this varies depending on the M5Stack version) and the button statues, and then publishes and notifies the values using BLE. Furthermore, it offers a write position, which controls the display status (on/off). 

## MicroPython
Download the version [GENERIC-SPIRAM (built with ESP-IDF v4.x)](http://micropython.org/resources/firmware/esp32spiram-idf4-20191220-v1.12.bin) -for M5Stacks with 16MB RAM- and program your board using the [esptool.py](https://github.com/espressif/esptool) program. If you are flashing MicroPython on your board for the first time then you should first erase the entire flash using:

```
esptool.py --chip esp32 --port /dev/ttyUSB0 erase_flash
```
Then, program the firmware starting at address 0x1000 using e.g.:

```
esptool.py --chip esp32 --port /dev/ttyUSB0 --baud 460800 write_flash -z 0x1000 esp32spiram-idf4-20191220-v1.12.bin
```

## Upload the Project
Clone the repository using:
```
git clone --recursive https://github.com/lemariva/uPyM5BLE.git
```
and use [VSCode](https://code.visualstudio.com/) and the PyMakr extension to upload the project to the M5Stack. A tutorial is available [here](https://lemariva.com/blog/2018/12/micropython-visual-studio-code-as-ide).

## Read and write data from/to the device
The device can have a fixed MAC address (e.g. PYBD) or a random address (e.g. ESP32). Thus, to connect to the M5Stack, I use the [BLE Scanner](https://play.google.com/store/apps/details?id=com.macdom.ble.blescanner&hl=de). The application searches for BLE devices, and lets you read data (see Fig. 1) and write values (see Fig. 2). Additionally, you can see the MAC address of the device (see Fig. 3). 

The read values included in this example are from:
* 3-axis accelerometer - 3 shorts & accuracy 0.01g
* 3-axis magnetometer - 3 ints & accuracy 0.01uT
* 3-axis gyroscope - 3 ints & accuracy 0.01°/s
* Temperature sensor - 1 short & accuracy 0.01°C
* Button A, B and C statues.

| |
|:--|
|![BLE Scanner](images/ble_scanner_read.png?raw=true "BLE Scanner")|
|Fig. 1: BLE Scanner Application - Reading data from the M5Stack|

| |
|:--|
|![BLE Scanner](images/ble_scanner_write.png?raw=true "BLE Scanner")|
|Fig. 2: BLE Scanner Application - Writing a variable value|

| |
|:--|
|![BLE Scanner](images/ble_scanner_mac.png?raw=true "BLE Scanner")|
|Fig. 2: BLE Scanner Application - Getting Device MAC address|

## Extra 

Other examples are included inside the folder `ble_examples`. These were taken from the [MicroPython official repository](https://github.com/micropython/micropython/tree/master/examples/bluetooth).

Additional information about the `ubluetooth` module can be found [here](https://docs.micropython.org/en/latest/library/ubluetooth.html).
