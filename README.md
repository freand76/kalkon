![Python Version from PEP 621 TOML](https://img.shields.io/python/required-version-toml?tomlFilePath=https%3A%2F%2Fraw.githubusercontent.com%2Ffreand76%2Fkalkon%2Fmain%2Fpyproject.toml)
![PyPI - Version](https://img.shields.io/pypi/v/kalkon)
![PyPI - Downloads](https://img.shields.io/pypi/dm/kalkon)

# Kalkon - /kalˈkuːn/

*Swedish Noun*

*1. a turkey; a kind of large bird (colloquial)*

*2. a turkey; a failure*

*3. a python/asteval based calculator*

<p align="center">
  <img alt="Kalkon" src="https://raw.githubusercontent.com/freand76/kalkon/09cf8aa94aaf30b82a9e00e68c696bd3865af394/src/kalkon/images/kalkon.png" width=50%>
</p>

## Quickstart

### Install from PyPi
```
pip3 install kalkon
```

### Install from GitHub
```
> git clone https://github.com/freand76/kalkon.git
> cd kalkon
> python3 -m pip install .
```

### Start

Start using python.

```
> python3 -m kalkon
```

Start using shell script (if the pip3 bin-folder is in your path).

```
> kalkon
```

## Calculator

<p align="center">
  <img alt="Kalkon" src="https://raw.githubusercontent.com/freand76/kalkon/09cf8aa94aaf30b82a9e00e68c696bd3865af394/images/screenshot.png">
</p>

### Asteval

The calculator uses the [asteval](https://pypi.org/project/asteval) package to evaluate expressions.

Asteval handles python-like expression and will obey python rules for arithmetic and logic operators.

*Example*
```python
int(sin(pi/3)*log(5) + 0xfe) & 0x23
```

Asteval also handles variables, i.e. you can give variable a value and use it for later calculations.

*Example: Set variable*
```python
foo=3
```

*Example: Use variable*
```python
10 + foo * 5
```

### Commands

All commands start with a colon character
*Example:* **:hex**

**Output format commands**

The calculator can show the result of the expression in several different modes, enter one of the following commands to switch to the desired mode.

| Command | Description |
| :------ | :---------- |
| :float  | Show results as floating point |
| :f32    | Show results as 32-bit float / ieee-754 |
| :int    | Show results as integer, floats will be truncated |
| :i8"    | Show results as signed 8-bit integer |
| :i16    | Show results as signed 16-bit integer |
| :i32    | Show results as signed 32-bit integer |
| :i64    | Show results as signed 64-bit integer |
| :u8     | Show results as unsigned 8-bit integer |
| :u16    | Show results as unsigned 16-bit integer |
| :u32    | Show results as unsigned 32-bit integer |
| :u64    | Show results as unsigned 64-bit integer |
| :dec    | Show results as decimal values |
| :hex    | Show results as hexadecimal values |
| :bin    | Show results as binary values |


**Control commands**

The following command will clear the calculator stack.

| Command | Description |
| :------ | :---------- |
| :clear  | Clear the calculator stack |

### Shortcuts

| Shortcut | Description |
| :------- | :---------- |
| Shift+Enter | Drop stack item to editable field |
