import sys
import time
import struct

import socket
import numpy as np
import logging

from cv2 import cv2
from threading import Thread

from PyQt5.QtCore import Qt
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap


logFormatter = logging.Formatter(
    '%(asctime)s.%(msecs)d %(message)s',
    datefmt='%Y-%m-%dT%H:%M:%S',
)
LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

fileHandler = logging.FileHandler('logs/screen_share_oculus.log', mode='w')
fileHandler.setFormatter(logFormatter)
LOGGER.addHandler(fileHandler)

consoleHandler = logging.StreamHandler()
consoleHandler.setFormatter(logFormatter)
# LOGGER.addHandler(consoleHandler)


def init_socket(host, port):
    sock = socket.socket()
    sock.bind((host, port))
    sock.listen()
    return sock


def check_time(func):
    def wrapper(*args, **kwargs):
        start = time.time()
        return_value = func(*args, **kwargs)
        end = time.time()

        # LOGGER.info(f'oculus:{func.__name__}:{(end - start) * 100:.2f}ms:{FRAME_NUM}')

        return return_value
    return wrapper


@check_time
def receive_frame(conn):
    payload_size = struct.calcsize('>Q')
    frame_size_bytes = b''
    while len(frame_size_bytes) < payload_size:
        frame_size_bytes += conn.recv(payload_size)

    frame_size = struct.unpack('>Q', frame_size_bytes)[0]
    frame_bytes = b''
    while len(frame_bytes) < frame_size:
        frame_bytes += conn.recv(frame_size - len(frame_bytes))

    return frame_bytes


@check_time
def convert_frame_bytes_to_arr(frame_bytes):
    frame_raw_arr = np.frombuffer(frame_bytes, np.uint8)
    frame_arr = cv2.imdecode(frame_raw_arr, cv2.IMREAD_COLOR)
    return frame_arr


def show_frame(app, frame_arr):
    app.update_frame(frame_arr)
    # cv2.imshow('Victima', frame_arr)


def screen_receiving(sock, app):
    conn, addr = sock.accept()

    last_time = time.time()
    fps = 0

    while True:
        frame_bytes = receive_frame(conn)
        frame_arr = convert_frame_bytes_to_arr(frame_bytes)
        show_frame(app, frame_arr)

        # if cv2.waitKey(1) & 0xFF == ord('q'):
        #     sock.close()
        #     break

        fps += 1
        if time.time() - last_time >= 1:
            print(f'FPS={fps}')
            last_time = time.time()
            fps = 0


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Qt live label demo")
        self.resize(1200, 800)

        self.image_label = QLabel(self)
        self.image_label.resize(1000, 700)

        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        self.setLayout(vbox)

    def update_frame(self, frame_arr):
        pixmap = self.convert_pixels_to_pixmap(frame_arr)
        self.image_label.setPixmap(pixmap)

    def convert_pixels_to_pixmap(self, frame_arr):
        img = QtGui.QImage(frame_arr, 1200, 720, QtGui.QImage.Format_RGB888)
        img = img.scaled(self.image_label.width(), self.image_label.height(), Qt.KeepAspectRatio)
        return QPixmap.fromImage(img)


def main(host='', port=9090):
    app_top = QApplication(sys.argv)
    app = App()

    sock = init_socket(host, port)
    screen_receiving_thread = Thread(target=screen_receiving, args=(sock, app))
    screen_receiving_thread.start()

    app.show()
    sys.exit(app_top.exec_())


if __name__ == '__main__':
    main()
