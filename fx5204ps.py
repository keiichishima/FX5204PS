#!/usr/bin/env python
# -*- coding: utf-8 -*-

import copy
import datetime
import struct
import threading

import usb.core
import usb.util

VENDOR_FUJITSUCOMP           = 0x0430
PRODUCT_FUJITSUCOMP_FX5204PS = 0x0423

OUT_VENDOR_DEVICE = (usb.util.CTRL_OUT
                     |usb.util.CTRL_TYPE_VENDOR
                     |usb.util.CTRL_RECIPIENT_DEVICE)
IN_VENDOR_DEVICE  = (usb.util.CTRL_IN
                     |usb.util.CTRL_TYPE_VENDOR
                     |usb.util.CTRL_RECIPIENT_DEVICE)

CMD_START        = 0x01
CMD_VALUE        = 0x20
CMD_GET_FIRMWARE = 0xC0
CMD_GET_SERIAL   = 0xC1
CMD_GET_VOLTAGE  = 0xB0
CMD_GET_TEMP     = 0xB4
CMD_GET_FREQ     = 0xA1
CMD_GET_UNK0     = 0xA2

MODE_WATTAGE = 0x10
MODE_CURRENT = 0x30

class FX5204PS(threading.Thread):
    def __init__(self, update_interval=5):
        super(FX5204PS, self).__init__()
        self._stop_event = threading.Event()
        self._count = 0
        self._last_temp_check = 0
        self._device = self._find_device()
        self._firmware_version = [0, 0]
        self._serial_number = 0
        self._endpoint = None
        self._initialize()
        self._temperature = 0
        self._frequency = 0
        self._voltage = 0
        self._wattage = [0,0,0,0]
        self._wattage_max = [0,0,0,0]
        self._wattage_avg = [0,0,0,0]
        self._lock = threading.Lock()
        self._update_interval = datetime.timedelta(seconds=update_interval)
        self._last_sumup_time = datetime.datetime(1970,1,1)

    @property
    def firmware_version(self):
        return self._firmware_version

    @property
    def serial_number(self):
        return self._serial_number

    @property
    def temperature(self):
        with self._lock:
            return self._temperature / 100

    @property
    def frequency(self):
        with self._lock:
            return self._frequency / 1000000

    @property
    def voltage(self):
        with self._lock:
            return self._voltage

    @property
    def wattage(self):
        with self._lock:
            return [w / 100 for w in self._wattage]

    @property
    def wattage_max(self):
        with self._lock:
            return [w / 100 for w in self._wattage_max]

    @property
    def wattage_avg(self):
        with self._lock:
            return [w / 100 for w in self._wattage_avg]

    def stop(self):
        self._stop_event.set()
        self.join()

    def _find_device(self):
        dev = usb.core.find(idVendor=VENDOR_FUJITSUCOMP,
                            idProduct=PRODUCT_FUJITSUCOMP_FX5204PS)
        if dev is None:
            raise Exception('No FX5204PS device found.')
        return dev

    def _initialize(self):
        # FX5204PS has only one configuration set.
        cfg = self._device[0]
        self._device.set_configuration(cfg)
        # FX5204PS has only one Interface and one Alternate setting.
        iface = cfg[(0,0)]
        # FX5204PS has only one outbound endpoint.
        self._endpoint = iface[0]
        # Get the firmware version.
        fmv = self._device.ctrl_transfer(IN_VENDOR_DEVICE,
                                         CMD_GET_FIRMWARE, 0, 0, 2)
        self._firmware_version = [(v >> 4) * 10 + (v & 0x0F) for v in fmv]
        # Get the serial number.
        sno = [(v >> 4) * 10 + (v & 0x0F)
               for v
               in self._device.ctrl_transfer(IN_VENDOR_DEVICE,
                                             CMD_GET_SERIAL, 0, 0, 3)]
        self._serial_number = sno[0]*10000 + sno[1]*100 + sno[2]

    def run(self):
        while not self._stop_event.is_set():
            now = datetime.datetime.now()
            self._update_wattage()
            if (now - self._last_sumup_time > self._update_interval):
                self._update_wattage_avg()
                self._update_frequency()
                self._update_voltage()
                self._last_sumup_time = now

    def _update_wattage(self):
        data = self._endpoint.read(16)
        wattage = struct.unpack('!4H', data[8:])
        with self._lock:
            self._wattage = wattage
            if self._count == 0:
                self._wattage_avg = copy.copy(wattage)
                self._wattage_max = copy.copy(wattage)
            else:
                self._wattage_max = [self._wattage_max[i]
                                     if self._wattage_max[i] > wattage[i]
                                     else wattage[i]
                                     for i in range(len(wattage))]
        self._count += 1

    def _update_wattage_avg(self):
        with self._lock:
            self._wattage_avg = [(self._wattage[i]
                                  + (self._wattage_avg[i] * self._count))
                                 // (self._count + 1)
                                 for i in range(len(self._wattage))]
        self._count = 0

    def _update_frequency(self):
        data = self._device.ctrl_transfer(IN_VENDOR_DEVICE,
                                          CMD_GET_FREQ, 0, 0, 8)
        freq = 0
        if (data[6] == 0) and (data[7] == 0):
            freq = 0
        else:
            val = (data[1] << 8) + data[0]
            if val == 0:
                # XXX
                pass
            freq = 2000000
            freq *= 1000000
            freq //= val
        with self._lock:
            self._frequency = freq

    def _update_voltage(self):
        (volt,) = self._device.ctrl_transfer(IN_VENDOR_DEVICE,
                                             CMD_GET_VOLTAGE, 0, 0, 1)
        with self._lock:
            self._voltage = volt

if __name__ == '__main__':
    import time

    fx = FX5204PS()
    print('Firmware: {0}'.format(fx.firmware_version))
    print('Serial #: {0}'.format(fx.serial_number))
    fx.start()
    try:
        while True:
            time.sleep(1)
            print('Volt:  {0}V'.format(fx.voltage))
            print('Freq:  {0}Hz'.format(fx.frequency))
            print('Watt:  {0}W@0, {1}W@1, {2}W@2, {3}W@3'.format(*fx.wattage))
            print('(Avg): {0}W@0, {1}W@1, {2}W@2, {3}W@3'.format(*fx.wattage_avg))
            print('(Max): {0}W@0, {1}W@1, {2}W@2, {3}W@3'.format(*fx.wattage_max))
    except KeyboardInterrupt:
        fx.stop()
