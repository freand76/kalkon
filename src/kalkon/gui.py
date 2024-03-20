# Copyright (c) Fredrik Andersson, 2023-2024
# All rights reserved

"""The kalkon calculator GUI"""

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QLineEdit, QMainWindow, QTextEdit, QVBoxLayout, QWidget

from .kalkon import Kalkon, ValueFormat, ValueType


WIDGET_STYLESHEET = """
color: rgb(0, 255, 0);
background-color: rgb(0, 0, 0);
margin:0px; border:2px solid rgb(0, 64, 0);
"""


class History(QTextEdit):
    """
    The result and history field of the calculator
    """

    def __init__(self, parent, kalkon):
        super().__init__(parent)
        self._parent = parent
        self._kalkon = kalkon
        self._num_lines = 1
        self._num_cols = 1
        self.setStyleSheet(WIDGET_STYLESHEET)
        self.setFont(parent.get_font())
        self.setReadOnly(True)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setFocusPolicy(Qt.NoFocus)
        self._parent.sig_input_field_change.connect(self._input_field_change)
        self._parent.sig_stack_updated.connect(self._stack_updated)

    def resizeEvent(self, new_size):
        """Qt event"""
        super().resizeEvent(new_size)
        self._num_lines = self.height() // self.fontMetrics().height() - 1
        self._num_cols = self.width() // self.fontMetrics().horizontalAdvance("A") - 2
        self._update()

    def _update(self):
        box_string = ""
        for index in range(0, self._num_lines):
            line_str = self._kalkon.get_expression(index)
            if line_str:
                line_str += " = " + self._kalkon.get_result(index)
            else:
                line_str = ""
            if len(line_str) > self._num_cols:
                line_str = "..."
            box_string = line_str + "\n" + box_string

        self.setText(box_string)

    def _input_field_change(self, _):
        self._update()

    def _stack_updated(self):
        self._update()


class InputField(QLineEdit):
    """
    The input field of the calculator
    """

    def __init__(self, parent, kalkon):
        super().__init__(parent)
        self._parent = parent
        self._kalkon = kalkon
        self._shift_pressed = False
        self.setStyleSheet(WIDGET_STYLESHEET)
        self.textChanged.connect(self._text_changed)
        self.returnPressed.connect(self._enter)
        font = self._parent.get_font()
        self.setFont(font)
        self._parent.sig_update_input.connect(self._update_input)

    def event(self, event):
        """Override widget event function"""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            # TAB
            return True
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Shift:
            self._shift_pressed = True
        elif event.type() == QEvent.KeyRelease and event.key() == Qt.Key_Shift:
            self._shift_pressed = False
        elif (
            self._shift_pressed
            and event.type() == QEvent.KeyPress
            and event.key() in [Qt.Key_Enter, Qt.Key_Return]
        ):
            expression = self._kalkon.pop()
            self._parent.sig_stack_updated.emit()
            self._parent.sig_update_input.emit(expression)
            return True

        return QLineEdit.event(self, event)

    def _update_input(self, expression):
        self.setText(expression)

    def _update(self, enter=False):
        expression = self.text()
        clear = self._kalkon.evaluate(expression, enter)
        if clear:
            self.setText("")
        self._parent.sig_input_field_change.emit(expression)
        status_str = self._kalkon.get_status()
        if status_str:
            self._parent.sig_update_status.emit(status_str.replace("\n", "::").strip())
        else:
            self._parent.sig_update_status.emit("")
        self._parent.sig_update_control.emit()

    def _enter(self):
        self._update(True)
        if self._kalkon.is_stack_updated() and not self._kalkon.is_error():
            self._parent.sig_stack_updated.emit()

    def _text_changed(self):
        self._update(False)


class CentralWidget(QWidget):
    """
    The central widget with the top widget and circuit editor widget.
    """

    sig_input_field_change = Signal(str)
    sig_stack_updated = Signal()
    sig_update_input = Signal(str)
    sig_update_status = Signal(str)
    sig_update_control = Signal()

    @staticmethod
    def get_font(fontsize=20):
        """Get default font"""
        font = QFont("Monospace")
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(fontsize)
        return font

    def __init__(self, parent, kalkon):
        super().__init__(parent)
        self._kalkon = kalkon

        self.setLayout(QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        self._control_field = QLabel("")
        self._control_field.setStyleSheet(WIDGET_STYLESHEET)
        self._control_field.setFont(self.get_font(10))
        self.layout().addWidget(self._control_field)
        self.layout().setStretchFactor(self._control_field, 0)

        history_view = History(self, kalkon)
        self.layout().addWidget(history_view)
        self.layout().setStretchFactor(history_view, 1)

        self._status_field = QLabel("")
        self._status_field.setStyleSheet(WIDGET_STYLESHEET)
        self._status_field.setFont(self.get_font(10))
        self.layout().addWidget(self._status_field)
        self.layout().setStretchFactor(self._status_field, 0)

        input_field = InputField(self, kalkon)
        self.layout().addWidget(input_field)
        self.layout().setStretchFactor(input_field, 0)

        self.sig_update_status.connect(self._update_status)
        self.sig_update_control.connect(self._update_control)
        self.sig_update_control.emit()

    def _update_control(self):
        _enum_to_text = {
            ValueFormat.DECIMAL: "DEC",
            ValueFormat.HEXADECIMAL: "HEX",
            ValueFormat.BINARY: "BIN",
            ValueType.F32: "F32/IEEE-754",
            ValueType.FLOAT: "FLOAT       ",
            ValueType.INT: "INTEGER     ",
            ValueType.INT8: "INT8        ",
            ValueType.INT16: "INT16       ",
            ValueType.INT32: "INT32        ",
            ValueType.INT64: "INT64        ",
            ValueType.UINT8: "UINT8        ",
            ValueType.UINT16: "UINT16       ",
            ValueType.UINT32: "UINT32       ",
            ValueType.UINT64: "UINT64       ",
        }

        value_type = self._kalkon.get_type()
        value_format = self._kalkon.get_format()
        control_string = f"{_enum_to_text[value_type]} {_enum_to_text[value_format]}"
        self._control_field.setText(control_string)

    def _update_status(self, status_str):
        self._status_field.setText(status_str)


class MainWindow(QMainWindow):
    """
    The main window for the applicaton.
    """

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Kalkon")
        self.resize(800, 600)
        kalkon = Kalkon()
        central_widget = CentralWidget(self, kalkon)
        self.setCentralWidget(central_widget)
