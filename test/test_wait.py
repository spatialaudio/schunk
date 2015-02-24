"""Test wait_until_position_reached()."""

import schunk
import pytest


class DummyConnection:

    stopped = False
    _count = 0

    def __init__(self, exc_class=None):
        self._exc_class = exc_class

    @schunk.coroutine
    def open(self):
        response = None
        while True:
            data = yield response
            assert not self.stopped

            if data == b'\x06\x95\x00\x00\x00\x00\x01':  # GET STATE
                self._count += 1
                if self._count == 3:
                    if self._exc_class:
                        raise self._exc_class()
                    # reached 0.0
                    yield bytearray(b'\x07\x95\x00\x00\x00\x00\x80\x00')
                    raise RuntimeError("Too many calls to the generator!")
                elif self._count == 2:
                    # Impulse message is ignored and next() is called:
                    # CMD POS REACHED 0.0
                    response = bytearray(b'\x05\x94\x00\x00\x00\x00')
                else:
                    # not reached
                    response = bytearray(b'\x07\x95\x00\x00\x00\x00\x7F\x00')
            elif data == b'\x01\x91':  # CMD STOP
                self.stopped = True
                yield NotImplemented  # returned data is ignored
                raise RuntimeError("Too many calls to the generator!")
            elif data is None:  # request more data after impulse message
                # not reached
                response = bytearray(b'\x07\x95\x00\x00\x00\x00\x7F\x00')
            else:
                raise RuntimeError("Unexpected data: {}".format(data))


def test_success():
    mod = schunk.Module(DummyConnection())
    assert not mod._connection.stopped
    pos = mod.wait_until_position_reached()
    assert pos == 0.0
    assert not mod._connection.stopped


@pytest.mark.parametrize("exc_class", [KeyboardInterrupt, SystemExit])
def test_exception(exc_class):
    mod = schunk.Module(DummyConnection(exc_class))
    assert not mod._connection.stopped
    with pytest.raises(exc_class):
        mod.wait_until_position_reached()
    assert mod._connection.stopped
