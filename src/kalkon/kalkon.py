# Copyright (c) Fredrik Andersson, 2023
# All rights reserved

"""The kalkon calculator application and GUI"""

# pylint: disable=too-few-public-methods

from enum import Enum, auto
from functools import partial

from asteval import Interpreter

from PySide6.QtCore import QEvent, Qt, Signal
from PySide6.QtWidgets import QGridLayout, QLabel, QLineEdit, QMainWindow, QVBoxLayout, QWidget


WIDGET_STYLESHEET = """
color: rgb(0, 255, 0);
background-color: rgb(0, 0, 0);
margin:0px; border:2px solid rgb(0, 255, 0);
"""


class ValueType(Enum):
    """Value Type class"""

    INT = auto()
    INT8 = auto()
    INT16 = auto()
    INT32 = auto()
    INT64 = auto()
    UINT8 = auto()
    UINT16 = auto()
    UINT32 = auto()
    UINT64 = auto()


class ValueSystem(Enum):
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
        self._type = ValueType.INT
        self._system = ValueSystem.DECIMAL
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
        print(self._type)

    def _set_system(self, system):
        self._system = system
        print(self._system)

    def clear(self):
        """Clear history"""
        self._stack = []
        for _ in range(0, self.STACK_DEPTH):
            self._stack.append((None, None))

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

    def get_result(self, index=0):
        """Return result"""
        result = self._stack[index][1] or ""
        return str(result)

    def get_expression(self, index=0):
        """Return expression"""
        return self._stack[index][0] or ""

    def _push(self, expression, result):
        self._stack[0] = (None, None)
        self._stack.insert(1, (expression, result))
        while len(self._stack) > self.STACK_DEPTH:
            self._stack.pop()
        self._stack_updated = True

    def _set(self, expression, result):
        self._stack[0] = (expression, result)
        self._stack_updated = True

    def _process_command(self, expression, enter):
        _cmd_dict = {
            ":dec": partial(self._set_system, ValueSystem.DECIMAL),
            ":hex": partial(self._set_system, ValueSystem.HEXADECIMAL),
            ":bin": partial(self._set_system, ValueSystem.BINARY),
            ":int": partial(self._set_type, ValueType.INT),
            ":i8": partial(self._set_type, ValueType.INT8),
            ":i16": partial(self._set_type, ValueType.INT16),
            ":i32": partial(self._set_type, ValueType.INT32),
            ":i64": partial(self._set_type, ValueType.INT64),
            ":u8": partial(self._set_type, ValueType.UINT8),
            ":u16": partial(self._set_type, ValueType.UINT16),
            ":u32": partial(self._set_type, ValueType.UINT32),
            ":u64": partial(self._set_type, ValueType.UINT64),
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

        if len(self._interpreter.error) == 0:
            if enter:
                self._push(expression, result)
                return True
            self._set(expression, result)
        else:
            self._status = self._interpreter.error[0].get_error()[1]
            self._error = True

        return False


class History(QWidget):
    """
    The result and history field of the calculator
    """

    def __init__(self, parent, kalkon):
        super().__init__(parent)
        self._parent = parent
        self._kalkon = kalkon
        self.setLayout(QGridLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)
        self._expression = {}
        self._result = {}
        depth = self._kalkon.STACK_DEPTH
        for index in range(0, depth):
            self._expression[index] = QLabel("")
            self._expression[index].setStyleSheet(WIDGET_STYLESHEET)
            self.layout().addWidget(self._expression[index], depth - index - 1, 0)
            self._result[index] = QLabel("")
            self._result[index].setStyleSheet(WIDGET_STYLESHEET)
            self.layout().addWidget(self._result[index], depth - index - 1, 1)
        self._parent.sig_input_field_change.connect(self._input_field_change)
        self._parent.sig_input_field_push.connect(self._input_field_push)

    def _input_field_change(self, expression):
        self._expression[0].setText(expression)
        status = self._kalkon.get_status()
        if status:
            self._result[0].setText(status.replace("\n", "::").strip())
        else:
            self._result[0].setText(self._kalkon.get_result())

    def _input_field_push(self):
        for key, expr in self._expression.items():
            expr.setText(self._kalkon.get_expression(key))
            self._result[key].setText(self._kalkon.get_result(key))


class InputField(QLineEdit):
    """
    The input field of the calculator
    """

    def __init__(self, parent, kalkon):
        super().__init__(parent)
        self._parent = parent
        self._kalkon = kalkon
        self.setStyleSheet(WIDGET_STYLESHEET)
        self.textChanged.connect(self._text_changed)
        self.returnPressed.connect(self._enter)

    def event(self, event):
        """Override widget event function"""
        if event.type() == QEvent.KeyPress and event.key() == Qt.Key_Tab:
            print("TAB")
            return True
        return QLineEdit.event(self, event)

    def _update(self, enter=False):
        expression = self.text()
        clear = self._kalkon.evaluate(expression, enter)
        if clear:
            self.setText("")
        self._parent.sig_input_field_change.emit(expression)

    def _enter(self):
        self._update(True)
        if self._kalkon.is_stack_updated() and not self._kalkon.is_error():
            self._parent.sig_input_field_push.emit()

    def _text_changed(self):
        self._update(False)


class CentralWidget(QWidget):
    """
    The central widget with the top widget and circuit editor widget.
    """

    sig_input_field_change = Signal(str)
    sig_input_field_push = Signal()

    def __init__(self, parent, kalkon):
        super().__init__(parent)
        self.setLayout(QVBoxLayout(self))
        self.layout().setContentsMargins(0, 0, 0, 0)
        self.layout().setSpacing(0)

        history_view = History(self, kalkon)
        self.layout().addWidget(history_view)
        self.layout().setStretchFactor(history_view, 1)

        input_field = InputField(self, kalkon)
        self.layout().addWidget(input_field)
        self.layout().setStretchFactor(input_field, 0)


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
