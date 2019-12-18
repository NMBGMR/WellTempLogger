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
import os
from datetime import datetime
import time
import serial
import pyvisa

WELCOME = """
Well Temp Logger

by Jake Ross (2019)
 
"""

DEVICE_ID = 'GPIB0::22::INSTR'
SIGNAL_DEV_ADDR = 'COM1'


class MockDevice:
    def query(self, cmd):
        return -1


class SignalDevice:
    _handle = None
    cts = True
    def open(self):
        try:
            self._handle = serial.Serial(SIGNAL_DEV_ADDR)
            return True
        except serial.SerialException:
            return True

    def active(self):
        if self._handle:
            return self._handle.cts

    def report_pin_states(self):
        if self._handle:
            for a in ('cts', 'dsr', 'ri', 'cd'):
                print('{:<3s}={}'.format(a, getattr(self._handle, a)))


def welcome():
    print(WELCOME)


def open_device():
    rm = pyvisa.ResourceManager()
    res = rm.list_resources()
    if DEVICE_ID not in res:
        print('DeviceID={}'.format(DEVICE_ID))
        print('Available Resources={}'.format(res))
    else:
        inst = rm.open_resource(DEVICE_ID)
        return inst


def open_signal_device():
    dev = SignalDevice()
    if dev.open():
        return dev


def start_logging(dev, signal_device):
    # setup output file
    root = 'data'
    p = 'wt-{}.csv'.format(datetime.now().isoformat())
    if not os.path.isdir(root):
        os.mkdir(root)

    p = os.path.join(root, p)

    counter = 0
    starttime = time.time()
    while 1:
        if wait_for_signal(signal_device):
            value = read_device(dev)
            if counter == 0:
                row = assemble_header()
                write_row(p, row)
                report_line(row)

            row = assemble_row(counter, value, starttime)
            write_row(p, row)
            report_row(row)
            counter += 1
            time.sleep(1)


def wait_for_signal(signal_device):
    st = time.time()
    timeout = 100

    while 1:
        if time.time() - st > timeout:
            break

        signal_device.report_pin_states()

        if signal_device.cts:
            return True

        time.sleep(0.01)


def read_device(dev, verbose=False):
    ret = dev.query('MEAS:VOLT:DC?')
    if verbose:
        print('query={}'.format(ret))
    return float(ret)


def assemble_header():
    return ['counter', 'time', 'rate', 'datetime', 'raw_value', 'temp']


def assemble_row(counter, value, starttime):
    t = time.time() - starttime
    r = counter / t
    row = [counter, t, r, datetime.now().isoformat(), value]
    return row


def report_row(row):
    c = '{:09n}'.format(row[0])
    t = '{:0.1f}'.format(row[1])
    r = '{:0.1f}'.format(row[2])
    dt = '{}'.format(row[3])
    v = '{}'.format(row[4])
    temp = '{}'.format(convert_to_temp(row[4]))
    report_line((c, t, r, dt, v, temp))


def report_line(row):
    print('{:<10s}{:<10s}{:<10s}{:<30s}{:<20s}{:<10s}'.format(*row))


def write_row(p, row):
    with open(p, 'a') as wfile:
        line = ','.join([str(r) for r in row])
        wfile.write('{}\n'.format(line))


def convert_to_temp(v):
    a = 10
    b = 100
    return v*a+b


def warning(msg):
    print('*************** {} ***************'.format(msg))


def main():
    welcome()
    dev = open_device()
    if dev:
        sd = open_signal_device()
        if sd:
            start_logging(dev, sd)
        else:
            warning('Failed to connect to Signal Device')


if __name__ == '__main__':
    main()
# ============= EOF =============================================
