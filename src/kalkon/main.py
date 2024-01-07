# Copyright (c) Fredrik Andersson, 2023-2024
# All rights reserved

""" The main function module of the kalkon calculator """

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon, QPainter, QPixmap
from PySide6.QtWidgets import QApplication

from .gui import MainWindow


def main():
    """The main function of kalkon calculator"""
    app = QApplication(sys.argv)
    main_path = Path(__file__).parent
    image_path = main_path / "images/kalkon.png"
    image_pixmap = QPixmap(image_path)
    size = max(image_pixmap.size().height(), image_pixmap.size().width())
    icon_pixmap = QPixmap(size, size)
    icon_pixmap.fill(Qt.transparent)
    painter = QPainter(icon_pixmap)
    painter.drawPixmap(
        (icon_pixmap.size().width() - image_pixmap.size().width()) // 2,
        (icon_pixmap.size().height() - image_pixmap.size().height()) // 2,
        image_pixmap,
    )
    painter.end()
    icon = QIcon(icon_pixmap)
    app.setWindowIcon(icon)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
