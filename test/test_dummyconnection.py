"""Test as much as possible without connection to an actual device."""

import schunk
import pytest


class DummyConnection:
    def __init__(self, expected, answer):
        self._expected = expected
        self._answer = answer

    @schunk.coroutine
    def open(self):
        data = yield
        assert data == self._expected
        if isinstance(self._answer, bytes):
            yield self._answer
        else:
            yield from self._answer
        # The generator must be closed before reaching this:
        raise RuntimeError("Too many calls to the generator!")


success_cases = {
    # 2.1.1 CMD REFERENCE (0x92)
    'reference': (
        'reference',
        (),
        {},
        b'\x01\x92',
        b'\x03\x92OK',
        None),

    # 2.1.3 MOVE POS (0xB0)
    'move_pos': (
        'move_pos',
        (10.0,),
        {},
        b'\x05\xB0\x00\x00\x20\x41',
        b'\x05\xB0\xCD\xCC\x04\x41',
        8.300000190734863),
    # TODO: check return b'OK'
    # TODO: check further arguments

    'move_pos_blocking': (
        'move_pos_blocking',
        (10.0,),
        {},
        b'\x05\xB0\x00\x00\x20\x41',
        (b'\x05\xB0\xCD\xCC\x04\x41', b'\x05\x94\x00\x00\x20\x41'),
        10.0),

    # 2.1.4 MOVE POS REL (0xB8)
    'move_pos_rel': (
        'move_pos_rel',
        (10.0,),
        {},
        b'\x05\xB8\x00\x00\x20\x41',
        b'\x05\xB8\xCD\xCC\x04\x41',
        8.300000190734863),
    # TODO: see move_pos, is repetition necessary?

    'move_pos_rel_blocking': (
        'move_pos_rel_blocking',
        (10.0,),
        {},
        b'\x05\xB8\x00\x00\x20\x41',
        (b'\x05\xB8\xCD\xCC\x04\x41', b'\x05\x94\x00\x00\x20\x41'),
        10.0),

    # 2.1.5 MOVE POS TIME (0xB1)
    'move_pos_time': (
        'move_pos_time',
        (10.0,),
        {},
        b'\x05\xB1\x00\x00\x20\x41',
        b'\x05\xB1\x00\x00\xA0\x40',
        5.0),

    'move_pos_time_blocking': (
        'move_pos_time_blocking',
        (10.0,),
        {},
        b'\x05\xB1\x00\x00\x20\x41',
        (b'\x05\xB1\x00\x00\xA0\x40', b'\05\x94\x00\x00\x20\x41'),
        10.0),

    # 2.1.6 MOVE POS TIME REL (0xB9)
    'move_pos_time_rel': (
        'move_pos_time_rel',
        (10.0,),
        {},
        b'\x05\xB9\x00\x00\x20\x41',
        b'\x05\xB9\x00\x00\xA0\x40',
        5.0),

    'move_pos_time_rel_blocking': (
        'move_pos_time_rel_blocking',
        (10.0,),
        {},
        b'\x05\xB9\x00\x00\x20\x41',
        (b'\x05\xB9\x00\x00\xA0\x40', b'\05\x94\x00\x00\x20\x41'),
        10.0),

    # 2.1.14 SET TARGET VEL (0xA0)
    'set_target_vel': (
        'set_target_vel',
        (12.2,),
        {},
        b'\x05\xA0\x33\x33\x43\x41',
        b'\x03\xA0OK',
        None),

    # 2.1.15 SET TARGET ACC (0xA1)
    'set_target_acc': (
        'set_target_acc',
        (12.2,),
        {},
        b'\x05\xA1\x33\x33\x43\x41',
        b'\x03\xA1OK',
        None),

    # 2.1.16 SET TARGET JERK (0xA2)
    'set_target_jerk': (
        'set_target_jerk',
        (1000.0,),
        {},
        b'\x05\xA2\x00\x00\x7A\x44',
        b'\x03\xA2OK',
        None),

    # 2.1.17 SET TARGET CUR (0xA3)
    'set_target_cur': (
        'set_target_cur',
        (2.7,),
        {},
        b'\x05\xA3\xCD\xCC\x2C\x40',
        b'\x03\xA3OK',
        None),

    # 2.1.18 SET TARGET TIME (0xA4)
    'set_target_time': (
        'set_target_time',
        (4.7,),
        {},
        b'\x05\xA4\x66\x66\x96\x40',
        b'\x03\xA4OK',
        None),

    # 2.1.19 CMD STOP (0x91)
    'stop': (
        'stop',
        (),
        {},
        b'\x01\x91',
        b'\x03\x91OK',
        None),

    # 2.2.6 CMD TOGGLE IMPULSE MESSAGE (0xE7)
    'toggle_impulse_message_off': (
        'toggle_impulse_message',
        (),
        {},
        b'\x01\xE7',
        b'\x04\xE7OFF',
        False),
    'toggle_impulse_message_on': (
        'toggle_impulse_message',
        (),
        {},
        b'\x01\xE7',
        b'\x03\xE7ON',
        True),

    # 2.5.1 GET STATE (0x95)
    'get_state1': (
        'get_state',
        (),
        {},
        b'\x06\x95\x00\x00\x00\x00\x07',
        b'\x0F\x95\xD6\xA3\x70\x41\x56\xC9\x41\x40\x3C\x41\xEB\x3E\x03\x00',
        (15.039999008178711, 3.0279135704040527, 0.4594820737838745,
         {'brake': False,
          'error': False,
          'move_end': False,
          'moving': True,
          'position_reached': False,
          'program_mode': False,
          'referenced': True,
          'warning': False},
         0x00)),
    'get_state2': (
        'get_state',
        (),
        {},
        b'\x06\x95\x00\x00\x00\x00\x07',
        b'\x0F\x95\x53\x63\xB7\x41\x00\x00\x00\x00\x00\x00\x00\x00\x61\xD9',
        (22.923498153686523, 0.0, 0.0,
         {'brake': True,
          'error': False,
          'move_end': True,
          'moving': False,
          'position_reached': False,
          'program_mode': False,
          'referenced': True,
          'warning': False},
         0xD9)),
    'get_state3': (
        'get_state',
        (),
        {},
        b'\x06\x95\x00\x00\x00\x00\x07',
        b'\x0F\x95\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x20\x00',
        (0.0, 0.0, 0.0,
         {'brake': True,  # typo in Schunk manual: "brake is off"
          'error': False,
          'move_end': False,
          'moving': False,
          'position_reached': False,
          'program_mode': False,
          'referenced': False,
          'warning': False},
         0x00)),

    # 2.5.2 CMD REBOOT (0xE0)
    'reboot': (
        'reboot',
        (),
        {},
        b'\x01\xE0',
        b'\x03\xE0OK',
        None),

    # 2.5.6 CHANGE USER (0xE3)
    'change_user_default': (
        'change_user',
        (),
        {},
        b'\x01\xE3',
        b'\x04\xE3OK\x00',
        "User"),
    'change_user_profi': (
        'change_user',
        ("Schunk",),
        {},
        b'\x07\xE3Schunk',
        b'\x04\xE3OK\x02',
        "Profi"),

    # 2.5.7 CHECK MC PC COMMUNICATION (0xE4)
    'check_mc_pc_communication': (
        'check_mc_pc_communication',
        (),
        {},
        b'\x01\xE4',
        b'\x15\xE4\x19\x04\x9E\xBF\xA4\x70\x3C\x42\x44\x33\x22\x11'
            b'\xCC\xDD\xEE\xFF\x00\x02\xFE\xAF',
        True),

    # 2.5.8 CHECK PC MC COMMUNICATION (0xE5)
    'check_pc_mc_communication': (
        'check_pc_mc_communication',
        (),
        {},
        b'\x15\xE5\x19\x04\x9E\xBF\xA4\x70\x3C\x42\x44\x33\x22\x11'
            b'\xCC\xDD\xEE\xFF\x00\x02\xFE\xAF',
        b'\x04\xE5OK\x00',
        True),

    # 2.8.1.4 CMD ACK (0x8B)
    'ack': (
        'ack',
        (),
        {},
        b'\x01\x8B',
        b'\x03\x8BOK',
        None),

    # 2.8.1.5 GET DETAILED ERROR INFO (0x96)
    'get_detailed_error_info': (
        'get_detailed_error_info',
        (),
        {},
        b'\x01\x96',
        b'\x07\x96\x88\xD9\x00\x00\x00\x00',
        ("ERROR", 0xD9, 0.0)),
}


@pytest.mark.parametrize(
    "method, args, kwargs, expected_bytes, answer_bytes, expected_result",
    success_cases.values(), ids=list(success_cases))
def test_success(
        method, args, kwargs, expected_bytes, answer_bytes, expected_result):
    mod = schunk.Module(DummyConnection(expected_bytes, answer_bytes))
    result = getattr(mod, method)(*args, **kwargs)
    assert result == expected_result


# 2.3.1 SET CONFIG (0x81)
set_config_success = {
    'module_id': (
        'module_id',
        12,
        b'\x03\x81\x01\x0C',
        b'\x04\x81OK\x01'),
}


@pytest.mark.parametrize(
    "property, value, expected_bytes, answer_bytes",
    set_config_success.values(), ids=list(set_config_success))
def test_set_config(property, value, expected_bytes, answer_bytes):
    mod = schunk.Module(DummyConnection(expected_bytes, answer_bytes))
    setattr(mod.config, property, value)


# 2.3.2 GET CONFIG (0x80)
get_config_success = {
    'unit_system': (
        'unit_system',
        b'\x02\x80\x06',
        b'\x03\x80\x06\x00',
        0),  # '[mm]'

    'module_type': (
        'module_type',
        b'\x01\x80',
        b'\x2D\x80\x50\x52\x2D\x37\x30\x00\x00\x00\x00\x00\x00\x00\x79\x00'
            b'\x03\x00\x12\x02\x31\x31\x3A\x32\x32\x3A\x32\x37\x20\x20\x4A'
            b'\x75\x6C\x20\x20\x33\x20\x32\x30\x30\x38?????',
        b'PR-70\x00\x00\x00'),

    'firmware_version': (
        'firmware_version',
        b'\x01\x80',
        b'\x2D\x80\x50\x52\x2D\x37\x30\x00\x00\x00\x00\x00\x00\x00\x79\x00'
            b'\x03\x00\x12\x02\x31\x31\x3A\x32\x32\x3A\x32\x37\x20\x20\x4A'
            b'\x75\x6C\x20\x20\x33\x20\x32\x30\x30\x38?????',
        121),  # 1.21

    'protocol_version': (
        'protocol_version',
        b'\x01\x80',
        b'\x2D\x80\x50\x52\x2D\x37\x30\x00\x00\x00\x00\x00\x00\x00\x79\x00'
            b'\x03\x00\x12\x02\x31\x31\x3A\x32\x32\x3A\x32\x37\x20\x20\x4A'
            b'\x75\x6C\x20\x20\x33\x20\x32\x30\x30\x38?????',
        3),

    'hardware_version': (
        'hardware_version',
        b'\x01\x80',
        b'\x2D\x80\x50\x52\x2D\x37\x30\x00\x00\x00\x00\x00\x00\x00\x79\x00'
            b'\x03\x00\x12\x02\x31\x31\x3A\x32\x32\x3A\x32\x37\x20\x20\x4A'
            b'\x75\x6C\x20\x20\x33\x20\x32\x30\x30\x38?????',
        530),  # 5.30


    'firmware_date': (
        'firmware_date',
        b'\x01\x80',
        b'\x2D\x80\x50\x52\x2D\x37\x30\x00\x00\x00\x00\x00\x00\x00\x79\x00'
            b'\x03\x00\x12\x02\x31\x31\x3A\x32\x32\x3A\x32\x37\x20\x20\x4A'
            b'\x75\x6C\x20\x20\x33\x20\x32\x30\x30\x38?????',
        b'11:22:27  Jul  3 2008?????'),
}


@pytest.mark.parametrize(
    "property, expected_bytes, answer_bytes, expected_result",
    get_config_success.values(), ids=list(get_config_success))
def test_get_config(property, expected_bytes, answer_bytes, expected_result):
    mod = schunk.Module(DummyConnection(expected_bytes, answer_bytes))
    result = getattr(mod.config, property)
    assert result == expected_result


class DummySerialManager:
    def __init__(self, expected, answer):
        for data in expected, answer:
            assert data[-2:] == schunk.crc16(data[:-2])
        self._expected = expected
        self._answer = answer

    def __enter__(self):
        return self

    def __exit__(self, *args):
        # TODO: somehow check if connection was closed in the end?
        pass

    def write(self, data):
        assert data == self._expected
        return len(data)

    def read(self, n):
        assert n <= len(self._answer)
        result = self._answer[:n]
        self._answer = self._answer[n:]
        return result


rs232_success_cases = {
    # 6.1.1.1 Referencing
    'reference': (
        'reference',
        (),
        {},
        b'\x05\x01\x01\x92\xD1\x31',
        b'\x07\x01\x03\x92OK\xE9\xD9',
        None),

    # 6.1.1.2 MOVE POS 10 [mm]
    'move_pos': (
        'move_pos',
        (10,),
        {},
        b'\x05\x01\x05\xB0\x00\x00\x20\x41\x48\x80',
        b'\x07\x01\x05\xB0\xEE\xEE\x56\x40\x7B\xE4',
        3.358333110809326),

    # 6.1.1.4 Troubleshooting
    'ack': (
        'ack',
        (),
        {},
        b'\x05\x01\x01\x8B\x10\xFB',
        b'\x07\x01\x03\x8BOK\x38\x1E',
        None),

    # 6.1.1.6 CHECK PC MC COMMUNICATION
    'check_pc_mc_communication': (
        'check_pc_mc_communication',
        (),
        {},
        # Note: error in Schunk documentation: CRC \x89\xD7 should be \x29\xD7
        b'\x05\x01\x15\xE5\x19\x04\x9E\xBF\xA4\x70\x3C\x42\x44\x33\x22\x11'
            b'\xCC\xDD\xEE\xFF\x00\x02\xFE\xAF\x29\xD7',
        b'\x07\x01\x04\xE5OK\x00\xB6\xFA',
        True),
}


@pytest.mark.parametrize(
    "method, args, kwargs, expected_bytes, answer_bytes, expected_result",
    rs232_success_cases.values(), ids=list(rs232_success_cases))
def test_rs232_success(
        method, args, kwargs, expected_bytes, answer_bytes, expected_result):
    mod = schunk.Module(schunk.RS232Connection(
        # This is the module ID used in the examples of the Schunk nanual:
        0x01,
        DummySerialManager,
        # Test passing args and kwargs:
        expected_bytes, answer=answer_bytes))
    result = getattr(mod, method)(*args, **kwargs)
    assert result == expected_result
