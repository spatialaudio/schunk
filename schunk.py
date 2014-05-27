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
import contextlib
import functools


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
            Something that has an ``open()`` method which returns a
            coroutine.  This coroutine must accept a bytes object and
            send it to a Schunk module, read the response (taking D-Len
            into account) and yield the response (and further messages)
            as a bytes object.

            :class:`RS232Connection` happens to do exactly that.

        """
        self._connection = connection
        self._config = _Config(self)

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
        move_pos_blocking, move_pos_rel
        set_target_vel, set_target_acc, set_target_cur, set_target_jerk

        """
        return self._move_pos_helper(0xB0, position, velocity,
                                     acceleration, current, jerk)

    def move_pos_blocking(self, position, velocity=None, acceleration=None,
                          current=None, jerk=None):
        """Move to position and wait until position is reached.

        .. note:: *Impulse messages* must be activated for this to work,
                  see :meth:`toggle_impulse_message` and
                  :attr:`communication_mode`.

                  This applies to all ``*_blocking()`` methods.

        Returns
        -------
        float
            The final position.

        See Also
        --------
        move_pos

        """
        return self._move_pos_helper(0xB0, position, velocity,
                                     acceleration, current, jerk,
                                     blocking=True)

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
        move_pos_rel_blocking, move_pos
        set_target_vel, set_target_acc, set_target_cur, set_target_jerk

        """
        return self._move_pos_helper(0xB8, position, velocity,
                                     acceleration, current, jerk)

    def move_pos_rel_blocking(self, position, velocity=None, acceleration=None,
                              current=None, jerk=None):
        """Move to relative position and wait until position is reached.

        Returns
        -------
        float
            The actual relative motion.

        See Also
        --------
        move_pos_rel

        """
        return self._move_pos_helper(0xB8, position, velocity,
                                     acceleration, current, jerk,
                                     blocking=True)

    def move_pos_time(self, position, velocity=None, acceleration=None,
                      current=None, time=None):
        """2.1.5 MOVE POS TIME (0xB1).

        See Also
        --------
        move_pos_time_blocking, move_pos, set_target_time

        """
        return self._move_pos_helper(0xB1, position, velocity,
                                     acceleration, current, time)

    def move_pos_time_blocking(self, position, velocity=None,
                               acceleration=None, current=None, time=None):
        """Move to position and wait until position is reached.

        Returns
        -------
        float
            The final position.

        See Also
        --------
        move_pos_time

        """
        return self._move_pos_helper(0xB1, position, velocity,
                                     acceleration, current, time,
                                     blocking=True)

    def move_pos_time_rel(self, position, velocity=None, acceleration=None,
                          current=None, time=None):
        """2.1.6 MOVE POS TIME REL (0xB9).

        See Also
        --------
        move_pos_time_rel_blocking, move_pos_rel, set_target_time

        """
        return self._move_pos_helper(0xB9, position, velocity,
                                     acceleration, current, time)

    def move_pos_time_rel_blocking(self, position, velocity=None,
                                   acceleration=None, current=None, time=None):
        """Move to position and wait until position is reached.

        Returns
        -------
        float
            The actual relative motion.

        See Also
        --------
        move_pos_time_rel

        """
        return self._move_pos_helper(0xB9, position, velocity,
                                     acceleration, current, time,
                                     blocking=True)

    def set_target_vel(self, velocity):
        """2.1.14 SET TARGET VEL (0xA0).

        Initially, the target velocity is set to 10% of the maximum.

        """
        self._send(0xA0, struct.pack('<f', velocity), b'OK')

    def set_target_acc(self, acceleration):
        """2.1.15 SET TARGET ACC (0xA1).

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
        """2.2.6 CMD TOGGLE IMPULSE MESSAGE (0xE7).

        .. note:: *Impulse messages* must be switched on for
                  ``*_blocking()``, e.g. :meth:`move_pos_blocking`.

        Returns
        -------
        bool
            ``True`` if impulse messages were switched on, ``False`` if
            they were switched off.

        """
        response = self._send(0xE7)
        if response == b'ON':
            return True
        elif response == b'OFF':
            return False
        else:
            raise SchunkError("Unexpected response: {}".format(response))

    @property
    def config(self):
        """2.3.1 SET CONFIG (0x81) / 2.3.2 GET CONFIG (0x80).

        The `config` object has several attributes which can be queried
        and changed.
        Except where otherwise noted, the new settings are immediately
        stored in the EEPROM but are only applied after the module has
        been restarted.

        Some options are read-only, some can only be set as "Profi"
        user. See :meth:`change_user`.

        Attributes
        ----------

        module_type : bytes
        firmware_version : int
        protocol_version : int
        hardware_version : int
        firmware_date : bytes

        eeprom : bytes
            All configuration data is read/written in one process.
            Depending on the type of user certain data might not be
            written. After successful writing of the data, the module is
            rebooted.

            .. note:: This command should not be used with one's own
                      applications, as the structure of the data to be
                      received/sent is not known.

        module_id : int (1..255)
        group_id : int (1..255)
        rs232_baudrate : int (1200, 2400, 4800, 9600, 19200, 38400)
        can_baudrate : int (50, 100, 125, 250, 500, 800, 1000)

        communication_mode : int
            See :const:`communication_modes`.

        unit_system : int
            See :const:`unit_systems`.

        soft_high : float
            The transferred value is not written to the EEPROM. The
            settings are applied immediately.

        soft_low : float
            The transferred value is not written to the EEPROM. The
            settings are applied immediately.

        gear_ratio : float
            The Gear Ratio 1 is changed (the command has no use with an
            integer unit system). The transferred value is written to
            the EEPROM and applied immediately.

        max_velocity : float
        max_acceleration : float
        max_current : float
        nom_current : float
        max_jerk : float
        offset_phase_a : int
        offset_phase_b : int

        data_crc : int
            A CRC16 over all variable and not module specified
            paramenters (like serial number, current offset).

        reference_offset : float
        serial_number : int
        order_number : int

        """
        return self._config

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
            See :func:`decode_status`.
        error_code : int
            See :const:`error_codes` for a mapping to strings.

        """
        data = struct.pack('<fB', 0.0, 0x01 | 0x02 | 0x04)
        pos, vel, cur, status, error = self._send(0x95, data, '<3fBB')
        return pos, vel, cur, decode_status(status), error

    def reboot(self):
        """2.5.2 CMD REBOOT (0xE0)."""
        self._send(0xE0, expected=b'OK')

    def change_user(self, password=None):
        """2.5.6 CHANGE USER (0xE3).

        If no password is specified - or if the password is wrong - the
        user is changed to "User".
        The default password for "Profi" is "Schunk", but don't tell
        anyone!

        After a reboot, the default user is "User".

        """
        if password is None:
            data = b''
        elif isinstance(password, str):
            data = password.encode()
        else:
            data = password
        ok, user = self._send(0xE3, data, '2sB')
        if ok != b'OK':
            raise SchunkError("Error changing user")
        return {0x00: "User",
                0x01: "Diag",
                0x02: "Profi",
                0x03: "Advanced"}[user]

    def check_mc_pc_communication(self):
        """2.5.7 CHECK MC PC COMMUNICATION (0xE4).

        Returns
        -------
        bool
            ``True`` on success.

        """
        response = self._send(0xE4, expected=_test_format_string)
        if response != _test_values:
            raise SchunkError("Wrong response: {}".format(response))
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

    def ack(self):
        """2.8.1.4 CMD ACK (0x8B).

        Acknowledgement of a pending error message.

        """
        self._send(0x8B, expected=b'OK')

    def get_detailed_error_info(self):
        """2.8.1.5 GET DETAILED ERROR INFO (0x96).

        Returns
        -------
        command : {"ERROR", "WARNING", "INFO"}
        error_code : int
            See :const:`error_codes` for a mapping to strings.
        data : float
            The value can be interpreted by the Schunk Service.

        Raises
        ------
        SchunkError
            If no error is active, or no detailed information is
            available, the command is raising an exception saying:
            ``INFO FAILED (0x05)``.

        """
        command, error_code, data = self._send(0x96, expected='<BBf')
        command = {0x88: "ERROR", 0x89: "WARNING", 0x8A: "INFO"}[command]
        return command, error_code, data

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
        with contextlib.closing(self._gen_send(command, data)) as gen:
            return _check_response(next(gen), command, expected)

    def _gen_send(self, command, data=b''):
        """Send data and return a generator."""
        data = struct.pack('B', command) + data  # prepend command code
        data = struct.pack('B', len(data)) + data  # prepend dlen
        with contextlib.closing(self._connection.open()) as gen:
            yield gen.send(data)
            yield from gen

    def _move_pos_helper(self, command, *args, blocking=False):
        """Move to the given position.

        If blocking=False, the movement is started and the estimated
        time is immediately returned.
        If the time cannot be estimated, 0.0 is returned.
        If blocking=True, the final position (or the actual relative
        movement) is returned when the movement is finished.

        Use command=0xB0 for absolute and command=0xB8 for relative
        positions.  For the "time" variants, use command=0xB1 and
        command=0xB9, respectively.

        Trailing None arguments are removed, None arguments between
        other arguments are not allowed.
        At least one argument (position) has to be specified.

        """
        n = len(args)
        while n > 1 and args[n - 1] is None:
            n -= 1

        data = struct.pack('<{}f'.format(n), *args[:n])

        with contextlib.closing(self._gen_send(command, data)) as gen:
            response = _check_response(next(gen), command)
            if response == b'OK':
                est_time = 0.0
            elif len(response) == 4:
                est_time, = struct.unpack('<f', response)
            else:
                raise SchunkError("Unexpected reponse: {}".format(response))

            if not blocking:
                return est_time
            else:
                # 2.2.3 CMD POS REACHED (0x94)
                position, = _check_response(next(gen), 0x94, '<f')
                return position


def _check_response(response, command, expected=None):
    """Check if the response has the correct format."""
    if len(response) < 2:
        raise SchunkError("Not enough data in response")
    dlen, cmd_code = response[:2]
    if dlen != len(response) - 1:
        raise SchunkError("D-Len mismatch in response")
    if dlen == 2:
        error = response[2]
        error_prefix = {
            0x88: "CMD ERROR: ",
            0x89: "CMD WARNING: ",
            0x8A: "CMD INFO: ",
            command: "",
        }.get(cmd_code, "Command code 0x{:02X}: ".format(cmd_code))
        error_string = "{} (0x{:02X})".format(
            error_codes.get(error, "UNKNOWN"), error)
        raise SchunkError(error_prefix + error_string)

    if cmd_code != command:
        raise SchunkError(
            "Unexpected command code in response: {}".format(hex(cmd_code)))
    response = response[2:]  # remove D-Len and command code

    if isinstance(expected, bytes):
        if response == expected:
            return
        else:
            err = "Unexpected response: {} instead of {}"
            raise SchunkError(err.format(response, expected))

    format_string = None
    if isinstance(expected, str):
        format_string = expected
        expected = struct.calcsize(format_string)

    if expected is not None:
        if len(response) != expected:
            err = "Unexpected payload size in reponse: {} instead of {}"
            raise SchunkError(err.format(len(response), expected))

    if format_string is not None:
        response = struct.unpack(format_string, response)

    return response


class SchunkError(Exception):
    """This exception is raised on all kinds of errors."""
    pass


class _Config:

    """Helper class for the Module.config property."""

    _params = {
        'module_id':          (b'\x01', 'B'),
        'group_id':           (b'\x02', 'B'),
        'rs232_baudrate':     (b'\x03', 'H'),
        'can_baudrate':       (b'\x04', 'H'),
        'communication_mode': (b'\x05', 'B'),
        'unit_system':        (b'\x06', 'B'),
        'soft_high':          (b'\x07', 'f'),
        'soft_low':           (b'\x08', 'f'),
        'max_velocity':       (b'\x09', 'f'),
        'max_acceleration':   (b'\x0A', 'f'),
        'max_current':        (b'\x0B', 'f'),
        'nom_current':        (b'\x0C', 'f'),
        'max_jerk':           (b'\x0D', 'f'),
        'offset_phase_a':     (b'\x0E', 'H'),
        'offset_phase_b':     (b'\x0F', 'H'),
        'data_crc':           (b'\x13', 'H'),
        'reference_offset':   (b'\x14', 'f'),
        'serial_number':      (b'\x15', 'I'),
        'order_number':       (b'\x16', 'I'),
        'gear_ratio':         (b'\x18', 'f'),
        'eeprom':             (b'\xFE', None),

        'module_type':        (None, '8s4x2x2x2x26x'),
        # 'order_number' is already available
        'firmware_version':   (None, '8x4xH2x2x26x'),
        'protocol_version':   (None, '8x4x2xH2x26x'),
        'hardware_version':   (None, '8x4x2x2xH26x'),
        # Note: the Schunk manual states that the date string has 21 bytes,
        # the PR-70 modules returns 5 more bytes, however:
        'firmware_date':      (None, '8x4x2x2x2x26s'),
    }

    def __init__(self, module):
        # Avoid __setattr__:
        vars(self)['_module'] = module

    def _getAttributeNames(self):
        """Return all possible attributes.

        This is useful for auto-completion (e.g. IPython).

        """
        return self._params

    def __getattr__(self, name):
        """2.3.2 GET CONFIG (0x80)."""
        try:
            cmd_byte, format_string = self._params[name]
        except KeyError:
            raise AttributeError("Invalid parameter: {}".format(name))

        if cmd_byte is None:
            result, = self._module._send(0x80, expected=format_string)
            firstbyte = None
        elif format_string is None:
            result = self._module._send(0x80, cmd_byte)
            firstbyte = result[0:1]
            result = result[1:]
        else:
            firstbyte, result = self._module._send(0x80, cmd_byte,
                                                   '<s' + format_string)
        if firstbyte != cmd_byte:
            raise SchunkError("Unexpected subcommand: {}".format(firstbyte))

        return result

    def __setattr__(self, name, value):
        """2.3.1 SET CONFIG (0x81)."""
        try:
            cmd_byte, format_string = self._params[name]
        except KeyError:
            raise AttributeError("Invalid parameter: {}".format(name))

        if cmd_byte is None:
            raise AttributeError("{} is read-only".format(name))

        if format_string is not None:
            value = struct.pack('<' + format_string, value)

        result, = self._module._send(0x81, cmd_byte + value, '3s')
        if result != b'OK' + cmd_byte:
            raise SchunkError("Error setting {}".format(name))


def coroutine(func):
    """Decorator for generator functions that calls next() initially."""
    @functools.wraps(func)
    def start(*args, **kwargs):
        gen = func(*args, **kwargs)
        next(gen)
        return gen
    return start


class RS232Connection:

    """A serial connection using RS232.

    For further documentation see the __init__() docstring.

    """

    def __init__(self, id, serialmanager, *args, **kwargs):
        """Prepare a serial connection using the RS232 protocol.

        This can be used to initialize a :class:`Module`.

        The connection is opened with :meth:`open`.

        Parameters
        ----------
        id : int
            Module ID of the Schunk device.

        serialmanager
            A callable (to be called with ``*args`` and ``**kwargs``)
            that must return a context manager which in turn must have
            ``read()`` and ``write()`` methods (and it should close the
            connection automatically in the end).

            This is typically ``serial.Serial`` from PySerial_, but
            anything with a similar API can be used.

            .. _PySerial: http://pyserial.sf.net/

            .. note:: there should be a timeout, otherwise you may have
                      to wait forever for the functions to return if
                      there is an error.
                      On the other hand, receiving multiple responses
                      only works if there is no timeout in between.
                      Multiple responses are needed for the blocking
                      movement commands, e.g.
                      :meth:`Module.move_pos_blocking`.

        *args, **kwargs
            All further arguments are forwarded to `serialmanager`.

        See Also
        --------
        Module

        Examples
        --------

        Using PySerial_:

        >>> import serial
        >>> conn = RS232Connection(0x0B, serial.Serial, port=0,
        ...                        baudrate=9600, timeout=1)

        """
        self._id = id
        self._serialmanager = serialmanager
        self._serial_args = args
        self._serial_kwargs = kwargs

    @coroutine
    def open(self):
        """Open an RS232 connection.

        A coroutine (a.k.a. generator object) is returned which can be
        used to send and receive one or more data frames.

        Calling ``.send(data)`` on this coroutine creates an RS232 frame
        around `data`, sends it to the module and waits for a response.

        `data` must have at least two bytes, D-Len and command code.
        The (optional) rest are parameters.
        2 Group/ID bytes are added in the beginning and 2 CRC bytes in
        the end.  The first byte is always 0x05 (= message from master
        to module), the second byte holds the module ID.

        When receiving a response, the 2 CRC bytes are checked (and
        removed), as well as the 2 Group/ID bytes.

        The connection is kept open and the coroutine can be invoked
        repeatedly to receive further data frames.
        Use ``.send(None)`` or the built-in ``next()`` function to
        receive a data frame without sending anything.

        When the desired number of frames has been received, the
        connection has to be closed with the generator's ``close()``
        method.

        Yields
        ------
        bytes
            Response data received from the module, including D-Len and
            command code.

            If the first RS232 byte indicates an error (0x03), the
            response is returned normally and the error has to be
            handled in the calling function. Error responses always have
            a D-Len of 2, i.e. they have 3 bytes: D-Len, command code
            and error code.

        See Also
        --------
        crc16

        """
        response = None
        with self._serialmanager(*self._serial_args,
                                 **self._serial_kwargs) as serial:

            while True:
                next_msg = yield response

                if next_msg is not None:
                    next_msg = struct.pack('BB', 0x05, self._id) + next_msg
                    next_msg += crc16(next_msg)
                    if serial.write(next_msg) != len(next_msg):
                        raise SchunkRS232Error("Error sending data")

                header = serial.read(3)
                if len(header) < 3:
                    raise SchunkRS232Error("Error reading response")

                msg_type, module_id, dlen = header
                if module_id != self._id:
                    raise SchunkRS232Error("Module ID mismatch")
                elif msg_type not in (0x03, 0x07):
                    raise SchunkRS232Error(
                        "Unexpected message type in response: "
                        "0x{:02X}".format(msg_type))
                crclen = 2
                the_rest = serial.read(dlen + crclen)

                if len(the_rest) < dlen + crclen:
                    raise SchunkRS232Error("Not enough data in response")

                crc = the_rest[-crclen:]
                the_rest = the_rest[:-crclen]
                if crc != crc16(header + the_rest):
                    raise SchunkRS232Error("CRC error in response")

                if msg_type == 0x03 and dlen != 2:
                    # This should never happen, but who knows ...
                    raise SchunkRS232Error(
                        "Message type 0x03, D-Len {}, data: {}".format(
                            dlen, the_rest))

                # Note: error checking (if dlen == 2) is not done here

                response = struct.pack('B', dlen) + the_rest


class SchunkRS232Error(SchunkError):
    """Exception class for errors related to RS232 connections.

    It is derived from :exc:`SchunkError`, so it is normally
    sufficient to check only for this::

        try:
            ...
            # Something that may throw SchunkError or SchunkRS232Error
            ...
        except SchunkError as e:
            # Do something with e
            ...

    """
    pass


def decode_status(status):
    """This is internally used in :meth:`Module.get_state`.

    >>> status = decode_status(0x03)
    >>> from pprint import pprint
    >>> pprint(status)  # to get pretty dict display
    {'brake': False,
     'error': False,
     'move_end': False,
     'moving': True,
     'position_reached': False,
     'program_mode': False,
     'referenced': True,
     'warning': False}

    """
    statuses = ('referenced', 'moving', 'program_mode', 'warning', 'error',
                'brake', 'move_end', 'position_reached')
    return {name: bool(status & 2 ** bit) for bit, name in enumerate(statuses)}


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
_crc16_tbl = [
    0x0000, 0xC0C1, 0xC181, 0x0140, 0xC301, 0x03C0, 0x0280, 0xC241,
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


communication_modes = {
    0x00: 'AUTO',
    0x01: 'RS232',
    0x02: 'CAN',
    0x03: 'Profibus DPV0',
    0x04: 'RS232 Silent',
}
"""Available communication modes.

See :attr:`Module.config`.

"""

unit_systems = {
    0x00: '[mm]',
    0x01: '[m]',
    0x02: '[Inch]',
    0x03: '[rad]',
    0x04: '[Degree]',
    0x05: '[Intern]',
    0x06: '[µm] Integer',
    0x07: '[µDegree] Integer',
    0x08: '[µInch] Integer',
    0x09: '[Milli - degree] Integer',
}
"""Available unit systems.

See :attr:`Module.config`.

.. note:: This Python module doesn't support integer unit systems.

"""


error_codes = {
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
"""Error codes.

See also :meth:`Module.get_state`.

.. note:: Error in Schunk manual: key 0xE4 (= 228) is not unique!

"""

# The Schunk people chose -1.2345 and 47.11 as test values which is
# unfortunate, because they cannot be represented exactly as binary floating
# point numbers.
_test_values = ( -1.2345000505447388, 47.11000061035156, 287454020, -1122868,
                512, -20482)
_test_format_string = '<2f2i2h'
