#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2016 - 2018 Bas van Meerten and Wouter Franssen

# This file is part of ssNake.
#
# ssNake is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# ssNake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with ssNake. If not, see <http://www.gnu.org/licenses/>.

import numpy as np
import matplotlib as mpl
import matplotlib.gridspec as gridspec
try:
    from PyQt5 import QtGui, QtCore, QtWidgets
except ImportError:
    from PyQt4 import QtGui, QtCore
    from PyQt4 import QtGui as QtWidgets

TIMELABELLIST = [u'[s]', u'[ms]', u'[μs]']
FREQLABELLIST = [u'[Hz]', u'[kHz]', u'[MHz]']

#########################################################################################################
# the class from which the 1d data is displayed, the operations which only edit the content of this class are for previewing


class PlotFrame(object):

    INVERT_X = True # Invert the x-axis when spectrum
    INVERT_Y = False # Invert the y-axis when spectrum
    GRID_PLOT = False # Grid plot for contour
    ZERO_SCROLL_ALLOWED = True # Scroll with respect to 0 on the y-axis
    
    def __init__(self, root, fig, canvas):
        self.root = root
        self.fig = fig
        self.canvas = canvas
        self.fig.clf()
        self.xminlim = -1
        self.xmaxlim = 1
        self.yminlim = -1
        self.ymaxlim = 1
        self.logx = False
        self.logy = False
        if self.GRID_PLOT:
            self.gs = gridspec.GridSpec(2, 2, width_ratios=[self.root.father.defaultWidthRatio, 1], height_ratios=[1, self.root.father.defaultHeightRatio])
            self.ax = self.fig.add_subplot(self.gs[2])
            if mpl.__version__[0] > '1':
                self.x_ax = self.fig.add_subplot(self.gs[0], sharex=self.ax, facecolor='none', frameon=False)
                self.y_ax = self.fig.add_subplot(self.gs[3], sharey=self.ax, facecolor='none', frameon=False)
            else:
                self.x_ax = self.fig.add_subplot(self.gs[0], sharex=self.ax, axisbg='none', frameon=False)
                self.y_ax = self.fig.add_subplot(self.gs[3], sharey=self.ax, axisbg='none', frameon=False)
            self.fig.subplots_adjust(hspace=0)
            self.fig.subplots_adjust(wspace=0)
            self.x_ax.axes.get_xaxis().set_visible(False)
            self.x_ax.axes.get_yaxis().set_visible(False)
            self.y_ax.axes.get_xaxis().set_visible(False)
            self.y_ax.axes.get_yaxis().set_visible(False)            
        else:
            self.ax = self.fig.add_subplot(111)
        self.leftMouse = False  # is the left mouse button currently pressed
        self.panX = None  # start position of dragging the spectrum
        self.panY = None  # start position of dragging the spectrum
        self.zoomX1 = None  # first corner of the zoombox
        self.zoomY1 = None  # first corner of the zoombox
        self.zoomX2 = None  # second corner of the zoombox
        self.zoomY2 = None  # second corner of the zoombox
        self.rect = [None, None, None, None]  # lines for zooming or peak picking
        self.rightMouse = False  # is the right mouse button currently pressed
        self.peakPick = False  # currently peakPicking (if 2 display cross)
        self.peakPickFunc = None  # the function that needs to be called after peakPicking
        # variables to be initialized

    def kill(self):
        pass

    def plotReset(self):  # this function needs to be overriden by the classes who inherit from PlotFrame
        pass

    ################
    # mouse events #
    ################

    def peakPickReset(self):
        if self.rect[0] is not None:
            try:
                self.rect[0].remove()
            except Exception:
                pass
            self.canvas.draw_idle()
        if self.rect[1] is not None:
            try:
                self.rect[1].remove()
            except Exception:
                pass
            self.canvas.draw_idle()
        self.rect = [None, None, None, None]
        self.peakPick = False
        self.peakPickFunc = None

    def scroll(self, event):
        zoomStep = self.root.father.defaultZoomStep
        event.step = event.step * zoomStep #Apply zoom sensitivity
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if modifiers == QtCore.Qt.ShiftModifier:
            self.altScroll(event)
        else:
            if self.rightMouse:
                if self.logx:
                    middle = (self.xmaxlim + self.xminlim) / 2.0
                    width = self.xmaxlim - self.xminlim
                else:
                    middle = (self.xmaxlim + self.xminlim) / 2.0
                    width = self.xmaxlim - self.xminlim
                if modifiers == QtCore.Qt.ControlModifier:
                    width = width * 0.6**event.step
                else:
                    width = width * 0.9**event.step
                if self.logx:
                    self.xmaxlim = np.exp(middle + width / 2.0)
                    self.xminlim = np.exp(middle - width / 2.0)
                else:
                    self.xmaxlim = middle + width / 2.0
                    self.xminlim = middle - width / 2.0
                if self.spec() > 0 and self.INVERT_X:
                    self.ax.set_xlim(self.xmaxlim, self.xminlim)
                else:
                    self.ax.set_xlim(self.xminlim, self.xmaxlim)
            else:
                noZeroScroll = not self.ZERO_SCROLL_ALLOWED or not self.root.father.defaultZeroScroll
                if noZeroScroll:
                    if self.logy:
                        middle = (np.log(self.ymaxlim) + np.log(self.yminlim)) / 2.0
                        width = np.log(self.ymaxlim) - np.log(self.yminlim)
                    else:
                        middle = (self.ymaxlim + self.yminlim) / 2.0
                        width = self.ymaxlim - self.yminlim
                    if modifiers == QtCore.Qt.ControlModifier:
                        width = width * 0.6**event.step
                    else:
                        width = width * 0.9**event.step
                    if self.logy:
                        self.ymaxlim = np.exp(middle + width / 2.0)
                        self.yminlim = np.exp(middle - width / 2.0)
                    else:
                        self.ymaxlim = middle + width / 2.0
                        self.yminlim = middle - width / 2.0
                else:
                    if modifiers == QtCore.Qt.ControlModifier:
                        self.ymaxlim *= 0.6**event.step
                        self.yminlim *= 0.6**event.step
                    else:
                        self.ymaxlim *= 0.9**event.step
                        self.yminlim *= 0.9**event.step
                self.ax.set_ylim(self.yminlim, self.ymaxlim)
                if self.INVERT_Y:
                    if self.spec(-2) > 0 :
                        self.ax.set_ylim(self.ymaxlim, self.yminlim)
            self.canvas.update()
            self.canvas.draw_idle()

    def altScroll(self, event):
        pass

    def altReset(self):
        pass

    def buttonPress(self, event):
        if event.button == 1 and not self.peakPick:
            self.leftMouse = True
            self.zoomX1 = event.xdata
            self.zoomY1 = event.ydata
        elif (event.button == 3) and event.dblclick:
            modifiers = QtWidgets.QApplication.keyboardModifiers()
            if modifiers == QtCore.Qt.ShiftModifier:
                self.altReset()
            else:
                self.plotReset()
        elif event.button == 3:
            self.rightMouse = True
            self.panX = event.xdata
            self.panY = event.ydata

    def buttonRelease(self, event):
        if event.button == 1:
            if self.peakPick:
                if self.rect[0] is not None:
                    try:
                        self.rect[0].remove()
                    finally:
                        self.rect[0] = None
                    if self.rect[1] is not None:
                        try:
                            self.rect[1].remove()
                        finally:
                            self.rect[1] = None
                    self.peakPick = False
                    idx = np.argmin(np.abs(self.line_xdata - event.xdata))
                    if self.peakPickFunc is not None:
                        self.peakPickFunc((idx, np.array(self.line_xdata).flatten()[idx], np.array(self.line_ydata).flatten()[idx]))
                    if not self.peakPick:  # check if peakpicking is still required
                        self.peakPickFunc = None
            else:
                self.leftMouse = False
                try:
                    if self.rect[0] is not None:
                        self.rect[0].remove()
                    if self.rect[1] is not None:
                        self.rect[1].remove()
                    if self.rect[2] is not None:
                        self.rect[2].remove()
                    if self.rect[3] is not None:
                        self.rect[3].remove()
                finally:
                    self.rect = [None, None, None, None]
                if self.zoomX2 is not None and self.zoomY2 is not None:
                    self.xminlim = min([self.zoomX1, self.zoomX2])
                    self.xmaxlim = max([self.zoomX1, self.zoomX2])
                    self.yminlim = min([self.zoomY1, self.zoomY2])
                    self.ymaxlim = max([self.zoomY1, self.zoomY2])
                    if self.spec() > 0 and self.INVERT_X:
                        self.ax.set_xlim(self.xmaxlim, self.xminlim)
                    else:
                        self.ax.set_xlim(self.xminlim, self.xmaxlim)
                    self.ax.set_ylim(self.yminlim, self.ymaxlim)
                    if self.INVERT_Y:
                        if self.spec(-2) > 0:
                            self.ax.set_ylim(self.ymaxlim, self.yminlim)
                self.zoomX1 = None
                self.zoomX2 = None
                self.zoomY1 = None
                self.zoomY2 = None
        elif event.button == 3:
            self.rightMouse = False
        self.canvas.draw_idle()

    def pan(self, event):
        modifiers = QtWidgets.QApplication.keyboardModifiers()
        if self.rightMouse and self.panX is not None and self.panY is not None:
            if self.logx or self.logy:
                x = event.xdata
                y = event.ydata
                if x is None or y is None:
                    return
            else:
                inv = self.ax.transData.inverted()
                point = inv.transform((event.x, event.y))
                x = point[0]
                y = point[1]
            if self.logx:
                diffx = np.log(x) - np.log(self.panX)
                self.xmaxlim = np.exp(np.log(self.xmaxlim) - diffx)
                self.xminlim = np.exp(np.log(self.xminlim) - diffx)
            else:
                diffx = x - self.panX
                self.xmaxlim = self.xmaxlim - diffx
                self.xminlim = self.xminlim - diffx
            if self.logy:
                diffy = np.log(y) - np.log(self.panY)
                self.ymaxlim = np.exp(np.log(self.ymaxlim) - diffy)
                self.yminlim = np.exp(np.log(self.yminlim) - diffy)
            else:
                diffy = y - self.panY
                self.ymaxlim = self.ymaxlim - diffy
                self.yminlim = self.yminlim - diffy
            if self.spec() > 0 and self.INVERT_X:
                self.ax.set_xlim(self.xmaxlim, self.xminlim)
            else:
                self.ax.set_xlim(self.xminlim, self.xmaxlim)
            self.ax.set_ylim(self.yminlim, self.ymaxlim)
            if self.INVERT_Y:
                if self.spec(-2) > 0:
                    self.ax.set_ylim(self.ymaxlim, self.yminlim)
            self.canvas.draw_idle()
        elif self.peakPick:
            if self.rect[0] is not None:
                try:
                    self.rect[0].remove()
                except Exception:
                    pass
                self.rect[0] = None
            if self.rect[1] is not None:
                try:
                    self.rect[1].remove()
                except Exception:
                    pass
                self.rect[1] = None
            if event.xdata is not None:
                self.rect[0] = self.ax.axvline(event.xdata, c='k', linestyle='--')
            if self.peakPick in [2, 3]:
                if event.ydata is not None:
                    self.rect[1] = self.ax.axhline(event.ydata, c='k', linestyle='--')
                if self.peakPick == 3:
                    xdata = self.xax() * self.getAxMult(self.spec(), self.getAxType(), self.getppm(), self.freq(), self.ref())
                    ydata = self.xax(-2) * self.getAxMult(self.spec(-2), self.getAxType(-2), self.getppm(-2), self.freq(-2), self.ref(-2))
                    if event.xdata is None or event.ydata is None:
                        return
                    idx = np.argmin(np.abs(xdata - event.xdata))
                    idy = np.argmin(np.abs(ydata - event.ydata))
                    if self.peakPickFunc is not None:
                        tmpdata = np.real(self.getDataType(self.data1D.getHyperData(0)[idy, idx]))
                        self.peakPickFunc((idx, xdata[idx], tmpdata, idy, ydata[idy]))
            self.canvas.draw_idle()
        elif self.leftMouse and (self.zoomX1 is not None) and (self.zoomY1 is not None):
            if self.logx or self.logy:
                self.zoomX2 = event.xdata
                self.zoomY2 = event.ydata
                if self.zoomX2 is None or self.zoomY2 is None:
                    return
            else:
                inv = self.ax.transData.inverted()
                point = inv.transform((event.x, event.y))
                self.zoomX2 = point[0]
                self.zoomY2 = point[1]
            if self.rect[0] is not None:
                try:
                    if self.rect[0] is not None:
                        self.rect[0].remove()
                    if self.rect[1] is not None:
                        self.rect[1].remove()
                    if self.rect[2] is not None:
                        self.rect[2].remove()
                    if self.rect[3] is not None:
                        self.rect[3].remove()
                finally:
                    self.rect = [None, None, None, None]
            self.rect[0], = self.ax.plot([self.zoomX1, self.zoomX2], [self.zoomY2, self.zoomY2], 'k', clip_on=False)
            self.rect[1], = self.ax.plot([self.zoomX1, self.zoomX2], [self.zoomY1, self.zoomY1], 'k', clip_on=False)
            self.rect[2], = self.ax.plot([self.zoomX1, self.zoomX1], [self.zoomY1, self.zoomY2], 'k', clip_on=False)
            self.rect[3], = self.ax.plot([self.zoomX2, self.zoomX2], [self.zoomY1, self.zoomY2], 'k', clip_on=False)
            self.canvas.draw_idle()

    def getAxMult(self, spec, axType, ppm, freq, ref=None):
        if spec == 1:
            if ppm:
                if ref is not None:
                    axMult = 1e6 / ref
                else:
                    axMult = 1e6 / freq
            else:
                axMult = 1.0 / (1000.0**axType)
        elif spec == 0:
            axMult = 1000.0**axType
        return axMult

    def getLabel(self, spec, axis, axType, ppm):
        if not axType in range(3):
            return 'User defined D' + str(axis+1)
        if spec:
            tmpString = "Frequency D" + str(axis+1) + ' '
            if ppm:
                return tmpString + '[ppm]'
            else:
                return tmpString + FREQLABELLIST[axType]
        else:
            
            return "Time D" + str(axis+1) + ' ' + TIMELABELLIST[axType]

    def setLog(self, logx, logy):
        self.logx = logx
        self.logy = logy
        self.ax.set_xlim(self.xminlim, self.xmaxlim)
        self.ax.set_ylim(self.yminlim, self.ymaxlim)
