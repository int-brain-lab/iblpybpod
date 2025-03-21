import struct

from pybpodapi.com.arcom import ArCOM, ArduinoTypes


class RotaryEncoderModule(object):
    arcom: ArCOM | None = None

    COM_HANDSHAKE        = 'C'
    COM_TOGGLEEVTTRANSM  = ord('V')
    COM_TOGGLEOUTPUTSTREAM = ord('O')
    COM_TOGGLESTREAM     = ord('S')
    COM_STARTLOGGING     = ord('L')
    COM_STOPLOGGING      = ord('F')
    COM_GETLOGDATA       = ord('R')
    COM_GETCURRENTPOS    = ord('Q')
    COM_SETZEROPOS       = ord('Z')
    COM_SETPOS           = ord('P')
    COM_ENABLETHRESHOLDS = ord(';')
    COM_SETPREFIX        = ord('I')
    COM_SETTHRESHOLDS    = ord('T')
    COM_SETWRAPPOINT     = ord('W')

    def __init__(self, serialport=None):
        """
        Constructor of the RotaryEncoderModule object
        A serial connection to the Rotary Encoder board is opened at the construction of the object.

        :ivar str serialport: PC serial port where the module is connected
        """
        if serialport:
            self.open(serialport)

    def open(self, serialport):
        """
        Opens a serial connection to the Rotary Encoder board.

        :ivar str serialport: PC serial port where the module is connected
        """
        self.arcom = ArCOM().open(serialport, 115200)
        self.arcom.write_char(self.COM_HANDSHAKE)
        if self.arcom.read_uint8() != 217:
            raise Exception('Could not connect =( ')

    def close(self):
        """
        Closes the serial connection to the Rotary Encoder board.
        """
        self.arcom.close()

    def __pos_2_degrees(self, pos) -> float:
        # todo: what is the rationale for limiting the precision here?
        return round(pos / 512.0 * 180.0, 1)

    def __degrees_2_pos(self, degrees) -> int:
        return round(degrees / 180.0 * 512.0)

    def enable_evt_transmission(self):
        """
        Enables the transmission of threshold crossing events to the Bpod state machine.
        """
        self.arcom.write_array([self.COM_TOGGLEEVTTRANSM, 1])
        return self.arcom.read_uint8() == 1

    def disable_evt_transmission(self):
        """
        Disables the transmission of events.
        """
        self.arcom.write_array([self.COM_TOGGLEEVTTRANSM, 0])
        return self.arcom.read_uint8() == 1

    def enable_module_outputstream(self):
        """
        Enables the streaming of current position data directly to another Bpod module (e.g. DDS, AnalogOutput).
        """
        self.arcom.write_array([self.COM_TOGGLEOUTPUTSTREAM, 1])
        return self.arcom.read_uint8() == 1

    def disable_module_outputstream(self):
        """
        Disables the streaming of current position data directly to another Bpod module.
        """
        self.arcom.write_array([self.COM_TOGGLEOUTPUTSTREAM, 0])
        return self.arcom.read_uint8() == 1

    def enable_stream(self):
        """
        Enables the streaming of the position and the time measurements to the USB port.
        """
        self.arcom.write_array([self.COM_TOGGLESTREAM, 1])

    def disable_stream(self):
        """
        Disables the streaming of the position and the time measurements to the USB port.
        """
        self.arcom.write_array([self.COM_TOGGLESTREAM, 0])

    def read_stream(self):
        """
        Reads the data being streamed through the USB port.
        """
        res = []
        available = self.arcom.bytes_available()
        data = self.arcom.serial_object.read(available)
        i = 0
        while i + 7 <= len(data):
            if data[i] == ord('P'):
                position, evt_time = struct.unpack_from('<xhI', data, i)
                evt_time /= 1000.0
                position_degrees = self.__pos_2_degrees(position)
                res.append(['P', evt_time, position_degrees])
            elif data[i] == ord('E'):
                origin, event, evt_time = struct.unpack_from('<xccI', data, i)
                evt_time /= 1000.0
                res.append(['E', evt_time, origin, event])
            i += 7

        return res

    def current_position(self):
        """
        Retrieves the current position.
        """
        self.arcom.write_array([self.COM_GETCURRENTPOS])
        ticks = self.arcom.read_int16()
        return self.__pos_2_degrees(ticks)

    def set_zero_position(self):
        """
        Sets current rotary encoder position to zero.
        """
        self.arcom.write_array([self.COM_SETZEROPOS])

    def set_position(self, degrees):
        """
        Sets the current position in degrees.

        :ivar int degrees: current position in degrees.
        """
        ticks = self.__degrees_2_pos(degrees)
        data = ArduinoTypes.get_uint8_array([self.COM_SETPOS])
        data += ticks.to_bytes(2, byteorder='little', signed=True)

        self.arcom.write_array(data)
        return self.arcom.read_uint8() == 1

    def enable_thresholds(self, thresholds):
        """
        Enables the thresholds.

        :ivar list(boolean) thresholds: list of 6 booleans indicating which thresholds are active to trigger events.
        """
        if len(thresholds) != 8:
            raise Exception('Thresholds array has to be of length 8')

        bits = sum(bit << (7 - i) for i, bit in enumerate(thresholds))
        self.arcom.write_array([self.COM_ENABLETHRESHOLDS, bits])

    def enable_logging(self):
        """
        Enables the logging to the SD Card.
        """
        self.arcom.write_array([self.COM_STARTLOGGING])

    def disable_logging(self):
        """
        Disables the logging to the SD Card.
        """
        self.arcom.write_array([self.COM_STOPLOGGING])

    def get_logged_data(self):
        """
        Retrieves the logged data in the SD Card.
        """
        self.arcom.write_array([self.COM_GETLOGDATA])
        msg = self.arcom.read_bytes_array(4)
        n_logs = int.from_bytes(b''.join(msg), byteorder='little', signed=False)
        data = self.arcom.serial_object.read(n_logs * 8)
        return [(evt_time / 1000.0, self.__pos_2_degrees(pos)) for pos, evt_time in struct.iter_unpack('<iI', data)]

    def set_prefix(self, prefix) -> bool:
        """
        Sets 1-character prefix for module output stream.

        :ivar char prefix: One character to be used as prefix.
        """
        self.arcom.write_array([self.COM_SETPREFIX, prefix])
        return self.arcom.read_uint8() == 1

    def set_thresholds(self, thresholds) -> bool:
        """
        Sets the thresholds values to trigger the events.

        :ivar list(int) thresholds: List, in maximum, of 6 thresholds to trigger events.
        """
        data = ArduinoTypes.get_uint8_array([self.COM_SETTHRESHOLDS, len(thresholds)])
        data += ArduinoTypes.get_uint16_array([self.__degrees_2_pos(thresh) for thresh in thresholds])
        self.arcom.write_array(data)
        return self.arcom.read_uint8() == 1

    def set_wrappoint(self, wrap_point) -> bool:
        """
        Sets wrap point (number of tics in a half-rotation)

        :ivar int wrap_point: number of tics in a half-rotation.
        """
        ticks = self.__degrees_2_pos(wrap_point)
        self.arcom.write_array([self.COM_SETWRAPPOINT] + ArduinoTypes.get_uint16_array([ticks]))
        return self.arcom.read_uint8() == 1


if __name__ == '__main__':
    import time

    m = RotaryEncoderModule('/dev/ttyACM0')

    m.enable_logging()
    time.sleep(5)
    m.disable_logging()

    print(m.get_logged_data())

    """
    m.enable_stream()



    count = 0
    while count<100 or True:
        data = m.read_stream()
        if len(data)==0: continue

        print(data)
        count += 1

    m.disable_stream()

    print('set', m.set_position(179))
    m.set_zero_position()

    m.enable_thresholds([True, False, True, True, False, False, True, True])
    print(m.current_position())
    print(m.get_logged_data())
    """
    m.close()
