# Copyright (c) 2014 Matthias Geier
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

"""Schunk Motion Protocol for Python 3.

Documentation:
  http://schunk.rtfd.org/

Code:
  http://github.com/spatialaudio/schunk/

Schunk Motion Protocol manual:
  http://www.schunk.com/schunk_files/attachments/MotionControl_en_2010-03.pdf

Example
-------

::

    import schunk
    import serial

    mod = schunk.Module(schunk.RS232Connection(
        0x0B, serial.Serial, port=0, baudrate=9600, timeout=1))

    mod.move_pos(42)

"""

import struct


# TODO: custom exception SchunkError?
# TODO: document exceptions in docstrings


class Module:

    """A Schunk module.

    For further documentation see the __init__() docstring (which is
    also used in the Sphinx documentation (http://schunk.rtfd.org/).

    """

    def __init__(self, connection):
        """Create an object for controlling a Schunk module.

        Parameters
        ----------
        connection
            Something that has a ``send()`` method. This method must
            accept bytes, send them to a Schunk module, read the
            response (taking D-Len into account) and return the response
            as a bytes object.

            :class:`RS232Connection` happens to do exactly that.

        """
        self._connection = connection

    def reference(self):
        """2.1.1 CMD REFERENCE (0x92).

        A reference movement is completed.

        """
        self._send(0x92, expected=b'OK')

    def move_pos(self, position, velocity=None, acceleration=None,
                 current=None, jerk=None):
        """2.1.3 MOVE POS (0xB0).

        Parameters
        ----------
        position : float
            Absolute position.
        velocity, acceleration, current, jerk : float, optional
            If one of them is not specified, all following arguments
            must not be specified either.

        Returns
        -------
        float
            Estimated time to reach `position`.
            If the time cannot be estimated, 0.0 is returned.

        See Also
        --------
        move_pos_rel
        set_target_vel, set_target_acc, set_target_cur, set_target_jerk

        """
        return self._move_pos_helper(0xB0, position, velocity,
                                     acceleration, current, jerk)

    def move_pos_rel(self, position, velocity=None, acceleration=None,
                     current=None, jerk=None):
        """2.1.4 MOVE POS REL (0xB8).

        Parameters
        ----------
        position : float
            Relative position.
        velocity, acceleration, current, jerk : float, optional
            If one of them is not specified, the following must not be
            specified either.

        Returns
        -------
        float
            Estimated time to reach `position`.
            If the time cannot be estimated, 0.0 is returned.

        See Also
        --------
        move_pos
        set_target_vel, set_target_acc, set_target_cur, set_target_jerk

        """
        return self._move_pos_helper(0xB8, position, velocity,
                                     acceleration, current, jerk)

    def move_pos_time(self, position, velocity=None, acceleration=None,
                      current=None, time=None):
        """2.1.5 MOVE POS TIME (0xB1).

        See Also
        --------
        set_target_time

        """
        return self._move_pos_helper(0xB1, position, velocity,
                                     acceleration, current, time)

    def move_pos_time_rel(self, position, velocity=None, acceleration=None,
                          current=None, time=None):
        """2.1.6 MOVE POS TIME REL (0xB9).

        See Also
        --------
        set_target_time

        """
        return self._move_pos_helper(0xB9, position, velocity,
                                     acceleration, current, time)

    def set_target_vel(self, velocity):
        """2.1.14 SET TARGET VEL (0xA0).

        Initially, the target velocity is set to 10% of the maximum.

	"""
        self._send(0xA0, struct.pack('<f', velocity), b'OK')

    def set_target_acc(self, acceleration):
        """2.1.15 SET TARGET VEL (0xA1).

        Initially, the target acceleration is set to 10% of the maximum.

        """
        self._send(0xA1, struct.pack('<f', acceleration), b'OK')

    def set_target_jerk(self, jerk):
        """2.1.16 SET TARGET JERK (0xA2).

        Initially, the target jerk is set to 50% of the maximum.

        """
        self._send(0xA2, struct.pack('<f', jerk), b'OK')

    def set_target_cur(self, current):
        """2.1.17 SET TARGET CUR (0xA3).

        Initially, the target current is set to the nominal current.

        """
        self._send(0xA3, struct.pack('<f', current), b'OK')

    def set_target_time(self, time):
        """2.1.18 SET TARGET TIME (0xA4)."""
        self._send(0xA4, struct.pack('<f', time), b'OK')

    def stop(self):
        """2.1.19 CMD STOP (0x91)."""
        self._send(0x91, expected=b'OK')

    # Not implemented (see warnings in Schunk manual):
    # 2.1.20 CMD EMERGENCY STOP (0x90)

    def toggle_impulse_message(self):
        """2.2.6 CMD TOGGLE IMPULSE MESSAGE (0xE7)."""
        response = self._send(0xE7)
        if response == b'ON':
            return True
        elif response == b'OFF':
            return False
        else:
            raise RuntimeError("Unexpected response: {}".format(response))

    def get_config(self, param=None):
        """2.3.2 GET CONFIG (0x80).

        """
        def sub_command(cmd, format_string):
            byte1, the_rest = self._send(0x80, cmd, '<s' + format_string)
            if byte1 != cmd:
                raise RuntimeError("Unexpected subcommand: {}".format(byte1))
            return the_rest

        one_byte = {
            'module_id': b'\x01',
            'group_id': b'\x02',
        }
        two_bytes = {
            'rs232_baudrate': b'\x03',
            'can_baudrate': b'\x04',
            'offset_phase_a': b'\x0E',
            'offset_phase_b': b'\x0F',
            'data_crc': b'\x13',
        }
        four_bytes_float = {
            'soft_high': b'\x07',
            'soft_low': b'\x08',
            'max_velocity': b'\x09',
            'max_acceleration': b'\x0A',
            'max_current': b'\x0B',
            'nom_current': b'\x0C',
            'max_jerk': b'\x0D',
            'reference_offset': b'\x14',
        }
        four_bytes_int = {
            'serial_number': b'\x15',
            'order_number': b'\x16',
        }

        if param is None:
            names = ('module_type', 'order_number', 'firmware_version',
                     'protocol_version', 'hardware_version', 'firmware_date')
            # Note: the Schunk manual states that the date string has 21 bytes,
            # the PR-70 modules returns 5 more bytes, however:
            config = self._send(0x80, expected='<8sIHHH26s')
            return {name: value.decode() if isinstance(value, bytes) else value
                    for name, value in zip(names, config)}
        elif param in one_byte:
            return sub_command(one_byte[param], 'B')
        elif param in two_bytes:
            return sub_command(two_bytes[param], 'H')
        elif param in four_bytes_float:
            return sub_command(four_bytes_float[param], 'f')
        elif param in four_bytes_int:
            return sub_command(four_bytes_int[param], 'I')
        elif param == 'communication_mode':
            return {
                0x00: 'AUTO',
                0x01: 'RS232',
                0x02: 'CAN',
                0x03: 'Profibus DPV0',
                0x04: 'RS232 Silent',
            }.get(sub_command(b'\x05', 'B'), 'unknown')
        elif param == 'unit_system':
            return {
                0x00: '[mm]',
                0x01: '[m]',
                0x02: '[Inch]',
                0x03: '[rad]',
                0x04: '[Degree]',
                0x05: '[Intern]',
                0x06: '[μm] Integer',
                0x07: '[μDegree] Integer',
                0x08: '[μInch] Integer',
                0x09: '[Milli − degree] Integer',
            }.get(sub_command(b'\x06', 'B'), 'unknown')
        elif param == 'eeprom':
            result = self._send(0x80, b'\xFE')
            cmd = result[0]
            if cmd != 0xFE:
                raise RuntimeError("Unexpected subcommand: {}".format(cmd))
            return result[1:]
        else:
            raise RuntimeError("Invalid sub-command: {}".format(param))

    def get_state(self):
        """2.5.1 GET STATE (0x95).

        Return the module status and other information.

        The time parameter (to get state repeatedly) is disabled
        (because impulse messages are not supported).
        The mode parameter is always set to request everything
        (position, velocity and current).

        Returns
        -------
        position, velocity, current : float
            Dito.
        status : dict
            Use :func:`decode_status` with ``status=0`` to see all
            status keys.
        error_code : int
            Use :func:`decode_error` to get a string representation.

        """
        data = struct.pack('<fB', 0.0, 0x01 | 0x02 | 0x04)
        pos, vel, cur, status, error = self._send(0x95, data, '<3fBB')
        return pos, vel, cur, decode_status(status), error

    def reboot(self):
        """2.5.2 CMD REBOOT (0xE0)."""
        self._send(0xE0, expected=b'OK')

    def ack(self):
        """2.8.1.4 CMD ACK (0x8B).

        Acknowledgement of a pending error message.

        """
        self._send(0x8B, expected=b'OK')

    def check_mc_pc_communication(self):
        """2.5.7 CHECK MC PC COMMUNICATION (0xE4).

        Returns
        -------
        bool
            ``True`` on success.

        """
        returned = self._send(0xE4, expected=_test_format_string)
        for ret, val in zip(returned, _test_values):
            if abs(ret - val) > 0.000001:
                raise RuntimeError("Wrong result for {}: {}".format(val, ret))
        return True

    def check_pc_mc_communication(self):
        """2.5.8 CHECK PC MC COMMUNICATION (0xE5).

        Returns
        -------
        bool
            ``True`` on success.

        """
        data = struct.pack(_test_format_string, *_test_values)
        self._send(0xE5, data, b'OK\x00')
        return True

    def get_detailed_error_info(self):
        """2.8.1.5 GET DETAILED ERROR INFO (0x96).

        .. note:: If no error is active, or no detailed information is
                  available, the command is replied with an
                  "INFO FAILED" exception.

        Returns
        -------
        bytes
            Command (1 byte), error code (1 byte), data (float).
            The shown value can be interpreted by the SCHUNK Service.

        """
        return self._send(0x96)

    def _send(self, command, data=b'', expected=None):
        """Send message, receive response.

        If the expected number of bytes doesn't match, an error is
        raised.
        If expected is a string, it is used as format strings to decode
        the received bytes.
        If expected is a bytes object, it is compared to the received
        data. If they are equal, the function returns, if not, an error
        is raised.

        """
        data = struct.pack('B', command) + data  # prepend command code
        data = struct.pack('B', len(data)) + data  # prepend dlen
        response = self._connection.send(data)

        if len(response) < 2:
            raise RuntimeError("Not enough data in response")
        dlen, cmd_code = response[:2]
        if dlen != len(response) - 1:
            raise RuntimeError("D-Len mismatch in response")
        if dlen == 2:
            error_prefix = {
                0x88: "CMD ERROR: ",
                0x89: "CMD WARNING: ",
                0x8A: "CMD INFO: ",
                command: "",
            }.get(cmd_code, "Command code 0x{:02X}: ")
            raise RuntimeError(error_prefix + decode_error(response[2]))
        if cmd_code != command:
            raise RuntimeError(
                "Unexpected command code in response: {}".format(hex(command)))
        response = response[2:]  # remove D-Len and command code

        if isinstance(expected, bytes):
            if response == expected:
                return
            else:
                err = "Unexpected response: {} instead of {}"
                raise RuntimeError(err.format(response, expected))

        format_string = None
        if isinstance(expected, str):
            format_string = expected
            expected = struct.calcsize(format_string)

        if expected is not None:
            if len(response) != expected:
                err = "Unexpected payload size in reponse: {} instead of {}"
                raise RuntimeError(err.format(len(response), expected))

        if format_string is not None:
            response = struct.unpack(format_string, response)

        return response

    def _move_pos_helper(self, code, *args):
        """Start moving to the given position and return estimated time.

        If the time cannot be estimated, 0.0 is returned.

        Use code=0xB0 for absolute and code=0xB8 for relative positions.
        For the "time" variants, use code=0xB1 and code=0xB9, resp.

        Trailing None arguments are removed, None arguments between
        other arguments are not allowed.
        At least one argument (position) has to be specified.

        """
        n = len(args)
        while n > 1 and args[n - 1] is None:
            n -= 1

        data = struct.pack('<{}f'.format(n), *args[:n])

        response = self._send(code, data)

        if response == b'OK':
            est_time = 0.0
        elif len(response) == 4:
            est_time, = struct.unpack('<f', response)
        else:
            raise RuntimeError("Unexpected reponse: {}".format(response))

        return est_time


class RS232Connection:

    """A serial connection using RS232.

    For further documentation see the __init__() docstring.

    """

    def __init__(self, id, serialmanager, *args, **kwargs):
        """Prepare a serial connection using the RS232 protocol.

        This can be used to initialize a :mod:`schunk.Module`.

        The connection is opened and closed on each :func:`send`.

        Parameters
        ----------
        id : int
            Module ID of the Schunk device.

        serialmanager
            A callable (to be called with ``*args`` and ``**kwargs``)
            that must return a context manager which in turn must have
            ``read()`` and ``write()`` methods.

            This is typically ``serial.Serial`` from PySerial_, but
            anything with a similar API can be used.

            .. _PySerial: http://pyserial.sf.net/

            .. note:: there should be a timeout, otherwise you may have
                      to wait forever for the functions to return if
                      there is an error.

        *args, **kwargs
            All further arguments are forwarded to `serialmanager`.

        See Also
        --------
        Module

        Examples
        --------

        A typical use case using PySerial_::

            import serial
            conn = schunk.RS232Connection(0x0B, serial.Serial, port=0,
                                          baudrate=9600, timeout=1))

        """
        self._id = id
        self._serialmanager = serialmanager
        self._serial_args = args
        self._serial_kwargs = kwargs

    def send(self, data):
        """Send and receive data via an RS232 connection.

        Adds 2 Group/ID bytes in the beginning and 2 CRC bytes in the
        end.  The first byte is always 0x05 (= message from master to
        module), the second byte holds the module ID.

        The connection is opened, the RS232 frame is sent to the module,
        a response is received and the connection is closed again.
        The 2 CRC bytes are checked (and removed), as well as the 2
        Group/ID bytes.
        If the first byte indicates an error (0x03), the response is
        returned normally. Error responses always have a D-Len of 2,
        i.e. they have 3 bytes: D-Len, command code and error code.

        Parameters
        ----------
        data : bytes
            Data to send. First byte: D-Len, second byte: command code.
            The (optional) rest are parameters.

        Returns
        -------
        bytes
            Response data received from the module, including D-Len and
            command code.

        See Also
        --------
        crc16

        """
        data = struct.pack('BB', 0x05, self._id) + data
        data += crc16(data)
        with self._serialmanager(*self._serial_args,
                                 **self._serial_kwargs) as serial:
            if serial.write(data) != len(data):
                raise RuntimeError("RS232: Error sending data")
            header = serial.read(3)
            if len(header) < 3:
                raise RuntimeError("RS232: Error reading header")

            msg_type, module_id, dlen = header
            if module_id != self._id:
                raise RuntimeError("RS232: Module ID mismatch")
            elif msg_type not in (0x03, 0x07):
                raise RuntimeError("RS232: Unexpected message type "
                                   "in response: 0x{:02X}".format(msg_type))
            crclen = 2
            the_rest = serial.read(dlen + crclen)

        if len(the_rest) < dlen + crclen:
            raise RuntimeError("RS232: Not enough data in response")

        crc = the_rest[-crclen:]
        the_rest = the_rest[:-crclen]
        if crc != crc16(header + the_rest):
            raise RuntimeError("RS232: CRC error in response")

        if msg_type == 0x03 and dlen != 2:
            # This should never happen, but who knows ...
            raise RuntimeError(
                "RS232: Message type 0x03, D-Len {}".format(dlen))

        # Note: error checking (if dlen == 2) is done in _send()

        return struct.pack('B', dlen) + the_rest


def decode_status(status):
    """Given a status byte return a dictionary of statuses."""
    statuses = ('referenced', 'moving', 'program_mode', 'warning', 'error',
                'brake', 'move_end', 'position_reached')
    return {name: bool(status & 2 ** bit) for bit, name in enumerate(statuses)}


def decode_error(error):
    """Given an error code return an error string."""
    return "{} (0x{:02X})".format(_error_codes.get(error, "UNKNOWN"), error)


def crc16_increment(crc, data):
    """Incrementally calculate CRC16.

    Implementation according to Schunk Motion Protocol documentation.

    Parameters
    ----------
    crc : int
        Previous CRC16 (2 bytes)
    data : int
        Data to append (1 byte)

    Returns
    -------
    int
        New CRC16 (again 2 bytes) after appending `data`.

    See Also
    --------
    crc16

    """
    # Note: if data is in 0..255, data & 0x00FF doesn't do anything.
    # But this is how it's done in the Schunk manual:

    return ((crc & 0xFF00) >> 8) ^ _crc16_tbl[(crc & 0x00FF) ^ (data & 0x00FF)]


def crc16(data):
    """Calculate CRC16 for a sequence of bytes.

    Parameters
    ----------
    data : iterable of integers (0..255) or bytes
        A sequece of bytes.

    Returns
    -------
    bytes
        CRC16 of `data` (2 bytes, little endian, a.k.a. '<H').

    See Also
    --------
    crc16_increment

    """
    crc = 0x0
    for b in data:
        crc = crc16_increment(crc, b)
    return struct.pack('<H', crc)


# Table copied from the Schunk manual:
_crc16_tbl = [0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
              0xC601, 0x06C0, 0x0780, 0xC741, 0x0500, 0xC5C1, 0xC481, 0x0440,
              0xCC01, 0x0CC0, 0x0D80, 0xCD41, 0x0F00, 0xCFC1, 0xCE81, 0x0E40,
              0x0A00, 0xCAC1, 0xCB81, 0x0B40, 0xC901, 0x09C0, 0x0880, 0xC841,
              0xD801, 0x18C0, 0x1980, 0xD941, 0x1B00, 0xDBC1, 0xDA81, 0x1A40,
              0x1E00, 0xDEC1, 0xDF81, 0x1F40, 0xDD01, 0x1DC0, 0x1C80, 0xDC41,
              0x1400, 0xD4C1, 0xD581, 0x1540, 0xD701, 0x17C0, 0x1680, 0xD641,
              0xD201, 0x12C0, 0x1380, 0xD341, 0x1100, 0xD1C1, 0xD081, 0x1040,
              0xF001, 0x30C0, 0x3180, 0xF141, 0x3300, 0xF3C1, 0xF281, 0x3240,
              0x3600, 0xF6C1, 0xF781, 0x3740, 0xF501, 0x35C0, 0x3480, 0xF441,
              0x3C00, 0xFCC1, 0xFD81, 0x3D40, 0xFF01, 0x3FC0, 0x3E80, 0xFE41,
              0xFA01, 0x3AC0, 0x3B80, 0xFB41, 0x3900, 0xF9C1, 0xF881, 0x3840,
              0x2800, 0xE8C1, 0xE981, 0x2940, 0xEB01, 0x2BC0, 0x2A80, 0xEA41,
              0xEE01, 0x2EC0, 0x2F80, 0xEF41, 0x2D00, 0xEDC1, 0xEC81, 0x2C40,
              0xE401, 0x24C0, 0x2580, 0xE541, 0x2700, 0xE7C1, 0xE681, 0x2640,
              0x2200, 0xE2C1, 0xE381, 0x2340, 0xE101, 0x21C0, 0x2080, 0xE041,
              0xA001, 0x60C0, 0x6180, 0xA141, 0x6300, 0xA3C1, 0xA281, 0x6240,
              0x6600, 0xA6C1, 0xA781, 0x6740, 0xA501, 0x65C0, 0x6480, 0xA441,
              0x6C00, 0xACC1, 0xAD81, 0x6D40, 0xAF01, 0x6FC0, 0x6E80, 0xAE41,
              0xAA01, 0x6AC0, 0x6B80, 0xAB41, 0x6900, 0xA9C1, 0xA881, 0x6840,
              0x7800, 0xB8C1, 0xB981, 0x7940, 0xBB01, 0x7BC0, 0x7A80, 0xBA41,
              0xBE01, 0x7EC0, 0x7F80, 0xBF41, 0x7D00, 0xBDC1, 0xBC81, 0x7C40,
              0xB401, 0x74C0, 0x7580, 0xB541, 0x7700, 0xB7C1, 0xB681, 0x7640,
              0x7200, 0xB2C1, 0xB381, 0x7340, 0xB101, 0x71C0, 0x7080, 0xB041,
              0x5000, 0x90C1, 0x9181, 0x5140, 0x9301, 0x53C0, 0x5280, 0x9241,
              0x9601, 0x56C0, 0x5780, 0x9741, 0x5500, 0x95C1, 0x9481, 0x5440,
              0x9C01, 0x5CC0, 0x5D80, 0x9D41, 0x5F00, 0x9FC1, 0x9E81, 0x5E40,
              0x5A00, 0x9AC1, 0x9B81, 0x5B40, 0x9901, 0x59C0, 0x5880, 0x9841,
              0x8801, 0x48C0, 0x4980, 0x8941, 0x4B00, 0x8BC1, 0x8A81, 0x4A40,
              0x4E00, 0x8EC1, 0x8F81, 0x4F40, 0x8D01, 0x4DC0, 0x4C80, 0x8C41,
              0x4400, 0x84C1, 0x8581, 0x4540, 0x8701, 0x47C0, 0x4680, 0x8641,
              0x8201, 0x42C0, 0x4380, 0x8341, 0x4100, 0x81C1, 0x8081, 0x4040]


_error_codes = {
    0x00: "NO ERROR",  # not in Schunk manual; added for convenience
    0x01: "INFO BOOT",
    0x02: "INFO NO FREE SPACE",
    0x03: "INFO NO RIGHTS",
    0x04: "INFO UNKNOWN COMMAND",
    0x05: "INFO FAILED",
    0x06: "NOT REFERENCED",
    0x07: "INFO SEARCH SINE VECTOR",
    0x08: "INFO NO ERROR",
    0x09: "INFO COMMUNICATION ERROR",
    0x10: "INFO TIMEOUT",
    0x16: "INFO WRONG BAUDRATE",
    0x19: "INFO CHECKSUM",
    0x1D: "INFO MESSAGE LENGTH",
    0x1E: "INFO WRONG PARAMETER",
    0x1F: "INFO PROGRAM END",
    0x40: "INFO TRIGGER",
    0x41: "INFO READY",
    0x42: "INFO GUI CONNECTED",
    0x43: "INFO GUI DISCONNECTED",
    0x44: "INFO PROGRAM CHANGED",
    0xC8: "ERROR WRONG RAMP TYPE",
    0xD2: "ERROR CONFIG MEMORY",
    0xD3: "ERROR PROGRAM MEMORY",
    0xD4: "ERROR INVALID PHRASE",
    0xD5: "ERROR SOFT LOW",
    0xD6: "ERROR SOFT HIGH",
    0xD7: "ERROR PRESSURE",
    0xD8: "ERROR SERVICE",
    0xD9: "ERROR EMERGENCY STOP",
    0xDA: "ERROR TOW",
    0xE4: "ERROR TOO FAST",
    0xEC: "ERROR MATH",
    0xDB: "ERROR VPC3",
    0xDC: "ERROR FRAGMENTATION",
    0xE4: "ERROR COMMUTATION",
    0xDE: "ERROR CURRENT",
    0xDF: "ERROR I2T",
    0xE0: "ERROR INITIALIZE",
    0xE1: "ERROR INTERNAL",
    0xE2: "ERROR HARD LOW",
    0xE3: "ERROR HARD HIGH",
    0x70: "ERROR TEMP LOW",
    0x71: "ERROR TEMP HIGH",
    0x72: "ERROR LOGIC LOW",
    0x73: "ERROR LOGIC HIGH",
    0x74: "ERROR MOTOR VOLTAGE LOW",
    0x75: "ERROR MOTOR VOLTAGE HIGH",
    0x76: "ERROR CABLE BREAK",
    0x78: "ERROR MOTOR TEMP",
}

_test_values = (-1.2345, 47.11, 287454020, -1122868, 512, -20482)
_test_format_string = '<2f2i2h'
