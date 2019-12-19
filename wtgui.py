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
from datetime import datetime
import os

from chaco.chaco_plot_editor import ChacoPlotItem
from numpy import hstack
from pyface.timer.do_later import do_after, do_later
from traits.api import HasTraits, Button, Float, File, Bool, Str, Array, Int, Instance
from traitsui.api import View, UItem, HGroup, VGroup, Item, Readonly

from src.device import SignalDevice, MeasurementDevice

DEBUG = True


class MainWindow(HasTraits):
    start_button = Button('Start')
    stop_button = Button('Stop')
    reset_button = Button('Reset')
    last_measurement = Str
    output_path = File
    post_measurement_delay = Float(0.05, auto_set=False, enter_set=True)

    npoints = Int
    _scan_thread = None

    _alive = Bool
    measurement_device = None
    signal_device = Instance(SignalDevice, ())

    xs = Array
    ys = Array
    ts = Array
    # private
    _initialized = False

    def _start_button_fired(self):
        if self._initialize_output_file():
            if self._initialize_devices():
                self.measurement_device.reset()
                self._start_scan()

    def _stop_button_fired(self):
        self._alive = False

    def _reset_button_fired(self):
        if self.measurement_device:
            self.measurement_device.reset()

    def _start_scan(self):
        self._alive = True
        do_later(self._scan)

    def _initialize_output_file(self):

        if not self.output_path:
            self.output_path = os.path.join('data', '{}.csv'.format(datetime.now().isoformat()))

        root = os.path.dirname(self.output_path)
        if not os.path.isdir(root):
            os.mkdir(root)
        return True

    def _initialize_devices(self):
        if not self._initialized:
            self.measurement_device = MeasurementDevice()

            if self.signal_device.open():
                if self.measurement_device.open():
                    return True
            if DEBUG:
                return True
        else:
            return True

    def _scan(self):

        self._iteration()
        if self._alive:
            do_after(self.post_measurement_delay*1000, self._scan)

    def _iteration(self):
        if self.signal_device.waitfor() or DEBUG:
            measurement = self.measurement_device.get_measurement()
            if measurement:
                self._report_measurement(measurement)
                self._write_measurement(measurement)
                self._plot_measurement(measurement)

    def _plot_measurement(self, ms):
        self.xs = hstack((self.xs, [-ms[0]]))
        self.ys = hstack((self.ys, [ms[-2]]))
        self.ts = hstack((self.ts, [ms[-1]]))

    def _report_measurement(self, row):
        fmt = '{:<10s}{:<10s}{:<10s}{:<30s}{:<20s}{:<10s}'

        c = '{:09n}'.format(row[0])
        t = '{:0.1f}'.format(row[1])
        r = '{:0.1f}'.format(row[2])
        dt = '{}'.format(row[3])
        v = '{}'.format(row[4])
        temp = '{}'.format(row[5])

        msg = fmt.format(c, t, r, dt, v, temp)
        print(msg)
        self.last_measurement = msg

    def _write_measurement(self, row):
        with open(self.output_path, 'a') as wfile:
            line = ','.join([str(r) for r in row])
            wfile.write('\n'.format(line))


tgrp = HGroup(UItem('start_button', enabled_when='not _alive'),
              UItem('stop_button', enabled_when='_alive'),
              UItem('reset_button', enabled_when='not _alive'),
              Readonly('last_measurement'))
cgrp = HGroup(Item('post_measurement_delay'), Item('object.signal_device.period'))
pgrp = VGroup(ChacoPlotItem('xs', 'ys',
                            resizable=True,
                            orientation='v',
                            x_label='Depth',
                            y_label='Signal(ohm)',
                            color='blue',
                            bgcolor='white',
                            border_visible=True,
                            border_width=1,
                            padding_bg_color='lightgray',
                            width=800,
                            height=380,
                            marker_size=2,
                            title='',
                            show_label=False),
              ChacoPlotItem('xs', 'ts',
                            resizable=True,
                            orientation='v',
                            x_label='Depth',
                            y_label='Temp C',
                            color='blue',
                            bgcolor='white',
                            border_visible=True,
                            border_width=1,
                            padding_bg_color='lightgray',
                            width=800,
                            height=380,
                            marker_size=2,
                            title='',
                            show_label=False))

view = View(VGroup(tgrp, cgrp, pgrp), resizable=True,
            width=900)

if __name__ == '__main__':
    m = MainWindow()
    m.configure_traits(view=view)
# ============= EOF =============================================
