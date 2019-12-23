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
from traits.api import HasTraits, Float, Int, Array, Button, Instance
from traitsui.api import View, VGroup, UItem
from chaco.chaco_plot_editor import ChacoPlotItem
from enable.api import Component, ComponentEditor
from chaco.api import DataView, ArrayDataSource, ScatterPlot, \
                      LinePlot, LinearMapper
import random
from datetime import datetime
import platform
import time
import pyvisa
import serial
from numpy import hstack, linspace, polyval, polyfit


class Calibrator(HasTraits):
    trigger_button = Button('Trigger')
    
    xs= ArrayDataSource
    ys = ArrayDataSource
    
    fx = ArrayDataSource
    fy = ArrayDataSource
    
    plot = Instance(Component)
    def _plot_default(self):
        x=[]
        y=[]
        y2=[]
        view = DataView(border_visible = True)
        scatter = ScatterPlot(index = ArrayDataSource(x),
                              value = ArrayDataSource(y),
                              marker = "square",
                              color = "red",
                              outline_color = "transparent",
                              index_mapper = LinearMapper(range=view.index_range),
                              value_mapper = LinearMapper(range=view.value_range))

        line = LinePlot(index = ArrayDataSource([]),
                        value = ArrayDataSource([]),
                        color = "blue",
                        index_mapper = LinearMapper(range=view.index_range),
                        value_mapper = LinearMapper(range=view.value_range))

        # Add the plot's index and value datasources to the dataview's
        # ranges so that it can auto-scale and fit appropriately
        view.index_range.sources.append(scatter.index)
        view.value_range.sources.append(scatter.value)
        view.value_range.sources.append(line.value)

        # Add the renderers to the dataview.  The z-order is determined
        # by the order in which renderers are added.
        view.add(scatter)
        view.add(line)
        self.xs = scatter.index
        self.ys = scatter.value
        self.fx = line.index
        self.fy = line.value
        return view
    def _trigger(self):
        y1 = self._get_a()    
        y2 = self._get_b()
        y2 = y1*3+y2
        self._record_point(y1, y2)
        self._plot_point(y1, y2)
    
    def _record_point(self, y1, y2):
        pass
    
    def _plot_point(self, y1, y2):
        self.xs.set_data(hstack((self.xs.get_data(), [y1])))
        self.ys.set_data(hstack((self.ys.get_data(), [y2])))
        
        # fit data
        self._fit()
        
    def _fit(self):
        
        xs = self.xs.get_data()
        if len(xs)>2:
            ys = self.ys.get_data()
            fx = linspace(min(xs)*0.9, max(xs)*1.1)
            coeffs = polyfit(xs, ys, 2)
            fy = polyval(coeffs, fx)
            self.fx.set_data(fx)
            self.fy.set_data(fy)
    
    def _get_a(self):
        return random.random()
    
    def _get_b(self):
        return random.random()
    
    def _trigger_button_fired(self):
        self._trigger()
        
    def traits_view(self):
        v = View(VGroup(UItem('trigger_button'),
                       UItem('plot', editor=ComponentEditor())
                       ),
                title='Calibtator'
                )
        return v
# ============= EOF =============================================
