# ===============================================================================
# Copyright 2019 ross
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ===============================================================================
from traits.api import HasTraits, Float, Int, Bool
from pyface.api import warning
import random
from datetime import datetime
import platform
import time
import pyvisa
import serial
import math


class Device(HasTraits):
    _handle = None

    def open(self):
        raise NotImplementedError


class SignalDevice(Device):
    period = Float(0.01, auto_set=False, enter_set=True)

    def __init__(self):
        if platform.system == 'Windows':
            self.device_id = 'UC-232A'
        else:
            self.device_id = '/dev/tty.UC-232A'

    def open(self):
        try:
            self._handle = serial.Serial(self.device_id)
            return True
        except serial.SerialException:
            warning(None, 'Triggering device {} not available. Please check connections'.format(self.device_id))

    def waitfor(self):
        if self._handle:
            while 1:
                if self._handle.dsr:
                    return True

                time.sleep(self.period)


class VisaDevice(Device):
    def open(self):
        rm = pyvisa.ResourceManager()
        res = rm.list_resources()
        if self.device_id not in res:
            print('DeviceID={}'.format(self.device_id))
            print('Available Resources={}'.format(res))
            warning(None, 'Device: {} not available. Please check connections'.format(self.device_id))
        else:
            inst = rm.open_resource(self.device_id)
            self._handle = inst
            self._configure()
            return True

    def _configure(self):
        pass


class MeasurementDevice(VisaDevice):
    counter = 0
    starttime = 0
    device_id = 'GPIB0::22::INSTR'
    npoints = Int(10)
    use_air_calibration = Bool(True)
    rate = Float
    def init(self):
        if not self.counter:
            self.starttime = time.time()

    def reset(self):
        self.counter = 0
        self.starttime = time.time()

    def _configure(self):
        self._handle.write('CONF:FRES 1MOHM, 0.000001MOHM')
        self._handle.write('SENSE:FRES:NPLC {}'.format(self.npoints))

    def get_measurement(self):
        self.counter += 1

        t = time.time() - self.starttime
        r = self.counter / t
        self.rate = r
        value = self._read()
        row = [self.counter, t, r, datetime.now().isoformat(), value, self._convert_to_temp(value)]

        return row

    # private
    def _convert_to_temp(self, v):
        if self.use_air_calibration:
            a = -39.74119491
            c = 573.6081692
            v = a*math.log(v)+c
        else:
            a = 1233.19043
            b = -192.56687
            c = 10.78172
            d = -0.24088
            x=math.log(v)
            v = a+b*x+c*x**2+d*x**3
            
        return v

    def _read(self):
        try:
            return float(self._handle.query('READ?'))
        except BaseException as e:
            print('failed reading from device, Error:{}'.format(e))
            return random.random()


class CalibrationDevice(VisaDevice):
    device_id = 'GPIB::23:INSTR'

    def _configure(self):
        pass

    def get_measurement(self):
        return random.random()
# ============= EOF =============================================
