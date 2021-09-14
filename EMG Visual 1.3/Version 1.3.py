# Version 1.3 (Update : Add Filter)
import serial
import sys
import time
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from pyqtgraph.Qt import QtGui
import pyqtgraph as pg
from scipy.signal import butter, filtfilt


def butter_lowpass(cutoff, fs, order=5):
    nyq = 0.5 * fs
    normal_cutoff = cutoff / nyq
    b, a = butter(order, normal_cutoff, btype='low', analog=False)
    return b, a


def butter_lowpass_filter(data, cutoff, fs, order=5):
    b, a = butter_lowpass(cutoff, fs, order=order)
    y = filtfilt(b, a, data)
    return y


ser = serial.Serial(port='COM6', baudrate=19200, bytesize=8, timeout=1)

# gain sensor
SENSORGAIN = 89.553

rwdt, dte, tme = [], [], []

app = QtGui.QApplication(sys.argv)

win = pg.GraphicsWindow(title="EMG Signal from Arduino")
p1 = win.addPlot(title="EMG Realtime Signal")
curve1 = p1.plot(pen=(0, 255, 0))
p1.setLabel('bottom', 'Sequence of Data', units='')
p1.setLabel('left', 'Voltage', units='mV')

# win.nextRow()

# p2 = win.addPlot(title="Power Spectral")
# curve2 = p2.plot(pen=(0, 255, 0))
# p2.setLabel('bottom', 'Frequency', units='Hz')
# p2.setLabel('left', 'Voltage', units='mV')

windowWidth = 1000
Xm = np.linspace(0, 0, windowWidth)
ptr = -windowWidth


def read_arduino_update(ser):
    # global curve1, curve2, ptr, Xm
    global curve1, ptr, Xm
    Xm[:-1] = Xm[1:]
    ser.flush()
    dec_bytes = ser.readline().decode("ISO−8859−1").strip()
    if sys.getsizeof(dec_bytes) == 53:
        Xm[-1] = round(((float(dec_bytes) * 1000) + 172.4) / SENSORGAIN, 3)
        ptr += 1
        curve1.setData(Xm)
        curve1.setPos(ptr, 0)
        # curve2.setData(Xm)
        # curve2.setPos(ptr, 0)
        QtGui.QApplication.processEvents()

        date = datetime.now().strftime("%d-%b-%Y")
        time1 = datetime.now().strftime("%H:%M:%S")

        rwdt.append(float(dec_bytes))
        dte.append(date)
        tme.append(time1)


def sampling_rate():
    count_data = len(rwdt)
    print('\n' + str(count_data) + ' samples received.')
    T = int(end - start)
    print(str(T) + ' seconds.')
    sps = count_data / int(end - start)
    print(str(sps) + ' samples per second.')
    return T, sps


def save_to_csv():
    filename = input("Filename : ") + ".csv"

    filtered = y.tolist()

    rowlist = list(zip(dte, tme, rwdt, filtered))

    df = pd.DataFrame(rowlist, columns=['Date', 'Time',
                                        'EMG Value (Voltage)',
                                        'Filtered EMG (Voltage)'])

    df.set_index('Time', inplace=True)
    df.to_csv(filename)


try:
    print("Logging Start.")
    start = time.time()

    while len(rwdt) < 5000:
        read_arduino_update(ser)

    end = time.time()
    T, sps = sampling_rate()

except ValueError:
    T, sps = sampling_rate()
    raise

finally:
    ser.close()

    order = 5
    fs = sps  # sample rate, Hz
    cutoff = 2  # desired cutoff frequency of the filter, Hz
    T = T  # seconds
    n = int(T * fs)  # total number of samples
    t = np.linspace(0, T, n, endpoint=False)

    data = np.array(rwdt)
    y = butter_lowpass_filter(data, cutoff, fs, order)
    save_to_csv()

    plt.subplot(2, 1, 1)
    plt.plot(t, data, 'b-', linewidth=1, label='unfiltered signal')
    plt.plot(t, y, 'g-', linewidth=1.3, label='filtered signal')
    plt.suptitle("EMG Signal")
    plt.title("Unfiltered")
    plt.xlabel('Time [sec]')
    plt.ylabel('Voltage [mV]')
    plt.grid()
    plt.legend()
    plt.subplot(2, 1, 2)
    plt.plot(t, y, 'g-', linewidth=1.3, label='filtered signal')
    plt.title("Low Pass Filtered (Cutoff " + str(cutoff) + " Hz)")
    plt.xlabel('Time [sec]')
    plt.ylabel('Voltage [mV]')
    plt.grid(True)
    plt.legend()
    plt.subplots_adjust(hspace=0.35)
    plt.show()
    # sys.exit(pg.QtGui.QApplication.exec_())
