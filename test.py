import pickle
import sys
import socket
import numpy as np

from cv2 import cv2
from mss import mss
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout
from PyQt5.QtGui import QPixmap


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, sock):
        super().__init__()
        self._run_flag = True
        self.sock = sock

    def run(self):
        while self._run_flag:
            conn, addr = self.sock.accept()
            data = b''
            while True:
                buffer_data = conn.recv(100000)
                if not buffer_data:
                    break
                data += buffer_data
            data = pickle.loads(data)
            self.change_pixmap_signal.emit(data)

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()


class App(QWidget):
    def __init__(self, sock):
        super().__init__()
        self.sock = sock

        self.setWindowTitle("Qt live label demo")
        self.disply_width = 1000
        self.display_height = 1000
        # create the label that holds the image
        self.image_label = QLabel(self)
        self.image_label.resize(self.disply_width, self.display_height)
        # create a text label
        self.textLabel = QLabel('Webcam')

        # create a vertical box layout and add the two labels
        vbox = QVBoxLayout()
        vbox.addWidget(self.image_label)
        vbox.addWidget(self.textLabel)
        # set the vbox layout as the widgets layout
        self.setLayout(vbox)

        # create the video capture thread
        self.thread = VideoThread(self.sock)
        # connect its signal to the update_image slot
        self.thread.change_pixmap_signal.connect(self.update_image)
        # start the thread
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.disply_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)


def initSocket():
    sock = socket.socket()
    sock.bind(('', 9090))
    sock.listen(1)
    return sock


def main():
    sock = initSocket()

    app = QApplication(sys.argv)
    a = App(sock)
    a.show()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
