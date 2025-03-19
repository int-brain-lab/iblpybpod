# !/usr/bin/python3
# -*- coding: utf-8 -*-

import logging
import serial
import numpy as np
import struct

logger = logging.getLogger(__name__)


class DataType(object):
    def __init__(self, name, size):
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
    def get_array(array, dtype):
        if dtype == ArduinoTypes.CHAR or dtype == ArduinoTypes.UINT8:
            return ArduinoTypes.get_uint8_array(array)
        elif dtype == ArduinoTypes.UINT16:
            return ArduinoTypes.get_uint16_array(array)
        elif dtype == ArduinoTypes.UINT32 or dtype == ArduinoTypes.FLOAT:
            return ArduinoTypes.get_uint32_array(array)
        else:
            return None

    @staticmethod
    def get_uint8_array(array):
        return np.array(array, dtype=str(ArduinoTypes.UINT8)).tobytes()

    @staticmethod
    def get_int16_array(array):
        return np.array(array, dtype=str(ArduinoTypes.INT16)).tobytes()

    @staticmethod
    def get_uint16_array(array):
        return np.array(array, dtype=str(ArduinoTypes.UINT16)).tobytes()

    @staticmethod
    def get_uint32_array(array):
        return np.array(array, dtype=str(ArduinoTypes.UINT32)).tobytes()

    @staticmethod
    def get_float(value):
        return struct.pack("<f", value)

    @staticmethod
    def cvt_float32(message_bytes):
        return struct.unpack("<f", message_bytes)[0]

    @staticmethod
    def cvt_float64(message_bytes):
        return struct.unpack("<d", message_bytes)[0]

    @staticmethod
    def cvt_int64(message_bytes):
        return int.from_bytes(message_bytes, byteorder="little")

    @staticmethod
    def cvt_uint32(message_bytes):
        return struct.unpack("<L", message_bytes)[0]

    @staticmethod
    def cvt_uint64(message_bytes):
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

    def write_char(self, value):
        self.serial_object.write(str.encode(value))

    def write_array(self, array):
        self.serial_object.write(array)

    ##############################################################
    ## READ BYTE #################################################
    ##############################################################

    def read_formatted(self, format_string: str) -> tuple:
        n_bytes = struct.calcsize(format_string)
        data = self.serial_object.read(n_bytes)
        return struct.unpack(format_string, data)

    def read_byte(self) -> bytes:
        data = self.serial_object.read(1)
        return data

    def read_char(self) -> str:
        data = self.serial_object.read(1)
        return data.decode("utf-8")

    def read_uint8(self) -> int:
        data = self.serial_object.read(1)
        message, = struct.unpack('<B', data)
        return message

    def read_uint16(self) -> int:
        data = self.serial_object.read(2)
        message, = struct.unpack('<H', data)
        return message

    def read_uint32(self) -> int:
        data = self.serial_object.read(4)
        message, = struct.unpack('<I', data)
        return message

    def read_uint64(self) -> int:
        data = self.serial_object.read(8)
        message, = struct.unpack('<Q', data)
        return message

    def read_float32(self) -> float:
        data = self.serial_object.read(4)
        message = struct.unpack("<f", data)
        return message[0]

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
        data = self.serial_object.read(array_len)
        return list(struct.unpack('<' + 'B' * array_len, data))

    def read_uint16_array(self, array_len=1) -> list[int]:
        data = self.serial_object.read(array_len)
        return list(struct.unpack('<' + 'H' * array_len * 2, data))

    def read_uint32_array(self, array_len=1) -> list[int]:
        data = self.serial_object.read(array_len)
        return list(struct.unpack('<' + 'I' * array_len * 4, data))

    def read_uint64_array(self, array_len=1) -> list[int]:
        data = self.serial_object.read(array_len)
        return list(struct.unpack('<' + 'Q' * array_len * 8, data))

    def read_float32_array(self, array_len=1) -> list[float]:
        data = self.serial_object.read(array_len)
        return list(struct.unpack('<' + 'f' * array_len * 4, data))
