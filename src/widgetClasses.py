#!/usr/bin/env python

# Copyright 2016 - 2019 Bas van Meerten and Wouter Franssen

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

from safeEval import safeEval
import os
from ssNake import QtGui, QtCore, QtWidgets, QT

class SsnakeTabs(QtWidgets.QTabWidget):
    # A tab widget were tabs can be closed with the middle mouse button

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.tabBar().tabAt(event.pos())
            if index >= 0:
                self.tabCloseRequested.emit(index)

class SsnakeTreeWidget(QtWidgets.QTreeView):
    def __init__(self, parent, startDir=None):
        super(SsnakeTreeWidget, self).__init__(parent)
        self.father = parent
        self.dirmodel = QtWidgets.QFileSystemModel()
        self.dirmodel.setRootPath('')
        # Don't show files, just folders
        self.dirmodel.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs| QtCore.QDir.Files| QtCore.QDir.Drives)
        self.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.openMenu)
        self.setModel(self.dirmodel)
        self.setRootIndex(self.dirmodel.index(''))
        if QT == 4:
            self.header().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
        elif QT == 5:
            self.header().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)
        self.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        #self.setToolTip(index.model()->data(index,Qt:isplayRole).toString());
        # Don't show columns for size, file type, and last modified
        self.setHeaderHidden(True)
        self.hideColumn(1)
        self.hideColumn(2)
        self.hideColumn(3)
        self.expand_all(self.dirmodel.index(self.father.lastLocation))

    def mouseDoubleClickEvent(self,event):
        index = self.indexAt(event.pos())
        path = self.dirmodel.filePath(index) 
        if event.button() == QtCore.Qt.MidButton:
            self.loadAct([path])
        elif event.button() == QtCore.Qt.LeftButton and not self.dirmodel.isDir(index):
            self.loadAct([path])
        super(SsnakeTreeWidget, self).mouseDoubleClickEvent(event)

    def mousePressEvent(self,event):
        if event.button() == QtCore.Qt.MidButton:
            index = self.indexAt(event.pos())
            path = self.dirmodel.filePath(index) 
            self.loadAct([path])
        else: #If not, let the QTreeView handle the event
            super(SsnakeTreeWidget, self).mousePressEvent(event)

    def expand_all(self, index):
        path = self.dirmodel.filePath(index) 
        run = True
        pathOld = '-1'
        while pathOld != path:
            self.setExpanded(self.dirmodel.index(path), True)
            pathOld = path
            path = os.path.dirname(path)

    def openMenu(self, position):
        index = self.selectedIndexes()
        path = [self.dirmodel.filePath(x) for x in index]
        menu = QtWidgets.QMenu()
        if len(path) == 1:
            if self.dirmodel.isDir(index[0]):
                menu.addAction("Load Directory", lambda: self.loadAct(path))
            else:
                menu.addAction("Load File", lambda: self.loadAct(path))
        else:
            menu.addAction("Load Selection", lambda: self.loadAct(path))
        menu.exec_(self.viewport().mapToGlobal(position))

    def loadAct(self,path):
        self.father.loadData(path)
        
class SsnakeSlider(QtWidgets.QSlider):
    def wheelEvent(self, event):
        if QT == 4:
            delta = event.delta()
        else:
            delta = event.angleDelta().y()
        step = self.singleStep() * 3
        if QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier and QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            step *= 1000
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier:
            step *= 10
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            step *= 100
        if delta > 0:
            self.setValue(self.value() + step)
        else:
            self.setValue(self.value() - step)
        

class SplitterEventFilter(QtCore.QObject):

    def __init__(self, root, *args):
        super(SplitterEventFilter, self).__init__(*args)
        self.root = root
        self.sizeBak = 0

    def eventFilter(self, receiver, event):
        Select = False
        if event.type() == QtCore.QEvent.MouseButtonDblClick:
            Select = True
        #If single click with middle mouse button
        if event.type() == QtCore.QEvent.MouseButtonPress:
            if event.button() == QtCore.Qt.MidButton:
                Select = True
        if Select:
            sizes = self.root.sizes()
            if sizes[0] == 0:
                self.root.setSizes([self.sizeBak, 1])
            else:
                self.sizeBak = sizes[0]
                self.root.setSizes([0, 1])
            return True
        return False

class SsnakeEventFilter(QtCore.QObject):

    def __init__(self, root, *args):
        super(SsnakeEventFilter, self).__init__(*args)
        self.root = root

    def eventFilter(self, receiver, event):
        if event.type() == QtCore.QEvent.KeyPress:
            if event.key() == QtCore.Qt.Key_Z:
                if (event.modifiers() & QtCore.Qt.ControlModifier) and (event.modifiers() & QtCore.Qt.ShiftModifier):
                    self.root.redo()
                    return True
                elif event.modifiers() == (QtCore.Qt.ControlModifier):
                    self.root.undo()
                    return True
        return False


class ToolWindows(QtWidgets.QWidget):

    NAME = ""
    PICK = False
    SINGLESLICE = False
    BROWSE = False
    RESIZABLE = False
    MENUDISABLE = True
    APPLYANDCLOSE = True
    CANCELNAME = "&Cancel"
    OKNAME = "&Ok"

    def __init__(self, parent):
        super(ToolWindows, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.Tool)
        self.father = parent
        self.setWindowTitle(self.NAME)
        self.layout = QtWidgets.QGridLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.box = QtWidgets.QDialogButtonBox()
        if self.BROWSE:
            self.layout.addLayout(self.grid, 0, 0, 1, 3)
        else:
            self.layout.addLayout(self.grid, 0, 0, 1, 2)
        if self.SINGLESLICE:
            self.singleSlice = QtWidgets.QCheckBox("Single slice")
            self.layout.addWidget(self.singleSlice, 1, 0, 1, 2)
        if self.BROWSE:
            self.browseButton = QtWidgets.QPushButton("&Browse")
            self.browseButton.clicked.connect(self.browse)
            self.box.addButton(self.browseButton, QtWidgets.QDialogButtonBox.ActionRole)
        self.cancelButton = QtWidgets.QPushButton(self.CANCELNAME)
        self.cancelButton.clicked.connect(self.closeEvent)
        self.okButton = QtWidgets.QPushButton(self.OKNAME)
        self.okButton.clicked.connect(self.applyAndClose)
        self.okButton.setFocus()
        self.box.addButton(self.cancelButton,QtWidgets.QDialogButtonBox.RejectRole)
        self.box.addButton(self.okButton,QtWidgets.QDialogButtonBox.AcceptRole)
        self.show()
        self.layout.addWidget(self.box,3,0)
        if not self.RESIZABLE:
            self.setFixedSize(self.size())
        if self.MENUDISABLE:
            self.father.menuEnable(False)
        self.setGeometry(self.frameSize().width() - self.geometry().width(), self.frameSize().height(), 0, 0)

    def browse(self):
        pass

    def applyFunc(self):
        pass

    def applyAndClose(self):
        self.applyFunc()
        if self.APPLYANDCLOSE:
            self.closeEvent()

    def closeEvent(self, *args):
        self.father.current.upd()
        self.father.current.showFid()
        if self.MENUDISABLE:
            self.father.menuEnable(True)
        self.father.updAllFrames()
        self.deleteLater()


class SliceValidator(QtGui.QValidator):

    def validate(self, string, position):
        string = str(string)
        try:
            int(safeEval(string))
            return (QtGui.QValidator.Acceptable, string, position)
        except Exception:
            return (QtGui.QValidator.Intermediate, string, position)


class SliceSpinBox(QtWidgets.QSpinBox):

    def __init__(self, parent, minimum, maximum, *args, **kwargs):
        self.validator = SliceValidator()
        super(SliceSpinBox, self).__init__(parent, *args, **kwargs)
        self.setMinimum(minimum)
        self.setMaximum(maximum)
        self.setKeyboardTracking(False)

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        inp = int(safeEval(str(text)))
        if inp < 0:
            inp = inp + self.maximum() + 1
        return inp

    def textFromValue(self, value):
        inp = int(value)
        if inp < 0:
            inp = inp + self.maximum() + 1
        return str(inp)

    def stepBy(self,steps):
        if QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier and QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            steps *= 1000
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier:
            steps *= 10
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            steps *= 100
        self.setValue(self.value() + steps)

    def wheelEvent(self, event):
        if QT == 4:
            delta = event.delta()
        else:
            delta = event.angleDelta().y() + event.angleDelta().x()
        step = 1
        if delta > 0:
            self.stepBy(step)
        else:
            self.stepBy(-step)
        event.accept()

class SsnakeDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def stepBy(self,steps):
        if QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier and QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            steps *= 1000
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier:
            steps *= 10
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            steps *= 100
        if QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.AltModifier:
            self.setValue(self.value() + self.singleStep() / steps)
        else:
            self.setValue(self.value() + self.singleStep() * steps)

    def wheelEvent(self, event):
        if QT == 4:
            delta = event.delta()
        else:
            delta = event.angleDelta().y() + event.angleDelta().x()
        step = 1
        if delta > 0:
            self.stepBy(step)
        else:
            self.stepBy(-step)
        event.accept()

class SsnakeSpinBox(QtWidgets.QSpinBox):
    def stepBy(self,steps):
        if QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier and QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            steps *= 1000
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ControlModifier:
            steps *= 10
        elif QtWidgets.qApp.keyboardModifiers() & QtCore.Qt.ShiftModifier:
            steps *= 100
        self.setValue(self.value() + self.singleStep() * steps)

    def wheelEvent(self, event):
        if QT == 4:
            delta = event.delta()
        else:
            delta = event.angleDelta().y() + event.angleDelta().x()
        step = 1
        if delta > 0:
            self.stepBy(step)
        else:
            self.stepBy(-step)
        event.accept()

class QLabel(QtWidgets.QLabel):

    def __init__(self, parent, *args, **kwargs):
        super(QLabel, self).__init__(parent, *args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignCenter)

class QSelectLabel(QtWidgets.QLabel):

    def __init__(self, parent, *args, **kwargs):
        super(QSelectLabel, self).__init__(parent, *args, **kwargs)
        self.setTextInteractionFlags(QtCore.Qt.TextSelectableByMouse)

class QLeftLabel(QtWidgets.QLabel):

    def __init__(self, parent, *args, **kwargs):
        super(QLeftLabel, self).__init__(parent, *args, **kwargs)
        self.setAlignment(QtCore.Qt.AlignLeft)
        self.setAlignment(QtCore.Qt.AlignVCenter)


class QLineEdit(QtWidgets.QLineEdit):

    def __init__(self, text='', func=None, parent=None):
        super(QLineEdit, self).__init__(parent)
        self.setText(str(text))
        self.setAlignment(QtCore.Qt.AlignCenter)
        if func is not None:
            self.returnPressed.connect(func)


class FitQLineEdit(QLineEdit):

    def __init__(self, fitParent, paramName, *args):
        super(FitQLineEdit, self).__init__(*args)
        self.fitParent = fitParent
        self.paramName = paramName

    def contextMenuEvent(self, event):
        menu = self.createStandardContextMenu()
        menu.addAction('Connect Parameter', self.connectParams)
        menu.exec_(event.globalPos())

    def connectParams(self, *args):
        parametertxtlist = self.fitParent.rootwindow.getParamTextList()
        ConnectParamsWindow(self, parametertxtlist, self.paramName, self.fitParent.rootwindow.getTabNames(), self.fitParent.rootwindow.getCurrentTabName(), self.setConnect)

    def setConnect(self, inpTuple):
        self.setText(str(inpTuple))


class ConnectParamsWindow(QtWidgets.QWidget):

    def __init__(self, parent, paramTextList, paramName, spectrumNames, currentSpectrum, returnFunc):
        super(ConnectParamsWindow, self).__init__(parent)
        self.setWindowFlags(QtCore.Qt.Window | QtCore.Qt.Tool)
        self.setWindowTitle("Connect Parameter")
        self.paramTextList = paramTextList
        self.paramText = paramName
        self.spectrumNames = spectrumNames
        self.currentSpectrum = self.spectrumNames.index(currentSpectrum)
        self.returnFunc = returnFunc
        self.layout = QtWidgets.QGridLayout(self)
        self.grid = QtWidgets.QGridLayout()
        self.layout.addLayout(self.grid, 0, 0, 1, 2)
        self.grid.addWidget(QtWidgets.QLabel("Parameter:"), 0, 0)
        self.paramNameEntry = QtWidgets.QComboBox()
        self.paramNameEntry.addItems(self.paramTextList)
        self.paramNameEntry.setCurrentIndex(self.paramTextList.index(self.paramText))
        self.grid.addWidget(self.paramNameEntry, 0, 1)
        self.grid.addWidget(QtWidgets.QLabel("Data:"), 1, 0)
        self.spectrumNameEntry = QtWidgets.QComboBox()
        self.spectrumNameEntry.addItems(self.spectrumNames)
        self.spectrumNameEntry.setCurrentIndex(self.currentSpectrum)
        self.grid.addWidget(self.spectrumNameEntry, 1, 1)
        self.grid.addWidget(QtWidgets.QLabel("Line:"), 2, 0)
        self.lineEntry = QtWidgets.QSpinBox()
        self.grid.addWidget(self.lineEntry, 2, 1)
        self.grid.addWidget(QtWidgets.QLabel("Multiplier:"), 3, 0)
        self.multEntry = QLineEdit("1.0")
        self.grid.addWidget(self.multEntry, 3, 1)
        self.grid.addWidget(QtWidgets.QLabel("Offset:"), 4, 0)
        self.addEntry = QLineEdit("0.0")
        self.grid.addWidget(self.addEntry, 4, 1)
        self.cancelButton = QtWidgets.QPushButton("&Cancel")
        self.cancelButton.clicked.connect(self.closeEvent)
        self.okButton = QtWidgets.QPushButton("&Ok")
        self.okButton.clicked.connect(self.applyAndClose)
        self.okButton.setFocus()
        self.box = QtWidgets.QDialogButtonBox()
        self.box.addButton(self.cancelButton,QtWidgets.QDialogButtonBox.RejectRole)
        self.box.addButton(self.okButton,QtWidgets.QDialogButtonBox.AcceptRole)
        self.layout.addWidget(self.box, 2, 0)
        self.show()

    def applyAndClose(self):
        paramName = self.paramTextList[self.paramNameEntry.currentIndex()]
        returnTuple = (paramName, self.lineEntry.value(), safeEval(self.multEntry.text()), safeEval(self.addEntry.text()), self.spectrumNameEntry.currentIndex())
        self.closeEvent()
        self.returnFunc(returnTuple)

    def closeEvent(self, *args):
        self.deleteLater()


class specialProgressBar(QtWidgets.QProgressBar):

    def __init__(self):
        super(specialProgressBar, self).__init__()
        self.setAlignment(QtCore.Qt.AlignCenter)
        self._text = 'Inactive'

    def setText(self, text):
        self._text = text

    def text(self):
        return self._text
