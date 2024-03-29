# by rpturbina, EMG Measurement System Project
# -*- coding: utf-8 -*-

from array import array
from PyQt5 import QtCore, QtGui, QtWidgets
from pyqtgraph import GraphicsLayoutWidget
import pyfirmata
import numpy as np
import pandas as pd
import time
import math
import pyqtgraph as pg
from scipy.signal import butter, filtfilt
import matplotlib.pyplot as plt
import os
import serial.tools.list_ports


def rmsValue(arr, n):
    square = 0
    mean = 0.0
    root = 0.0
    # Calculate square
    for i in range(0, n):
        square += (arr[i]**2)
    # Calculate Mean
    mean = (square / (float)(n))
    # Calculate Root
    root = math.sqrt(mean)
    return root

# Combo Box Pop Up


class ComboBox(QtWidgets.QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        super(ComboBox, self).showPopup()


class Ui_MainWindow(QtWidgets.QWidget):

    rwdt, dte, tme = [], [], []  # temporary place for emg & datetime data
    SENSORGAIN = 89.553  # sensorgain value
    windowWidth = 2000  # width of plot graph
    cutoff = 2  # desired cutoff frequency of the filter, Hz
    rmsVariable = 0  # initial rms value
    Xm = np.linspace(0, 0, windowWidth)
    Ym = np.linspace(0, 0, windowWidth)
    ptr = -windowWidth

    def setupUi(self, MainWindow):
        # UI Design
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1000, 900)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(
            "C:/Users/RPTURBINA/Downloads/electromyography.png"),
            QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)  # add icon for window bar
        MainWindow.setIconSize(QtCore.QSize(30, 30))
        # MainWindow.setStyleSheet("background-color: rgb(52, 52, 52);\n""")
        self.centralwidget = QtWidgets.QWidget(MainWindow)

        # Set vertical layout
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)

        self.graphicsView = GraphicsLayoutWidget(self.centralwidget)
        self.p1 = self.graphicsView.addPlot(title="EMG Realtime Signal")
        self.p1.setLabel('bottom', 'Time', units='second')
        self.p1.setLabel('left', 'Voltage', units='volt')
        self.p1.showGrid(x=True, y=True, alpha=0.5)
        self.curve1 = self.p1.plot(pen=(0, 255, 0))
        pg.setConfigOptions(antialias=True)
        self.verticalLayout.addWidget(self.graphicsView)

        self.gridLayout_1 = QtWidgets.QGridLayout()
        self.labelDataSample = QtWidgets.QLabel(self.centralwidget)
        self.labelDataSample.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout_1.addWidget(self.labelDataSample, 0, 2, 1, 1)
        self.labelStatus = QtWidgets.QLabel(self.centralwidget)
        self.labelStatus.setAlignment(QtCore.Qt.AlignLeft)
        self.gridLayout_1.addWidget(self.labelStatus, 0, 0, 1, 1)
        self.labelElapsedtime = QtWidgets.QLabel(self.centralwidget)
        self.labelElapsedtime.setAlignment(QtCore.Qt.AlignCenter)
        self.gridLayout_1.addWidget(self.labelElapsedtime, 0, 1, 1, 1)
        self.labelRMSValue = QtWidgets.QLabel(self.centralwidget)
        self.labelRMSValue.setAlignment(QtCore.Qt.AlignRight)
        self.gridLayout_1.addWidget(self.labelRMSValue, 0, 3, 1, 1)
        self.line_1 = QtWidgets.QFrame(self.centralwidget)
        self.line_1.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_1.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_1.addWidget(self.line_1, 1, 0, 1, 4)
        self.verticalLayout.addLayout(self.gridLayout_1)

        font = QtGui.QFont()
        font.setFamily("NewsGoth BT")
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)

        self.gridLayout_2 = QtWidgets.QGridLayout()
        self.startButton = QtWidgets.QPushButton(self.centralwidget)
        self.startButton.setFont(font)
        # self.startButton.setStyleSheet("\n""color: rgb(255, 255, 255);")
        self.startButton.setStyleSheet(
            "QPushButton::hover:!pressed\n"
            "{background-color : rgb(0, 255, 0);}\n"
            "QPushButton::pressed\n"
            "{background-color :rgb(0, 229, 0);\n"
            "color:black;}\n"
            "")
        self.gridLayout_2.addWidget(self.startButton, 0, 0, 1, 1)
        self.stopButton = QtWidgets.QPushButton(self.centralwidget)
        self.stopButton.setFont(font)
        self.stopButton.setStyleSheet(
            "QPushButton::hover:!pressed\n"
            "{background-color : red;\n"
            "color:white;}\n"
            "QPushButton::pressed\n"
            "{background-color :rgb(229, 0, 0);\n"
            "color:white;}\n"
            "")
        self.stopButton.setEnabled(False)
        self.gridLayout_2.addWidget(self.stopButton, 0, 1, 1, 1)
        self.clearButton = QtWidgets.QPushButton(self.centralwidget)
        self.clearButton.setFont(font)
        self.clearButton.setStyleSheet(
            "QPushButton::hover:!pressed\n"
            "{background-color : yellow;\n"
            "color:black;}\n"
            "QPushButton::pressed\n"
            "{background-color :rgb(229, 229, 0);\n"
            "color:black;}\n"
            "")
        self.clearButton.setEnabled(False)
        self.gridLayout_2.addWidget(self.clearButton, 0, 2, 1, 1)

        self.labelPort = QtWidgets.QLabel(self.centralwidget)
        self.labelPort.setAlignment(
            QtCore.Qt.AlignRight |
            QtCore.Qt.AlignTrailing |
            QtCore.Qt.AlignVCenter)
        self.gridLayout_2.addWidget(self.labelPort, 0, 3, 1, 1)

        self.comboBoxPort = ComboBox(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.comboBoxPort.setSizePolicy(sizePolicy)
        self.comboBoxPort.setMaximumSize(QtCore.QSize(120, 28))
        self.comboBoxPort.setStyleSheet(
            "QComboBox {\n"
            "background-color:white;\n"
            "}\n"
            "\n"
            "QComboBox:hover{\n"
            "border : 1px solid rgb(27, 102, 242);\n"
            "}\n"
            "\n"
            "QComboBox QAbstractItemView\n"
            "{\n"
            "selection-background-color: rgb(27, 102, 242);}\n"
            "border-radius: 0px;\n")

        self.gridLayout_2.addWidget(self.comboBoxPort, 0, 4, 1, 1)
        ports = [p.device for p in serial.tools.list_ports.comports()
                 if 'Arduino' in p.description]
        self.comboBoxPort.clear()
        self.comboBoxPort.addItems(ports)

        self.line_2 = QtWidgets.QFrame(self.centralwidget)
        self.line_2.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_2.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_2.addWidget(self.line_2, 1, 0, 1, 5)
        self.verticalLayout.addLayout(self.gridLayout_2)

        self.gridLayout_3 = QtWidgets.QGridLayout()
        self.singlePlotButton = QtWidgets.QPushButton(self.centralwidget)
        self.singlePlotButton.setEnabled(False)
        self.gridLayout_3.addWidget(self.singlePlotButton, 1, 2, 1, 1)
        self.savePlotButton = QtWidgets.QPushButton(self.centralwidget)
        self.savePlotButton.setEnabled(False)
        self.gridLayout_3.addWidget(self.savePlotButton, 1, 1, 1, 1)
        self.fileName = QtWidgets.QLineEdit(self.centralwidget)
        self.fileName.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.fileName.sizePolicy().hasHeightForWidth())
        self.fileName.setSizePolicy(sizePolicy)
        self.gridLayout_3.addWidget(self.fileName, 1, 0, 1, 1)
        self.line_3 = QtWidgets.QFrame(self.centralwidget)
        self.line_3.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_3.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_3.addWidget(self.line_3, 2, 0, 1, 3)
        self.labelSavePlot = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout_3.addWidget(self.labelSavePlot, 0, 0, 1, 3)
        self.verticalLayout.addLayout(self.gridLayout_3)

        self.gridLayout_4 = QtWidgets.QGridLayout()
        self.fileSelect_1 = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.fileSelect_1.sizePolicy().hasHeightForWidth())
        self.fileSelect_1.setSizePolicy(sizePolicy)
        self.gridLayout_4.addWidget(self.fileSelect_1, 1, 0, 1, 1)
        self.selectButton_1 = QtWidgets.QPushButton(self.centralwidget)
        self.gridLayout_4.addWidget(self.selectButton_1, 1, 1, 1, 1)
        self.fileSelect_2 = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.fileSelect_2.sizePolicy().hasHeightForWidth())
        self.fileSelect_2.setSizePolicy(sizePolicy)
        self.gridLayout_4.addWidget(self.fileSelect_2, 2, 0, 1, 1)
        self.selectButton_2 = QtWidgets.QPushButton(self.centralwidget)
        self.gridLayout_4.addWidget(self.selectButton_2, 2, 1, 1, 1)
        self.fileSelect_3 = QtWidgets.QLineEdit(self.centralwidget)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.fileSelect_3.sizePolicy().hasHeightForWidth())
        self.fileSelect_3.setSizePolicy(sizePolicy)
        self.gridLayout_4.addWidget(self.fileSelect_3, 3, 0, 1, 1)
        self.selectButton_3 = QtWidgets.QPushButton(self.centralwidget)
        self.gridLayout_4.addWidget(self.selectButton_3, 3, 1, 1, 1)
        self.line_4 = QtWidgets.QFrame(self.centralwidget)
        self.line_4.setFrameShape(QtWidgets.QFrame.HLine)
        self.line_4.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.gridLayout_4.addWidget(self.line_4, 4, 0, 1, 3)
        self.multiPlotButton = QtWidgets.QPushButton(self.centralwidget)
        self.multiPlotButton.setEnabled(False)
        sizePolicy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Minimum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(
            self.multiPlotButton.sizePolicy().hasHeightForWidth())
        self.multiPlotButton.setSizePolicy(sizePolicy)
        self.gridLayout_4.addWidget(self.multiPlotButton, 1, 2, 3, 1)
        self.labelMulti = QtWidgets.QLabel(self.centralwidget)
        self.gridLayout_4.addWidget(self.labelMulti, 0, 0, 1, 3)
        self.verticalLayout.addLayout(self.gridLayout_4)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusBar = QtWidgets.QStatusBar(MainWindow)
        MainWindow.setStatusBar(self.statusBar)

        self.fileName.setText("".join([time.strftime(
                                       "%Y-%m-%d-%H.%M.%S"), "-"]))
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    # UI Design
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(
            _translate("MainWindow",
                       "EMG Real-Time Signal Visualization"))
        self.labelDataSample.setStatusTip(
            _translate("MainWindow",
                       "Number of data samples received"))
        self.labelDataSample.setText(
            _translate("MainWindow",
                       "Data Samples : - samples received"))
        self.labelStatus.setText(_translate(
            "MainWindow", "Status : Waiting for Arduino devices to reset..."))
        self.labelElapsedtime.setText(_translate(
            "MainWindow", "Elapsed time : - second"))
        self.labelRMSValue.setText(_translate(
            "MainWindow", "RMS Value : - volt"))
        self.startButton.setStatusTip(
            _translate("MainWindow",
                       "Display real-time electromyography signal (Spacebar)"))
        self.startButton.setText(_translate("MainWindow", "RECORD"))
        self.startButton.setShortcut(_translate("MainWindow", "Space"))
        self.stopButton.setStatusTip(
            _translate("MainWindow",
                       "Stop real-time electromyography signal update (S)"))
        self.stopButton.setText(_translate("MainWindow", "STOP"))
        self.stopButton.setShortcut(_translate("MainWindow", "S"))
        self.clearButton.setStatusTip(
            _translate("MainWindow",
                       "Clear the display and the signal samples (C)"))
        self.clearButton.setText(_translate("MainWindow", "CLEAR"))
        self.clearButton.setShortcut(_translate("MainWindow", "C"))
        self.labelPort.setText(_translate("MainWindow", "COM Port :"))
        self.fileName.setStatusTip(
            _translate("MainWindow",
                       "Type filename for save to CSV files"))
        self.fileName.setPlaceholderText(
            _translate("MainWindow",
                       "Type the file name..."))
        self.labelSavePlot.setText(
            _translate(
                "MainWindow",
                "".join(["<html><head/><body><p align=\"center\"",
                         "><span style=\" font-weight:600;\">",
                         "Save Plot to CSV File | ",
                         "Single Plot using Matplotlib",
                         "</span></p></body></html>"])
            ))
        self.savePlotButton.setStatusTip(
            _translate("MainWindow", "Save plot to CSV file (Ctrl+S)"))
        self.savePlotButton.setText(_translate("MainWindow", "Save Plot"))
        self.savePlotButton.setShortcut(_translate("MainWindow", "Ctrl+S"))
        self.savePlotButton.setStatusTip(
            _translate("MainWindow",
                       "Plot signal using matplotlib (Ctrl+P)"))
        self.singlePlotButton.setText(
            _translate("MainWindow", "Single Plot"))
        self.singlePlotButton.setShortcut(_translate("MainWindow", "Ctrl+P"))
        self.labelMulti.setText(
            _translate(
                "MainWindow",
                "".join(["<html><head/><body><p align=\"center\">",
                         "<span style=\" font-weight:600;\">",
                         "Multiple Plot Tool using Matplotlib",
                         "</span></p></body></html>"])
            ))
        self.graphicsView.setStatusTip(
            _translate("MainWindow", "Real-time electromyography signal"))

        self.fileSelect_1.setStatusTip(
            _translate("MainWindow", "Type filename for save to CSV files"))
        self.fileSelect_1.setPlaceholderText(
            _translate("MainWindow", "Select CSV file to plot"))
        self.selectButton_1.setText(
            _translate("MainWindow", "Select File"))
        self.fileSelect_2.setStatusTip(
            _translate("MainWindow", "Type filename for save to CSV files"))
        self.fileSelect_2.setPlaceholderText(
            _translate("MainWindow", "Select CSV file to plot"))
        self.selectButton_2.setText(
            _translate("MainWindow", "Select File"))
        self.fileSelect_3.setStatusTip(
            _translate("MainWindow", "Type filename for save to CSV files"))
        self.fileSelect_3.setPlaceholderText(
            _translate("MainWindow", "Select CSV file to plot"))
        self.selectButton_3.setText(
            _translate("MainWindow", "Select File"))
        self.multiPlotButton.setText(
            _translate("MainWindow",
                       "\n".join(["Multiple", "or", "Single Plot"])))

        # Set event and signal (user interaction)
        self.startButton.clicked.connect(self.start_button)
        self.stopButton.clicked.connect(self.stop_button)
        self.savePlotButton.clicked.connect(self.save_plot_button)
        self.clearButton.clicked.connect(self.clear_button)
        self.comboBoxPort.popupAboutToBeShown.connect(self.updatePorts)
        self.singlePlotButton.clicked.connect(self.single_plot_button)
        self.selectButton_1.clicked.connect(self.select_file_button_1)
        self.selectButton_2.clicked.connect(self.select_file_button_2)
        self.selectButton_3.clicked.connect(self.select_file_button_3)
        self.multiPlotButton.clicked.connect(self.multiple_plot_button)

    def arduino_ready(self):
        self.labelStatus.setText("Status : Arduino is ready")

    def no_arduino(self):
        self.labelStatus.setText("Status : No Arduino Found!")

    def updatePorts(self):
        ports = [p.device for p in serial.tools.list_ports.comports()
                 if 'Arduino' in p.description]
        self.comboBoxPort.clear()
        self.comboBoxPort.addItems(ports)

    # read emg input
    def read_arduino_update(self, analog_input, interval):
        analog_value = analog_input.read()
        if type(analog_value) == float:
            voltage_value = analog_value * (5.00 / 1.0)
            # dataLength = len(Ui_MainWindow.rwdt)
            # Ui_MainWindow.Xm[:-dataLength] = Ui_MainWindow.Xm[dataLength:]
            # Ui_MainWindow.Ym[:-dataLength] = Ui_MainWindow.Ym[dataLength:]
            Ui_MainWindow.Xm[:-1] = Ui_MainWindow.Xm[1:]
            Ui_MainWindow.Ym[:-1] = Ui_MainWindow.Ym[1:]
            emg_float = voltage_value
            # emg_float = round(
            #     (voltage_value * 1000
            #      + 172.4) / Ui_MainWindow.SENSORGAIN, 3)
            Ui_MainWindow.Xm[-1] = interval
            Ui_MainWindow.Ym[-1] = emg_float
            # Ui_MainWindow.ptr += 1
            self.curve1.setData(Ui_MainWindow.Xm, Ui_MainWindow.Ym)
            # self.curve1.setPos(Ui_MainWindow.ptr, 0)
            QtWidgets.QApplication.processEvents()
            Ui_MainWindow.rwdt.append(emg_float)
            # Ui_MainWindow.dte.append(time.strftime("%d-%b-%Y"))
            # Ui_MainWindow.tme.append(time.strftime("%H:%M:%S"))

    # measure sampling rate
    def sampling_rate(self):
        count_data = len(Ui_MainWindow.rwdt)
        print(" ".join([str(count_data), 'samples received.']))
        self.T = self.end - self.start
        print(" ".join([str("%.2f" % self.T), 'seconds.']))
        self.sps = count_data / self.T
        print(" ".join([str("%.0f" % self.sps), 'samples per second.']))
        return self.T, self.sps

    # set digital filter
    def butter_lowpass(self, cutoff, fs, order):
        nyq = 0.5 * fs
        normal_cutoff = cutoff / nyq
        b, a = butter(order, normal_cutoff, btype='low', analog=False)
        return b, a

    def butter_lowpass_filter(self, data, cutoff, fs, order):
        b, a = self.butter_lowpass(cutoff, fs, order)
        y = filtfilt(b, a, data)
        return y

    def filter_signal(self):
        order = 3   # desired filter order
        fs = self.sps  # sample rate, Hz
        ui.cutoff = ui.cutoff  # desired cutoff frequency of the filter, Hz
        T = self.T  # seconds
        self.n = len(Ui_MainWindow.rwdt)  # total number of samples
        self.t = np.linspace(0, T, self.n, endpoint=False)
        self.data = np.array(Ui_MainWindow.rwdt)
        y_f = self.butter_lowpass_filter(
            self.data, ui.cutoff, fs, order)
        y_f = np.around(y_f, decimals=3)
        return y_f

    # Set record button
    def start_button(self):
        self.condition = 1
        self.startButton.setEnabled(False)
        self.stopButton.setEnabled(True)
        self.fileSelect_1.setEnabled(False)
        self.fileSelect_2.setEnabled(False)
        self.fileSelect_3.setEnabled(False)
        self.selectButton_1.setEnabled(False)
        self.selectButton_2.setEnabled(False)
        self.selectButton_3.setEnabled(False)
        self.multiPlotButton.setEnabled(False)
        self.p1.setMouseEnabled(x=False, y=False)
        self.p1.enableAutoRange(enable=True)
        self.p1.setLimits(xMin=0, xMax=None, yMin=0, yMax=5)
        self.labelStatus.setText("Status : Updating EMG signal")
        print("\n" + "Logging started.")
        self.start = time.time()
        while self.condition:
            self.now = time.time()
            self.interval = round(self.now - self.start, 2)
            self.read_arduino_update(analog_input, self.interval)
            self.labelDataSample.setText(
                " ".join(["Data Samples :",
                          str(len(Ui_MainWindow.rwdt)),
                          "samples received"])
            )
            Ui_MainWindow.tme.append(self.interval)
            self.labelElapsedtime.setText(
                " ".join(["Elapsed Time :",
                          str("%.2f" % (self.now - self.start)),
                          "seconds"]))

        print("\n" + "Logging stopped.")
        self.end = time.time()
        self.T, self.sps = self.sampling_rate()
        self.y_f = self.filter_signal()
        Ui_MainWindow.rmsVariable = format(self.calculate_root_mean_square(
            Ui_MainWindow.rwdt), '.3f')
        self.labelRMSValue.setText(
            f"RMS Value : {Ui_MainWindow.rmsVariable} volt")
        print(
            f"\nRMS Value : {Ui_MainWindow.rmsVariable} volt")

    # Calculate root mean square

    def calculate_root_mean_square(self, arr: array):
        arr_length = len(arr)
        rms_value = round(rmsValue(arr, arr_length), 3)
        return rms_value

        # Set stop button

    def stop_button(self):
        self.condition = 0
        self.stopButton.setEnabled(False)
        self.clearButton.setEnabled(True)
        self.labelStatus.setText("Status : Signal update stopped")
        self.fileName.setEnabled(True)
        self.savePlotButton.setEnabled(True)
        self.singlePlotButton.setEnabled(True)
        self.fileName.setText(
            "".join([time.strftime("%Y-%m-%d-%H.%M.%S"), "-"]))
        self.fileSelect_1.setEnabled(True)
        self.fileSelect_2.setEnabled(True)
        self.fileSelect_3.setEnabled(True)
        self.selectButton_1.setEnabled(True)
        self.selectButton_2.setEnabled(True)
        self.selectButton_3.setEnabled(True)

    # Set clear button
    def clear_button(self):
        self.condition = 0
        Ui_MainWindow.rwdt.clear()  # clear emg data list
        Ui_MainWindow.dte.clear()   # clear date data list
        Ui_MainWindow.tme.clear()   # clear time data list
        Ui_MainWindow.Xm = np.linspace(0, 0, Ui_MainWindow.windowWidth)
        Ui_MainWindow.Ym = np.linspace(0, 0, Ui_MainWindow.windowWidth)
        self.curve1.setData(Ui_MainWindow.Xm, Ui_MainWindow.Ym)
        self.labelDataSample.setText("Data Samples : - samples received")
        self.labelStatus.setText("Status : Signal plot cleared")
        self.labelElapsedtime.setText("Elapsed time : - second")
        self.labelRMSValue.setText("RMS Value : - volt")
        self.startButton.setEnabled(True)
        self.clearButton.setEnabled(False)
        self.fileName.setEnabled(False)
        self.savePlotButton.setEnabled(False)
        self.singlePlotButton.setEnabled(False)
        print("\n" + "Datalog cleared.")

    # Set Save Plot Button
    def save_plot_button(self):
        dirName = QtWidgets.QFileDialog.getExistingDirectory(
            self,
            'Choose file directory', os.curdir,
            QtWidgets.QFileDialog.ShowDirsOnly)
        # print(dirName)
        if not dirName:
            return
        filtered = self.y_f.tolist()
        rowlist = list(zip(
            # self.dte,
            self.tme,
            self.rwdt,
            filtered))

        df = pd.DataFrame(rowlist,
                          columns=[
                              # 'Date',
                              'Time (second)',
                              'EMG Value (V)', 'Filtered Value (V)'])
        # new_row = {'Time': 'Retrieval Time (sec)',
        #            #    'Date': str("%.2f" % self.T),
        #            'EMG Value (V)': 'Total Samples',
        #            'Filtered Value (V)': self.n}
        # df = df.append(new_row, ignore_index=True)
        df.at[0, 'Retrieval Time (second)'] = str("%.2f" % self.T)
        df.at[0, 'Total Samples'] = self.n
        df.at[0, 'RMS Value'] = Ui_MainWindow.rmsVariable
        df.at[0, 'Datetime'] = time.strftime("%Y-%m-%d-%H.%M.%S")
        df.set_index('Time (second)', inplace=True)
        filename = self.fileName.text() + ".csv"
        df.to_csv("/".join([dirName, filename]))
        self.labelStatus.setText("Status : CSV File Saved")
        print("\n" + "Filename: " + filename)
        print("CSV File saved at " + dirName)

    # Set Single Plot Button

    def single_plot_button(self):
        self.labelStatus.setText("Status : EMG Signal plotted on Matplotlib")
        plt.ion()
        plt.gcf().canvas.manager.set_window_title('Single Plot EMG Signal')
        plt.subplot(2, 1, 1)
        plt.plot(self.t, self.data,
                 'b-', linewidth=1, label='unfiltered signal')
        plt.suptitle("EMG Signal")
        plt.title('Non Filtered Signal')
        plt.xlabel('Time [sec]')
        plt.ylabel('Voltage [V]')
        plt.grid(True, alpha=0.6)
        plt.legend()

        plt.subplot(2, 1, 2)
        plt.plot(self.t, self.y_f, 'g-',
                 linewidth=1, label='filtered signal')
        plt.title('Filtered Signal (Cutoff Frequency ' +
                  str(ui.cutoff) + ' Hz)')
        plt.xlabel('Time [sec]')
        plt.ylabel('Voltage [V]')
        # plt.ylim([0, 5])
        plt.grid(True, alpha=0.6)
        plt.legend()
        plt.subplots_adjust(hspace=0.35)
        print("\nData plotted.")

    # Set Multiple Plot Button

    def multiple_plot_button(self):
        self.labelStatus.setText(
            "Status : Multiple or single signal plotted on Matplotlib"
        )
        plt.ion()
        plt.gcf().canvas.manager.set_window_title('Single/Multiple Plot EMG Signals')
        if self.fileSelect_1.text() != "":
            dirName = self.fileSelect_1.text()
            csvName = dirName.split("/")
            self.read_csv_files(dirName)
            plt.subplot(2, 1, 1)
            plt.plot(self.t_read, self.y_read,
                     'r-', linewidth=1, label=f"Plot data 1: {csvName[-1]}")
            plt.subplot(2, 1, 2)
            plt.plot(self.t_read, self.yf_read, 'r-',
                     linewidth=1, label=f"Plot data 1: {csvName[-1]}")

        if self.fileSelect_2.text() != "":
            dirName = self.fileSelect_2.text()
            csvName = dirName.split("/")
            self.read_csv_files(dirName)
            plt.subplot(2, 1, 1)
            plt.plot(self.t_read, self.y_read,
                     'g-', linewidth=1, label=f"Plot data 2: {csvName[-1]}")
            plt.subplot(2, 1, 2)
            plt.plot(self.t_read, self.yf_read, 'g-',
                     linewidth=1, label=f"Plot data 2: {csvName[-1]}")

        if self.fileSelect_3.text() != "":
            dirName = self.fileSelect_3.text()
            csvName = dirName.split("/")
            self.read_csv_files(dirName)
            plt.subplot(2, 1, 1)
            plt.plot(self.t_read, self.y_read,
                     'b-', linewidth=1, label=f"Plot data 3: {csvName[-1]}")
            plt.subplot(2, 1, 2)
            plt.plot(self.t_read, self.yf_read, 'b-',
                     linewidth=1, label=f"Plot data 3: {csvName[-1]}")

        plt.suptitle("EMG Signal")
        plt.subplot(2, 1, 1)
        plt.title('Non Filtered Signal')
        plt.xlabel('Time [sec]')
        plt.ylabel('Voltage [V]')
        plt.grid(True, alpha=0.6)
        plt.legend()

        plt.subplot(2, 1, 2)
        plt.title('Filtered Signal (Cutoff Freqeuncy ' +
                  str(ui.cutoff) + ' Hz)')
        plt.xlabel('Time [sec]')
        plt.ylabel('Voltage [V]')
        plt.grid(True, alpha=0.6)
        plt.legend()
        plt.subplots_adjust(hspace=0.35)
        print("\nData plotted.")

    # Set Select File BUtton

    def select_file_button_1(self):
        self.labelStatus.setText("Status : Select CSV file to plot")
        fileName = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Choose CSV file', os.curdir,
            'CSV file (*.csv)')
        self.fileSelect_1.setText(fileName[0])
        self.multiPlotButton.setEnabled(True)
        print("\nSelected file: " + fileName[0])

    def select_file_button_2(self):
        self.labelStatus.setText("Status : Select CSV file to plot")
        fileName = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Choose CSV file', os.curdir,
            'CSV file (*.csv)')
        self.fileSelect_2.setText(fileName[0])
        self.multiPlotButton.setEnabled(True)
        print("\nSelected file: " + fileName[0])

    def select_file_button_3(self):
        self.labelStatus.setText("Status : Select CSV file to plot")
        fileName = QtWidgets.QFileDialog.getOpenFileName(
            self,
            'Choose CSV file', os.curdir,
            'CSV file (*.csv)')
        self.fileSelect_3.setText(fileName[0])
        self.multiPlotButton.setEnabled(True)
        print("\nSelected file: " + fileName[0])

    # read saved csv
    def read_csv_files(self, dirName):
        df = pd.read_csv(dirName)
        # read non filter`ed emg value column
        nonfilt_value = df["EMG Value (V)"]
        # nonfilt_value = nonfilt_value.drop(nonfilt_value.tail(1).index)
        nonfilt_value = nonfilt_value.astype(float)
        self.y_read = nonfilt_value.to_numpy()
        # read filtered emg value column
        filtered_value = df["Filtered Value (V)"]
        # filtered_value = filtered_value.drop(filtered_value.tail(1).index)
        self.yf_read = filtered_value.to_numpy()
        # read retrieval time from csv file
        self.retrieval_time = float(df.at[0, 'Retrieval Time (second)'])
        # read total sample from csv file
        self.number_sample = int(df.at[0, 'Total Samples'])
        self.t_read = np.linspace(
            0, self.retrieval_time, self.number_sample, endpoint=False)


if __name__ == "__main__":
    print("Initializing the program...")
    import sys
    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    ports = [p.device for p in serial.tools.list_ports.comports()
             if 'Arduino' in p.description]
    if not ports:
        raise IOError("No Arduino found")
    board = pyfirmata.Arduino(ports[0], baudrate=9600)
    iterator = pyfirmata.util.Iterator(board)
    iterator.start()
    print("Program is ready to use.")
    analog_input = board.get_pin('a:0:i')
    ui.arduino_ready()
    sys.exit(app.exec_())
