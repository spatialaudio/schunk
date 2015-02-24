"""Test for KeyboardInterrupt/SystemExit during blocking function calls."""

import schunk
import pytest


class RaisingConnection:

    stopped = False

    def __init__(self, exc_class, immediately):
        self._immediately = immediately
        self._exc_class = exc_class

    @schunk.coroutine
    def open(self):
        data = yield
        if data == b'\x05\xB0\x00\x00\x20\x41':  # MOVE POS 10.0
            if self._immediately:
                raise self._exc_class()
            yield bytearray(b'\x05\xB0????')  # estimated time is ignored
            if not self._immediately:
                raise self._exc_class()
        elif data == b'\x01\x91':  # CMD STOP
            self.stopped = True
            yield NotImplemented  # returned data is ignored
            raise RuntimeError("Too many calls to the generator!")
        else:
            raise RuntimeError("Unexpected data: {}".format(data))
        raise RuntimeError("Too many calls to the generator!")


@pytest.fixture(params=[True, False])
def true_or_false(request):
    return request.param


@pytest.mark.parametrize("exc_class", [KeyboardInterrupt, SystemExit])
def test_raise_during_move_pos_blocking(exc_class, true_or_false):
    mod = schunk.Module(RaisingConnection(exc_class, true_or_false))
    assert not mod._connection.stopped
    with pytest.raises(exc_class):
        mod.move_pos_blocking(10.0)
    assert mod._connection.stopped


def test_that_other_exceptions_dont_stop(true_or_false):
    mod = schunk.Module(RaisingConnection(schunk.SchunkError, true_or_false))
    assert not mod._connection.stopped
    with pytest.raises(schunk.SchunkError):
        mod.move_pos_blocking(10.0)
    assert not mod._connection.stopped
