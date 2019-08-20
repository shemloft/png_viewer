import sys
import math
from PyQt5 import QtWidgets, QtCore, QtGui
from PyQt5.QtGui import QPainter, QColor, QFont, QBrush
from PyQt5.QtCore import QSize, QSizeF, QPointF, QRectF, QEvent

PICTURE_AREA_SIZE = QSize(800, 600)


def show_window(rgb_map, header):
    app = QtWidgets.QApplication(sys.argv)
    png_win = Window(rgb_map, header)
    png_win.show()
    sys.exit(app.exec_())


class Window(QtWidgets.QWidget):
    def __init__(self, rgb_map, meta):
        super().__init__()
        self.rgb_map = rgb_map
        self.bit_depth = meta.bit_depth
        self.picture_size = QSize(meta.width, meta.height)
        self.rescaled_size = self.picture_size
        self.pixel_size = 1

        self.init_ui()

    def init_ui(self):

        self.increase_button = QtWidgets.QPushButton('Увеличить', self)
        self.reduce_button = QtWidgets.QPushButton('Уменьшить', self)
        self.back_button = QtWidgets.QPushButton('Назад к 100%', self)

        self.increase_button.clicked.connect(self.increase_image)
        self.reduce_button.clicked.connect(self.reduce_image)
        self.back_button.clicked.connect(self.turn_original_image_size)

        self.picture = Picture(self)

        self.hbox = QtWidgets.QHBoxLayout()
        self.hbox.addWidget(self.increase_button)
        self.hbox.addWidget(self.reduce_button)
        self.hbox.addWidget(self.back_button)

        self.vbox = QtWidgets.QVBoxLayout()
        self.vbox.addLayout(self.hbox)
        self.vbox.addWidget(self.picture)

        self.setLayout(self.vbox)

        self.picture.update_picture()

        self.setWindowTitle('PNG viewer')

    def increase_image(self):
        if self.pixel_size >= 4:
            return
        self.pixel_size += 0.25
        self.reduce_button.setEnabled(True)
        if self.pixel_size >= 4:
            self.increase_button.setDisabled(True)
        self.picture.update_picture()

    def reduce_image(self):
        if self.pixel_size <= 0.25:
            return
        self.pixel_size -= 0.25
        self.increase_button.setEnabled(True)
        if self.pixel_size <= 0.25:
            self.reduce_button.setDisabled(True)
        self.picture.update_picture()

    def turn_original_image_size(self):
        self.pixel_size = 1
        self.increase_button.setEnabled(True)
        self.reduce_button.setEnabled(True)
        self.picture.update_picture()


class Picture(QtWidgets.QWidget):
    def __init__(self, window):
        super().__init__()
        self.window = window
        self.rgb_map = self.window.rgb_map
        self.bit_depth = self.window.bit_depth
        self.picture_size = self.window.picture_size
        self.rescaled_size = self.picture_size
        self.pixel_size = self.window.pixel_size
        self.init_ui()

    def init_ui(self):
        self.scrollbar_width = 24

        self.width_central_shift = 0
        self.height_central_shift = 0

        self.scroll_width_shift = 0
        self.scroll_height_shift = 0

        self.widget_size = QSize(
            PICTURE_AREA_SIZE.width() + self.scrollbar_width,
            PICTURE_AREA_SIZE.height() + self.scrollbar_width)

        self.horizontal_scroll = QtWidgets.QScrollBar(
            QtCore.Qt.Horizontal, self)
        self.vertical_scroll = QtWidgets.QScrollBar(
            QtCore.Qt.Vertical, self)

        self.horizontal_scroll.setFixedWidth(self.widget_size.width())
        self.horizontal_scroll.setFixedHeight(self.scrollbar_width)
        self.horizontal_scroll.valueChanged.connect(self.width_scroll_change)
        self.horizontal_scroll.setGeometry(
            0, PICTURE_AREA_SIZE.height(),
            PICTURE_AREA_SIZE.width(), self.scrollbar_width)

        self.vertical_scroll.setFixedWidth(self.scrollbar_width)
        self.vertical_scroll.setFixedHeight(self.widget_size.height())
        self.vertical_scroll.valueChanged.connect(self.height_scroll_change)
        self.vertical_scroll.setGeometry(
            PICTURE_AREA_SIZE.width(), 0,
            self.scrollbar_width, PICTURE_AREA_SIZE.height())

        self.setFixedSize(self.widget_size)

    def update_picture(self):
        self.pixel_size = self.window.pixel_size
        self.rescale_image()
        self.process_dimensions()
        self.update()

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)
        self.draw_picture(qp)
        qp.end()

    def process_dimensions(self):
        if self.rescaled_size.width() <= PICTURE_AREA_SIZE.width():
            self.width_central_shift = (PICTURE_AREA_SIZE.width() // 2) - \
                                       (self.rescaled_size.width() // 2)
            self.horizontal_scroll.setDisabled(True)
            self.setup_scrollbar_dimensions(self.horizontal_scroll,
                                            PICTURE_AREA_SIZE.width(),
                                            PICTURE_AREA_SIZE.width())

        if self.rescaled_size.width() > PICTURE_AREA_SIZE.width():
            self.horizontal_scroll.setEnabled(True)
            self.setup_scrollbar_dimensions(
                self.horizontal_scroll,
                PICTURE_AREA_SIZE.width() // self.pixel_size,
                self.picture_size.width())

        if self.rescaled_size.height() <= PICTURE_AREA_SIZE.height():
            self.height_central_shift = (PICTURE_AREA_SIZE.height() // 2) - \
                                        (self.rescaled_size.height() // 2)
            self.vertical_scroll.setDisabled(True)
            self.setup_scrollbar_dimensions(self.vertical_scroll,
                                            PICTURE_AREA_SIZE.height(),
                                            PICTURE_AREA_SIZE.height())

        if self.rescaled_size.height() > PICTURE_AREA_SIZE.height():
            self.vertical_scroll.setEnabled(True)
            self.setup_scrollbar_dimensions(
                self.vertical_scroll,
                PICTURE_AREA_SIZE.height() // self.pixel_size,
                self.picture_size.height())

    def setup_scrollbar_dimensions(
            self, scrollbar, page_step, pic_max_dimension):
        scrollbar.setPageStep(page_step)
        scrollbar.setMinimum(0)
        scrollbar.setMaximum(pic_max_dimension - page_step)

    def width_scroll_change(self):
        self.scroll_width_shift = self.horizontal_scroll.value()
        self.update()

    def height_scroll_change(self):
        self.scroll_height_shift = self.vertical_scroll.value()
        self.update()

    def rescale_image(self):
        # размер занимаемой картинкой области
        self.rescaled_size = QSize(
            math.ceil(self.picture_size.width() * self.pixel_size),
            math.ceil(self.picture_size.height() * self.pixel_size))

        if self.rescaled_size.width() <= PICTURE_AREA_SIZE.width():
            # диапазон пикселей по x
            self.width_pixel_count = self.picture_size.width()
        else:
            self.width_pixel_count = int(
                PICTURE_AREA_SIZE.width() // self.pixel_size)

        if self.rescaled_size.height() <= PICTURE_AREA_SIZE.height():
            # диапазон пикселей по y
            self.height_pixel_count = self.picture_size.height()
        else:
            self.height_pixel_count = int(
                PICTURE_AREA_SIZE.height() // self.pixel_size)

    def draw_picture(self, qp):
        size = QSizeF(self.pixel_size, self.pixel_size)

        pixel_width_range = list(
            range(self.scroll_width_shift,
                  self.scroll_width_shift + self.width_pixel_count))
        pixel_height_range = list(
            range(self.scroll_height_shift,
                  self.scroll_height_shift + self.height_pixel_count))

        for y in range(self.height_pixel_count):
            line_index = pixel_height_range[y]
            line = self.rgb_map[line_index]

            for x in range(self.width_pixel_count):
                pixel_index = pixel_width_range[x]
                pixel_color = line[pixel_index]
                if self.bit_depth == 16:
                    color = QColor.fromRgba64(*pixel_color)
                else:
                    color = QColor(*pixel_color)
                brush = QBrush(color)
                left_top = QPointF(
                    x * self.pixel_size + self.width_central_shift,
                    y * self.pixel_size + self.height_central_shift)
                rect = QRectF(left_top, size)
                qp.fillRect(rect, brush)
