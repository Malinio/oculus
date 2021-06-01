import sys
import time
import pickle
import datetime

import screeninfo
import socket
import numpy as np

from cv2 import cv2
from mss import mss
from zlib import decompress
from PIL import Image
from PIL.ImageQt import ImageQt

from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap


def recvall(conn, length):
    buf = b''
    while len(buf) < length:
        data = conn.recv(min(4096, length - len(buf)))
        if not data:
            return data
        buf += data
    return buf


def initSocket():
    sock = socket.socket()
    sock.bind(('', 9090))
    sock.listen()
    return sock


def check_time(description):
    def decorator(func):
        def wrapper(*args, **kwargs):
            start = time.time()
            return_value = func(*args, **kwargs)
            end = time.time()

            print(f'{func.__name__} completed - {end - start}s')

            return return_value
        return wrapper
    return decorator


class ScreenSharingThread(QThread):
    change_pixmap_signal = pyqtSignal(bytes)

    def __init__(self):
        super().__init__()
        self._run_flag = True

    def run(self):
        sock = initSocket()
        conn, addr = sock.accept()

        # second_start = time.time()
        # second_frames = 0

        @check_time('receive_pixels')
        def receive_pixels():
            size_len = int.from_bytes(conn.recv(1), byteorder='big')
            size = int.from_bytes(conn.recv(size_len), byteorder='big')
            compressed_pixels = recvall(conn, size)
            return compressed_pixels

        @check_time('decompress_pixels')
        def decompress_pixels(compressed_pixels):
            return decompress(compressed_pixels)

        @check_time('change_pixmap')
        def change_pixmap():
            self.change_pixmap_signal.emit(pixels)

        try:
            while self._run_flag:
                pixels = receive_pixels()
                pixels = decompress_pixels(pixels)
                change_pixmap()

                # second_frames += 1
                # check_time = time.time()
                # if check_time - second_start >= 1:
                #     print(f'FPS={second_frames}')
                #     second_frames = 0
                #     second_start = time.time()
        finally:
            sock.close()

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt live label demo")
        self.resize(1200, 800)

        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(1000, 700)
        # self.image_label.setMinimumSize(1, 1)

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # create the video capture thread
        self.thread = ScreenSharingThread()
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(bytes)
    def update_image(self, pixels):
        """Updates the image_label with a new opencv image"""
        qpixmap = self.convert_pixels_to_qpixmap(pixels)
        self.image_label.setPixmap(qpixmap)

    def convert_pixels_to_qpixmap(self, pixels):
        # img = Image.frombytes('RGB', (1200, 720), pixels, 'raw', 'BGRX').tobytes()
        img = Image.frombytes('RGB', (1200, 720), pixels, 'raw', 'BGRX').tobytes()
        img = QtGui.QImage(img, 1200, 720, QtGui.QImage.Format_RGB888)
        img = img.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        # qt_img = QtGui.QImage(img.to, 1920, 1080, QtGui.QImage.Format_RGB)
        # p = convert_to_Qt_format.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        # return QPixmap.fromImage(qt_img)
        return QPixmap.fromImage(img)


def main():
    app = QApplication(sys.argv)
    a = App()
    a.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
