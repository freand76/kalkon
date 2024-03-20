# Copyright (c) Fredrik Andersson, 2023-2024
# All rights reserved

"""The kalkon calculator class"""

import struct
from enum import Enum, auto
from functools import partial

from asteval import Interpreter


class ValueType(Enum):
    """Value Type class"""

    FLOAT = auto()
    F32 = auto()
    INT = auto()
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
        self._type = ValueType.FLOAT
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
        if value_type == ValueType.FLOAT and self._format == ValueFormat.BINARY:
            self._status = "No binary representation for float"
        else:
            self._type = value_type

    def _set_format(self, value_format):
        if self._type == ValueType.FLOAT and value_format == ValueFormat.BINARY:
            self._status = "No binary representation for float"
        else:
            self._format = value_format

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
        if self._type == ValueType.INT:
            return int(value)
        if self._type in [ValueType.F32, ValueType.FLOAT, ValueType.INT]:
            return value
        signed = self._is_signed_type()
        int_value = int(value)
        try:
            value_bytes = int_value.to_bytes(8, "little", signed=True)
        except OverflowError:
            self._status = "Input overflow"
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

    def _get_formatted_result(self, value):
        result_str = ""
        if value is None:
            result_str = ""
        elif self._format == ValueFormat.BINARY:
            if self._type == ValueType.FLOAT:
                result_str = ""
            elif self._type == ValueType.F32:
                value_bytes = struct.pack("f", value)
                value = int.from_bytes(value_bytes[0:4], "little")
                result_str = f"{bin(value)}"
            else:
                result_str = bin(value)
        elif self._format == ValueFormat.HEXADECIMAL:
            if self._type == ValueType.FLOAT:
                result_str = float.hex(float(value))
            elif self._type == ValueType.F32:
                value_bytes = struct.pack("f", value)
                value = int.from_bytes(value_bytes[0:4], "little")
                result_str = hex(value)
            else:
                result_str = hex(value)
        else:
            if self._type == ValueType.F32:
                value_bytes = struct.pack("f", value)
                value = struct.unpack("f", value_bytes)[0]
            result_str = str(value)
        return result_str

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
            ":float": partial(self._set_type, ValueType.FLOAT),
            ":dec": partial(self._set_format, ValueFormat.DECIMAL),
            ":hex": partial(self._set_format, ValueFormat.HEXADECIMAL),
            ":bin": partial(self._set_format, ValueFormat.BINARY),
            ":f32": partial(self._set_type, ValueType.F32),
            ":int": partial(self._set_type, ValueType.INT),
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

    def evaluate(self, expression, enter=False):
        """Evaluate expression"""
        self._status = ""
        self._error = False

        if not expression:
            self._set(None, None)
            return False

        expression = expression.replace(",", ".")

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
        if result is not None and ("<built-in function" in str(result) or "<class" in str(result)):
            result = ""
            return False

        if isinstance(result, str):
            self._status = "Strings are not supported"
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
