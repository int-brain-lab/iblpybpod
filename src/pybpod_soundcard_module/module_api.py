import array
import math
import time
import traceback

import numpy as np
from enum import Enum, IntEnum
from aenum import auto
import os
import collections
import usb.core
import usb.util
from usb.backend import libusb1 as libusb

class SampleRate(IntEnum):
    """
    Enumeration for the Sample rate of the sounds in the Sound Card
    """

    #: 96KHz sample rate
    _96000HZ = 96000
    #: 192KHz sample rate
    _192000HZ = 192000


class DataType(IntEnum):
    """
    Type of the data to be send to the Sound Card
    """

    #: Integer 32 bits
    INT32 = 0,

    #: Single precision float
    FLOAT32 = 1


class SoundCardErrorCode(Enum):
    OK = 0,
    BAD_USER_INPUT = -1,

    HARP_SOUND_CARD_NOT_DETECTED = -1000,
    NOT_ABLE_TO_SEND_METADATA = auto(),
    NOT_ABLE_TO_READ_METADATA_COMMAND_REPLY = auto(),
    METADATA_COMMAND_REPLY_NOT_CORRECT = auto(),
    NOT_ABLE_TO_SEND_DATA = auto(),
    NOT_ABLE_TO_READ_DATA_COMMAND_REPLY = auto(),
    DATA_COMMAND_REPLY_NOT_CORRECT = auto(),
    NOT_ABLE_TO_SEND_READ_METADATA = auto(),
    NOT_ABLE_TO_READ_READ_METADATA_COMMAND_REPLY = auto(),
    READ_METADATA_COMMAND_REPLY_NOT_CORRECT = auto(),

    BAD_SOUND_INDEX = -1020,
    BAD_SOUND_LENGTH = auto(),
    BAD_SAMPLE_RATE = auto(),
    BAD_DATA_TYPE = auto(),
    DATA_TYPE_DO_NOT_MATCH = auto(),
    BAD_DATA_INDEX = auto(),

    PRODUCING_SOUND = -1030,
    STARTED_PRODUCING_SOUND = auto(),

    NOT_ABLE_TO_OPEN_FILE = -1040


class SoundMetadata(object):

    def __init__(self, sound_index, sound_length, sample_rate, data_type):
        """

        :param self:
        :param sound_index: Sound index in the soundcard (2 -> 31 since 0 and 1 are reserved)
        :param sound_length: Sound length in number of samples
        :param sample_rate: Sample rate
        :param data_type: 0 for Int32 and 1 for Float32 (not available right now)
        """
        self._sound_index = sound_index
        self._sound_length = sound_length
        self._sample_rate = sample_rate
        self._data_type = data_type

    def check_data(self):
        if self._sound_index < 2 or self._sound_index > 32:
            return SoundCardErrorCode.BAD_SOUND_INDEX

        if self._sound_length < 16:
            return SoundCardErrorCode.BAD_SOUND_LENGTH

        if self._sample_rate is not SampleRate._96000HZ and self._sample_rate is not SampleRate._192000HZ:
            return SoundCardErrorCode.BAD_SAMPLE_RATE

        if self._data_type is not DataType.INT32 and self._data_type is not DataType.FLOAT32:
            return SoundCardErrorCode.BAD_DATA_TYPE

        if self._sound_index == 0 and self._data_type is not DataType.FLOAT32:
            return SoundCardErrorCode.DATA_TYPE_DO_NOT_MATCH

        if self._sound_index == 1 and self._data_type is not DataType.FLOAT32:
            return SoundCardErrorCode.DATA_TYPE_DO_NOT_MATCH

        if self._sound_index > 1 and self._data_type is not DataType.INT32:
            return SoundCardErrorCode.DATA_TYPE_DO_NOT_MATCH

        return SoundCardErrorCode.OK

    def as_array(self):
        return np.array([self._sound_index, self._sound_length, self._sample_rate, self._data_type], dtype=np.int32)


class SoundCardModule(object):
    """
    Provides access to the Harp Sound Card. It allows to send and read the sounds in the Sound Card, through a normal
    USB connection.
    """

    def __init__(self, device=None):
        """
        If a libUSB's device is given, it will try to open it. If none is given it will try to connect to the first Sound Card that is connected to the computer.

        :param device: (Optional) libUSB device to use. If nothing is passed, it will try to connect automatically.
        """
        self._backend = libusb.get_backend()
        try:
            self._devices = list(usb.core.find(backend=self._backend, idVendor=0x04d8, idProduct=0xee6a, find_all=True))
        except OSError as e:
            pass
        
        self._dev = self._devices[0] if self._devices else None
        self._cfg = None
        self._port = None
        self._connected = False

        self.open(self._dev if device is None else device)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def open(self, device=None):
        """
        Opens the connection to the Sound Card. If no device is given, it will try to connect to the first Sound Card that is connected to the computer.

        :param device: (Optional) Already initialized libUSB's device to use.
        """
        if device is None:
            self._backend = libusb.get_backend()
            try:
                self._dev = usb.core.find(backend=self._backend, idVendor=0x04d8, idProduct=0xee6a)
            except OSError as e:
                self._dev = None
                pass
        else:
            self._dev = device

        if self._dev is None:
            print(
                "Unable to connect to the Sound Card through the USB port. You will be unable to send and receive sounds.")
        else:
            # set the active configuration. With no arguments, the first configuration will be the active one
            # note: some devices reset when setting an already selected configuration so we should check for it before
            self._cfg = self._dev.get_active_configuration()
            if self._cfg is None or self._cfg.bConfigurationValue != 1:
                self._dev.set_configuration(1)

        self._connected = True if self._dev else False

    @property
    def devices(self):
        return self._devices

    @property
    def connected(self):
        return self._connected

    def close(self):
        """
        Closes the connection with the Sound Card. It will close USB connection (to read and save sounds)
        """
        if self._dev:
            usb.util.dispose_resources(self._dev)

    def reset(self):
        """
        Resets the device, waits 700ms and tries to connect again so that the current instance of the SoundCard object can still be used.

        .. note:: Necessary at the moment after sending a sound.
        """
        if not self._dev:
            raise Exception("Sound card might not be connected. Please connect it before any operation.")

        # Reset command length:    'c' 'm' 'd' '0x88' + 'f'
        reset_cmd = [ord('c'), ord('m'), ord('d'), 0x88, ord('f')]
        # cmd = 'cmd' + chr(0x88) + 'f'
        wrt = self._dev.write(1, reset_cmd, 100)
        assert wrt == len(reset_cmd)

        time.sleep(700.0 / 1000.0)
        self.open()

    def read_sounds(self, output_folder=None, sound_index=None, clean_dst_folder=True):
        """
        Reads sounds from the sound card.

        .. note:: by default, it will clear the destination folder of all data. It will also write by default to a
                  "from_soundcard" folder in the working directory if none is given.

        :param output_folder: Destination folder's path.
        :param sound_index: If a sound_index is given, it will get only that sound, if nothing is passed it will gather all sounds from all indexes.
        :param clean_dst_folder: Flag that defines if the method should clean the destination folder or not

        """
        if not self._dev:
            raise Exception("Sound card might not be connected. Please connect it before any operation.")

        # admit that if the output_folder is None, write inside a 'from_soundcard' folder in the current directory
        if not output_folder:
            output_folder = os.path.join(os.getcwd(), 'from_soundcard')
            if not os.path.isdir(output_folder):
                os.makedirs(output_folder)
        else:
            # create folder if it doesn't exists
            if not os.path.exists(output_folder):
                os.makedirs(output_folder)

            if clean_dst_folder:
                for file in os.listdir(output_folder):
                    file_path = os.path.join(output_folder, file)
                    try:
                        if os.path.isfile(file_path):
                            os.unlink(file_path)
                    except Exception as e:
                        # probably a permissions error while deleting, ignore and try the next one
                        print("Error occurred when deleting file '{file_path}'. Ignoring error and continuing.".format(file_path=file_path))
                        continue

        if sound_index is None:
            for i in range(2, 32):
                self._from_soundcard(output_folder, i)
        else:
            self._from_soundcard(output_folder, sound_index)

        print("All files read!")

    def send_sound(self, wave_int, sound_index, sample_rate, data_type, 
                   sound_filename=None, metadata_filename=None, 
                   description_filename=None):
        """
            This method will send the sound to the Harp Sound Card as a byte array (int8)

            :param wave_int: NumPy array as int32 that represents the sound data
            :param sound_index:  The destination index in the Sound Card (>=2 and <= 32)
            :param sample_rate: The SampleRate enum value for either 96KHz or 192KHz
            :param data_type: The DataType enum value for either Int32 or Float32 (not implemented yet in the hardware)
            :param sound_filename: The name of the sound filename to be saved with the sound in the board (str)
            :param metadata_filename: The name of the metadata filename to be saved with the sound in the board (str)
            :param description_filename: The name of the description filename to be saved with the sound in the board (str)
        """
        self._to_soundcard(wave_int, sound_index, sample_rate, data_type, sound_filename, metadata_filename,
                          description_filename)

    def _from_soundcard(self, output_folder=None, sound_index=None):
        """
        Reads sounds from the sound card.

        :param output_folder: Destination folder's path.
        :param sound_index: If a sound_index is given, it will get only that sound, if nothing is passed it will gather all sounds from all indexes.

        """
        if not self._dev:
            raise Exception("Sound card might not be connected. Please connect it before any operation.")

        if sound_index is None or sound_index < 2 or sound_index > 31:
            raise Exception("sound_index must have a value between 2 and 31")

        metadata = self.__get_metadata_from_device(sound_index)

        if metadata is None:
            raise Exception('SoundCardModule: Error while getting metadata from device')

        # define prefix
        prefix = 'i'
        if sound_index < 9:
            prefix += '0' + str(sound_index) + '_'
        else:
            prefix += str(sound_index) + '_'

        sound_filename = metadata.sound_filename.decode('utf-8')
        metadata_filename = metadata.metadata_filename.decode('utf-8') if metadata.metadata_filename else None
        description_filename = metadata.description_filename.decode(
            'utf-8') if metadata.description_filename else None

        if prefix not in sound_filename:
            sound_filename = prefix + sound_filename
        if metadata_filename and prefix not in metadata_filename:
            metadata_filename = prefix + metadata_filename
        if description_filename and prefix not in description_filename:
            description_filename = prefix + description_filename

        if metadata.has_sound:
            with open(os.path.join(output_folder, sound_filename), 'w', encoding='utf8') as f:
                # TODO: read the sound so we can write it here
                f.write('TODO')

        if metadata.has_metadata:
            with open(os.path.join(output_folder, metadata_filename), 'wb') as f:
                # clean the zeros at the end
                f.write(metadata.metadata_array.tobytes().strip(b'\0'))

        if metadata.has_description:
            with open(os.path.join(output_folder, description_filename), 'wb') as f:
                f.write(metadata.description.tobytes().strip(b'\0'))

        # create summary info file
        if metadata.has_sound:
            with open(os.path.join(output_folder, sound_filename + '.metadata.txt'), 'w') as f:
                f.write('SOUND_INDEX = ' + str(sound_index))

                used_pos = math.ceil(metadata.sound_length / (33554432.0 * 2.0 / 32.0)) - 1
                if used_pos > 0:
                    f.write(", ")
                f.write(", ".join(str(sound_index + idx + 1) for idx in range(used_pos)))

                f.write("\n")

                f.write("TOTAL_SAMPLES = " + str(metadata.sound_length) + "\n")
                f.write(
                    "TOTAL_LENGTH_MS = " + str(int(metadata.sound_length / 2 / metadata.sample_rate * 1000)) + "\n")
                f.write("SAMPLE_RATE = " + str(metadata.sample_rate) + "\n")

                if metadata.data_type == 0:
                    f.write("DATA_TYPE = Int32\n")
                else:
                    f.write("DATA_TYPE = Float32\n")

                f.write("SOUND_FILENAME = " + sound_filename + "\n")

                if metadata.has_metadata:
                    f.write("USER_METADATA_FILENAME = " + metadata_filename + "\n")
                if metadata.has_description:
                    f.write("USER_DESCRIPTION_FILENAME = " + description_filename + "\n")

    def _to_soundcard(self, wave_int, sound_index, sample_rate, data_type,
                      sound_filename=None, metadata_filename=None, 
                      description_filename=None):
        """
            This method will send the sound to the Harp Sound Card as a byte array (int8)

            :param wave_int: NumPy array as int32 that represents the sound data
            :param sound_index:  The destination index in the Sound Card (>=2 and <= 32)
            :param sample_rate: The SampleRate enum value for either 96KHz or 192KHz
            :param data_type: The DataType enum value for either Int32 or Float32 (not implemented yet in the hardware)
            :param sound_filename: The name of the sound filename to be saved with the sound in the board (str)
            :param metadata_filename: The name of the metadata filename to be saved with the sound in the board (str)
            :param description_filename: The name of the description filename to be saved with the sound in the board (str)
        """
        # confirm that the dev exists and is ready
        if not self._dev:
            raise EnvironmentError(
                'Sound card not initialized. Please call the initialize method before any operation.')

        int32_size = np.dtype(np.int32).itemsize
        # work with a int8 view of the wave_int (which is int32)
        wave_int8 = wave_int.view(np.int8)

        # get number of commands to send
        sound_file_size_in_samples = len(wave_int8) // 4
        commands_to_send = int(sound_file_size_in_samples * 4 // 32768 + (
            1 if ((sound_file_size_in_samples * 4) % 32768) != 0 else 0))

        # Metadata command length: 'c' 'm' 'd' '0x80' + random + metadata  + 32768 + 2048 + 'f'
        metadata_cmd_header_size = 4 + int32_size + (4 * int32_size)
        metadata_cmd = np.zeros(metadata_cmd_header_size + 32768 + 2048 + 1, dtype=np.int8)

        metadata_cmd[0] = ord('c')
        metadata_cmd[1] = ord('m')
        metadata_cmd[2] = ord('d')
        metadata_cmd[3] = 0x80
        metadata_cmd[-1] = ord('f')

        rand_val = np.random.randint(-32768, 32768, size=1, dtype=np.int32)
        # copy that random data
        metadata_cmd[4: 4 + int32_size] = rand_val.view(np.int8)

        # create metadata info and add it to the metadata_cmd
        metadata = SoundMetadata(sound_index, sound_file_size_in_samples, sample_rate, data_type)
        if metadata.check_data() is not SoundCardErrorCode.OK:
            print("Input data incorrect, please correct it before proceeding.")
            return

        metadata_cmd[8: 8 + (4 * int32_size)] = metadata.as_array().view(np.int8)

        # add first data block of data to the metadata_cmd
        metadata_cmd_data_index = metadata_cmd_header_size
        metadata_cmd[metadata_cmd_data_index: metadata_cmd_data_index + 32768] = wave_int8[0: 32768]

        # prepare user_metadata
        # [0:169]     sound_filename
        # [170:339]   metadata_filename
        # [340:511]   description_filename
        # [512:1535]  metadata_filename content
        # [1536:2047] description_filename content
        user_metadata = np.zeros(2048, dtype=np.int8)
        user_metadata_index = metadata_cmd_data_index + 32768

        if sound_filename:
            tmp = bytearray()
            tmp.extend(map(ord, os.path.basename(sound_filename)))
            tmp_size = len(tmp) if len(tmp) < 169 else 169
            user_metadata[0:tmp_size] = tmp[0:tmp_size]

        if metadata_filename:
            tmp = bytearray()
            tmp.extend(map(ord, os.path.basename(metadata_filename)))
            tmp_size = len(tmp) if len(tmp) < 169 else 169
            user_metadata[170: 170 + tmp_size] = tmp[0:tmp_size]

            # get file contents, truncate data if required
            try:
                with open(metadata_filename, 'r', encoding='utf8') as f:
                    text = f.read()
                    text_tmp = bytearray()
                    text_tmp.extend(map(ord, text))
                    data_tmp = np.array(text_tmp)
                    data = data_tmp.view(np.int8)
                    data_size = len(data) if len(data) < 1023 else 1023
                    user_metadata[512: 512 + data_size] = data[0: data_size]
            except OSError as e:
                # TODO: should be a stronger error
                print("Error opening metadata file.")

        if description_filename:
            tmp = bytearray()
            tmp.extend(map(ord, os.path.basename(description_filename)))
            tmp_size = len(tmp) if len(tmp) < 169 else 169
            user_metadata[340: 340 + tmp_size] = tmp[0: tmp_size]

            # get file contents, truncate data if required
            try:
                with open(description_filename, 'r', encoding='utf8') as f:
                    text = f.read()
                    text_tmp = bytearray()
                    text_tmp.extend(map(ord, text))
                    data_tmp = np.array(text_tmp)
                    data = data_tmp.view(np.int8)
                    data_size = len(data) if len(data) < 511 else 511
                    user_metadata[1536: 1536 + data_size] = data[0: data_size]
            except OSError as e:
                print(e)
                # TODO: should be a stronger error
                print("Error opening description file.")

        # add user metadata (2048 bytes) to metadata_cmd
        metadata_cmd[user_metadata_index: user_metadata_index + 2048] = user_metadata

        # Metadata command reply: 'c' 'm' 'd' '0x80' + random + error
        metadata_cmd_reply = array.array('b', [0] * (4 + int32_size + int32_size))

        # send metadata_cmd and get it's reply
        try:
            res_write = self._dev.write(0x01, metadata_cmd.tobytes(), 100)
        except usb.core.USBError as e:
            # TODO: we probably should try again
            print("something went wrong while writing to the device")
            return

        assert res_write == len(metadata_cmd)

        try:
            ret = self._dev.read(0x81, metadata_cmd_reply, 1000)
        except usb.core.USBError as e:
            # TODO: we probably should try again
            traceback.print_exc()
            print("something went wrong while reading from the device")
            return

        # get the random received and the error received from the reply command
        rand_val_received = int.from_bytes(metadata_cmd_reply[4: 4 + int32_size], byteorder='little', signed=True)
        error_received = int.from_bytes(metadata_cmd_reply[8: 8 + int32_size], byteorder='little', signed=False)

        assert rand_val_received == rand_val[0]
        assert error_received == 0

        # prepare command to send and to receive
        # Data command length:     'c' 'm' 'd' '0x81' + random + dataIndex + 32768 + 'f'
        data_cmd = np.zeros(4 + int32_size + int32_size + 32768 + 1, dtype=np.int8)
        data_cmd_data_index = 4 + int32_size + int32_size

        data_cmd[0] = ord('c')
        data_cmd[1] = ord('m')
        data_cmd[2] = ord('d')
        data_cmd[3] = 0x81
        data_cmd[-1] = ord('f')

        # Data command reply:     'c' 'm' 'd' '0x81' + random + error
        data_cmd_reply = array.array('b', [0] * (4 + int32_size + int32_size))

        # loop to send the rest of the commands
        # check reply for each command sent
        for i in range(1, commands_to_send):
            # it has to be as an np.array of int32 so that we can get a view as int8s
            rand_val = np.random.randint(-32768, 32768, size=1, dtype=np.int32)
            # copy that random data
            data_cmd[4: 4 + int32_size] = rand_val.view(np.int8)

            # write dataIndex to the data_cmd (2 ints size)
            data_cmd[8: 8 + int32_size] = np.array([i], dtype=np.int32).view(np.int8)

            # write data from wave_int to cmd
            wave_idx = i * 32768
            data_block = wave_int8[wave_idx: wave_idx + 32768]
            data_cmd[data_cmd_data_index: data_cmd_data_index + len(data_block)] = data_block

            # send data to device
            try:
                res_write = self._dev.write(0x01, data_cmd.tobytes(), 100)
            except usb.core.USBError as e:
                # TODO: we probably should try again
                print("something went wrong while writing to the device")
                return

            # TODO: we probably should try again
            assert res_write == len(data_cmd)

            try:
                ret = self._dev.read(0x81, data_cmd_reply, 400)
            except usb.core.USBError as e:
                # TODO: we probably should try again
                traceback.print_exc()
                print("something went wrong while reading from the device")
                return

            # get the random received and the error received from the reply command
            rand_val_received = int.from_bytes(data_cmd_reply[4: 4 + int32_size], byteorder='little', signed=True)
            error_received = int.from_bytes(data_cmd_reply[8: 8 + int32_size], byteorder='little', signed=False)

            assert rand_val_received == rand_val[0]
            assert error_received == 0

    def __get_metadata_from_device(self, sound_index):
        int32_size = np.dtype(np.int32).itemsize

        # Read metadata command length: 'c' 'm' 'd' '0x84' + random + soundIndex + 'f'
        read_metadata_cmd = np.zeros(4 + int32_size + int32_size + 1, dtype=np.int8)
        read_metadata_cmd[0] = ord('c')
        read_metadata_cmd[1] = ord('m')
        read_metadata_cmd[2] = ord('d')
        read_metadata_cmd[3] = 0x84
        read_metadata_cmd[-1] = ord('f')

        rand_val = np.random.randint(-32768, 32768, size=1, dtype=np.int32)
        # copy that random data
        read_metadata_cmd[4: 4 + int32_size] = rand_val.view(np.int8)
        read_metadata_cmd[8: 8 + int32_size] = np.array([sound_index], dtype=np.int32).view(np.int8)

        # prepare to send command and receive the reply
        read_reply_cmd = array.array('b', [0] * (4 + 6 * int32_size + 2048))

        try:
            res_write = self._dev.write(0x01, read_metadata_cmd.tobytes(), 100)
        except usb.core.USBError as e:
            # TODO: we probably should try again
            print("something went wrong while writing to the device")
            return

        assert res_write == len(read_metadata_cmd)

        try:
            ret = self._dev.read(0x81, read_reply_cmd, 100)
        except usb.core.USBError as e:
            # TODO: we probably should try again
            traceback.print_exc()
            print("something went wrong while reading from the device")
            return

        metadata = collections.namedtuple('Metadata',
                                          ['metadata_array', 'description', 'bit_mask', 'sound_length', 'data_type',
                                           'sample_rate', 'sound_filename', 'metadata_filename',
                                           'description_filename',
                                           'has_sound', 'has_metadata', 'has_description'])

        # get data from the reply array
        metadata.metadata_array = array.array('b', [0] * 1024)
        metadata.description = array.array('b', [0] * 512)

        # get the random received and the error received from the reply command
        rand_val_received = int.from_bytes(read_reply_cmd[4: 4 + int32_size], byteorder='little', signed=True)
        error_received = int.from_bytes(read_reply_cmd[8: 8 + int32_size], byteorder='little', signed=False)

        assert rand_val_received == rand_val[0]
        assert error_received == 0

        # bitmask
        metadata.bit_mask = int.from_bytes(read_reply_cmd[12:12 + int32_size + int32_size], byteorder='little',
                                           signed=True)

        metadata.has_sound = metadata.bit_mask & (1 << sound_index) == (1 << sound_index)

        metadata.sound_length = int.from_bytes(read_reply_cmd[16:16 + int32_size], byteorder='little', signed=True)
        metadata.sample_rate = int.from_bytes(read_reply_cmd[20:20 + int32_size], byteorder='little', signed=True)
        metadata.data_type = int.from_bytes(read_reply_cmd[24:24 + int32_size], byteorder='little', signed=True)

        metadata.sound_filename = read_reply_cmd[28:170].tobytes().strip(b'\0')

        metadata.has_metadata = False
        metadata.metadata_filename = ''
        if read_reply_cmd[28 + 170]:
            metadata.has_metadata = True
            metadata.metadata_array[0:1024] = read_reply_cmd[28 + 512:28 + 512 + 1024]
            metadata.metadata_filename = read_reply_cmd[28 + 170: 28 + 170 + 170].tobytes().strip(b'\0')

        metadata.has_description = False
        metadata.description_filename = ''
        if read_reply_cmd[28 + 170 + 170]:
            metadata.has_description = True
            metadata.description[0:512] = read_reply_cmd[28 + 512 + 1024:28 + 512 + 1024 + 512]
            metadata.description_filename = read_reply_cmd[28 + 170 + 170: 28 + 170 + 170 + 170].tobytes().strip(b'\0')

        return metadata

