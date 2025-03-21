# !/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
from typing import Sequence

import numpy as np
import serial
import struct

from pybpodapi.exceptions.bpod_error import BpodErrorException

logger = logging.getLogger(__name__)


class DataType(object):
    def __init__(self, name: str, size: int):
        self.name = name
        self.size = size

    def __str__(self):
        return self.name


class ArduinoTypes(object):
    BYTE = DataType("byte", 1)
    CHAR = DataType("char", 1)
    UINT8 = DataType("uint8", 1)
    INT16 = DataType("int16", 2)
    UINT16 = DataType("uint16", 2)
    UINT32 = DataType("uint32", 4)
    UINT64 = DataType("uint64", 8)
    FLOAT32 = DataType("float32", 4)
    FLOAT64 = DataType("float64", 8)

    @staticmethod
    def get_array(array: Sequence, dtype: DataType) -> bytes:
        if dtype in (ArduinoTypes.CHAR, ArduinoTypes.UINT8):
            return ArduinoTypes.get_uint8_array(array)
        elif dtype == ArduinoTypes.UINT16:
            return ArduinoTypes.get_uint16_array(array)
        elif dtype == ArduinoTypes.UINT32:
            return ArduinoTypes.get_uint32_array(array)
        elif dtype == ArduinoTypes.FLOAT32:
            return ArduinoTypes.get_float32_array(array)
        else:
            raise BpodErrorException(f"dtype {dtype} not supported by get_array()")

    @staticmethod
    def get_uint8_array(array) -> bytes:
        return np.array(array, dtype=str(ArduinoTypes.UINT8)).tobytes()
        # the above will coerce floats to ints! Alternative:
        # return struct.pack('<' + 'B' * len(array), *array)

    @staticmethod
    def get_int16_array(array) -> bytes:
        return np.array(array, dtype=str(ArduinoTypes.INT16)).tobytes()
        # the above will coerce floats to ints! Alternative:
        # return struct.pack('<' + 'h' * len(array), *array)

    @staticmethod
    def get_uint16_array(array) -> bytes:
        return np.array(array, dtype=str(ArduinoTypes.UINT16)).tobytes()
        # the above will coerce floats to ints! Alternative:
        # return struct.pack('<' + 'H' * len(array), *array)

    @staticmethod
    def get_uint32_array(array) -> bytes:
        return np.array(array, dtype=str(ArduinoTypes.UINT32)).tobytes()
        # the above will coerce floats to ints! Alternative:
        # return struct.pack('<' + 'I' * len(array), *array)

    @staticmethod
    def get_float32_array(array) -> bytes:
        return struct.pack('<' + 'f' * len(array), *array)

    @staticmethod
    def get_float(value) -> bytes:
        return struct.pack("<f", value)

    @staticmethod
    def cvt_float32(message_bytes) -> float:
        return struct.unpack("<f", message_bytes)[0]

    @staticmethod
    def cvt_float64(message_bytes) -> float:
        return struct.unpack("<d", message_bytes)[0]

    @staticmethod
    def cvt_int64(message_bytes) -> int:
        return struct.unpack("<q", message_bytes)[0]

    @staticmethod
    def cvt_uint32(message_bytes) -> int:
        return struct.unpack("<L", message_bytes)[0]

    @staticmethod
    def cvt_uint64(message_bytes) -> int:
        return struct.unpack("<Q", message_bytes)[0]


class ArCOM(object):
    """
    ArCOM is an interface to simplify data transactions between Arduino and Python.
    """

    def open(self, serial_port, baudrate=115200, timeout=1):
        """
        Open serial connection
        :param serialPortName:
        :param baudRate:
        :return:
        """
        self.serial_object = serial.Serial(
            serial_port, baudrate=baudrate, timeout=timeout
        )

        return self

    def close(self):
        """
        Close serial connection
        :return:
        """
        self.serial_object.close()

    def bytes_available(self):
        """

        :return:
        """
        return self.serial_object.inWaiting()

    ##############################################################
    ## WRITE #####################################################
    ##############################################################

    def write_char(self, value) -> None:
        self.serial_object.write(str.encode(value))

    def write_array(self, array) -> None:
        self.serial_object.write(array)

    ##############################################################
    ## READ BYTE #################################################
    ##############################################################

    def read_formatted(self, format_string: str) -> tuple:
        n_bytes = struct.calcsize(format_string)
        data = self.serial_object.read(n_bytes)
        return struct.unpack(format_string, data)

    def iter_read_formatted(self, format_string: str, n_iterations: int) -> tuple:
        n_bytes = struct.calcsize(format_string) * n_iterations
        data = self.serial_object.read(n_bytes)
        return struct.iter_unpack(format_string, data)

    def read_byte(self) -> bytes:
        return self.serial_object.read(1)

    def read_char(self) -> str:
        return self.serial_object.read(1).decode("utf-8")

    def read_uint8(self) -> int:
        return self.read_formatted('<B')[0]

    def read_uint16(self) -> int:
        return self.read_formatted('<H')[0]

    def read_uint32(self) -> int:
        return self.read_formatted('<I')[0]

    def read_uint64(self) -> int:
        return self.read_formatted('<Q')[0]

    def read_float32(self) -> float:
        return self.read_formatted('<f')[0]

    def read_int8(self) -> int:
        return self.read_formatted('<b')[0]

    def read_int16(self) -> int:
        return self.read_formatted('<h')[0]

    def read_int32(self) -> int:
        return self.read_formatted('<i')[0]

    def read_int64(self) -> int:
        return self.read_formatted('<q')[0]

    ##############################################################
    ## READ ARRAY ################################################
    ##############################################################

    def read_bytes_array(self, array_len=1) -> list[bytes]:
        data = self.serial_object.read(array_len)
        return [bytes([byte]) for byte in data]

    def read_char_array(self, array_len=1) -> list[str]:
        data = self.serial_object.read(array_len)
        return list(data.decode('UTF8'))

    def read_uint8_array(self, array_len=1) -> list[int]:
        return list(self.read_formatted('<' + 'B' * array_len))

    def read_uint16_array(self, array_len=1) -> list[int]:
        return list(self.read_formatted('<' + 'H' * array_len))

    def read_uint32_array(self, array_len=1) -> list[int]:
        return list(self.read_formatted('<' + 'I' * array_len))

    def read_uint64_array(self, array_len=1) -> list[int]:
        return list(self.read_formatted('<' + 'Q' * array_len))

    def read_float32_array(self, array_len=1) -> list[float]:
        return list(self.read_formatted('<' + 'f' * array_len))
