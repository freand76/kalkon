# Copyright (c) Fredrik Andersson, 2023
# All rights reserved

"""The kalkon calculator application and GUI"""

# pylint: disable=too-few-public-methods

import struct
from enum import Enum, auto
from functools import partial

from asteval import Interpreter

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtGui import QFont
from PySide6.QtWidgets import QLabel, QLineEdit, QMainWindow, QTextEdit, QVBoxLayout, QWidget


WIDGET_STYLESHEET = """
color: rgb(0, 255, 0);
background-color: rgb(0, 0, 0);
margin:0px; border:2px solid rgb(0, 255, 0);
"""


class ValueType(Enum):
    """Value Type class"""

    F32 = auto()
    INT8 = auto()
    INT16 = auto()
    INT32 = auto()
    INT64 = auto()
    UINT8 = auto()
    UINT16 = auto()
    UINT32 = auto()
    UINT64 = auto()


class ValueFormat(Enum):
    """Value System class"""

    DECIMAL = auto()
    HEXADECIMAL = auto()
    BINARY = auto()


class Kalkon:
    """The kalkon calculator class"""

    STACK_DEPTH = 5

    def __init__(self):
        super().__init__()
        self._stack = None
        self._type = ValueType.INT64
        self._format = ValueFormat.DECIMAL
        self._status = ""
        self._error = False
        self._stack_updated = False
        self._interpreter = Interpreter(
            use_numpy=False,
            minimal=True,
        )
        self.clear()

    def _set_type(self, value_type):
        self._type = value_type

    def _set_format(self, system):
        self._format = system

    def get_type(self):
        """Get value type"""
        return self._type

    def get_format(self):
        """Get value format"""
        return self._format

    def clear(self):
        """Clear history"""
        self._stack = []
        self._stack_updated = True

    def is_error(self):
        """Is the current field an error?"""
        return self._error

    def is_stack_updated(self):
        """Is the stack updated?"""
        stack_updated = self._stack_updated
        self._stack_updated = False
        return stack_updated

    def get_status(self):
        """Return status"""
        return self._status

    def _is_signed_type(self):
        if self._type in [ValueType.INT8, ValueType.INT16, ValueType.INT32, ValueType.INT64]:
            return True
        return False

    def _get_typed_result(self, value):
        if self._type == ValueType.F32:
            return value
        signed = self._is_signed_type()
        int_value = int(value)
        try:
            value_bytes = int_value.to_bytes(8, "little", signed=True)
        except OverflowError:
            print("OverflowError")
            return None
        width = 1
        if self._type in [ValueType.INT8, ValueType.UINT8]:
            width = 1
        elif self._type in [ValueType.INT16, ValueType.UINT16]:
            width = 2
        elif self._type in [ValueType.INT32, ValueType.UINT32]:
            width = 4
        elif self._type in [ValueType.INT64, ValueType.UINT64]:
            width = 8
        return int.from_bytes(value_bytes[0:width], "little", signed=signed)

    def _get_formatted_result(self, value):  # pylint: disable=too-many-return-statements
        if value is None:
            return ""
        if self._format == ValueFormat.BINARY:
            if self._type == ValueType.F32:
                value_bytes = struct.pack("f", value)
                value = int.from_bytes(value_bytes[0:4], "little")
                return f"{bin(value)}"
            negative = "-" if value < 0 else ""
            value = abs(value)
            return f"{negative}0b{int(value):b}"
        if self._format == ValueFormat.HEXADECIMAL:
            if self._type == ValueType.F32:
                value_bytes = struct.pack("f", value)
                value = int.from_bytes(value_bytes[0:4], "little")
                return f"{hex(value)}"
            negative = "-" if value < 0 else ""
            value = abs(value)
            return f"{negative}0x{int(value):x}"
        if self._type == ValueType.F32:
            value_bytes = struct.pack("f", value)
            value = struct.unpack("f", value_bytes)[0]
            return str(value)
        return str(value)

    def get_result(self, index=0):
        """Return result"""
        if index >= len(self._stack):
            return ""
        value = self._stack[index][1]
        if value is None:
            return ""
        value = self._get_typed_result(value)
        value = self._get_formatted_result(value)
        return value

    def get_expression(self, index=0):
        """Return expression"""
        if index >= len(self._stack):
            return ""
        return self._stack[index][0]

    def _push(self, expression, result):
        self._stack[0] = (None, None)
        self._stack.insert(1, (expression, result))
        self._stack_updated = True

    def pop(self):
        """Pop item from stack"""
        expression = ""
        if len(self._stack) > 1:
            (expression, _) = self._stack[1]
        if len(self._stack) > 0:
            self._stack.pop(0)
            self._stack_updated = True
        if len(self._stack) > 0:
            self._stack[0] = (None, None)
        return expression

    def _set(self, expression, result):
        if len(self._stack) == 0:
            self._stack.append((expression, result))
        else:
            self._stack[0] = (expression, result)
        self._stack_updated = True

    def _process_command(self, expression, enter):
        _cmd_dict = {
            ":dec": partial(self._set_format, ValueFormat.DECIMAL),
            ":hex": partial(self._set_format, ValueFormat.HEXADECIMAL),
            ":bin": partial(self._set_format, ValueFormat.BINARY),
            ":f32": partial(self._set_type, ValueType.F32),
            ":i8": partial(self._set_type, ValueType.INT8),
            ":i16": partial(self._set_type, ValueType.INT16),
            ":i32": partial(self._set_type, ValueType.INT32),
            ":i64": partial(self._set_type, ValueType.INT64),
            ":u8": partial(self._set_type, ValueType.UINT8),
            ":u16": partial(self._set_type, ValueType.UINT16),
            ":u32": partial(self._set_type, ValueType.UINT32),
            ":u64": partial(self._set_type, ValueType.UINT64),
            ":clear": self.clear,
        }
        if not expression.startswith(":"):
            return False

        if expression in _cmd_dict and enter:
            _cmd_dict[expression]()
            return True
        if expression in _cmd_dict:
            self._status = f"CMD: {expression}"
            return True

        self._status = f"Unknown command '{expression}'"
        return True

    def _validate_set_variable(self, expression):
        if "==" in expression:
            return False
        if "=" not in expression:
            return False
        validator = Interpreter(
            use_numpy=False,
            minimal=True,
        )
        validator(expression, show_errors=False, raise_errors=False)
        if len(validator.error) > 0:
            return False
        return True

    def evaluate(self, expression, enter=False):  # pylint: disable=too-many-return-statements
        """Evaluate expression"""
        self._status = ""
        self._error = False

        if not expression:
            self._set(None, None)
            return False

        if self._process_command(expression, enter):
            if self._status:
                return False
            if enter:
                self._set(None, None)
                return True
            return False

        if self._validate_set_variable(expression):
            self._status = f"Set {expression}"
            if enter:
                self._set(None, None)
                self._interpreter(expression, show_errors=False, raise_errors=False)
                return True
            return False

        result = self._interpreter(expression, show_errors=False, raise_errors=False)
        if result is not None and "<built-in function" in str(result):
            result = ""
            return False

        if len(self._interpreter.error) == 0:
            if enter:
                self._push(expression, result)
                return True
            self._set(expression, result)
        else:
            self._status = self._interpreter.error[0].get_error()[1]
            self._error = True

        return False


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
        self.setFocusPolicy(Qt.NoFocus)
        self._parent.sig_input_field_change.connect(self._input_field_change)
        self._parent.sig_stack_updated.connect(self._stack_updated)

    def resizeEvent(self, new_size):
        """Qt event"""
        super().resizeEvent(new_size)
        self._num_lines = self.height() // self.fontMetrics().height() - 2
        self._num_cols = self.width() // self.fontMetrics().horizontalAdvance("A") - 2
        self._update()

    def _update(self):
        box_string = ""
        for index in range(0, self._num_lines):
            line_str = self._kalkon.get_expression(index)
            if line_str:
                result_str = " = " + self._kalkon.get_result(index)
                max_length = self._num_cols - len(line_str)
                if max_length > 0:
                    line_str = line_str + f"{result_str:>{max_length}}"
                else:
                    line_str = line_str + " = ..."
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
        self.resize(640, 400)
        kalkon = Kalkon()
        central_widget = CentralWidget(self, kalkon)
        self.setCentralWidget(central_widget)
