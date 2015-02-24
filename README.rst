Schunk Motion Protocol for Python
=================================

Documentation:
   http://schunk.rtfd.org/

Code:
   http://github.com/spatialaudio/schunk/

Python Package Index:
   http://pypi.python.org/pypi/SchunkMotionProtocol/

Schunk Motion Protocol manual:
   http://www.schunk.com/schunk_files/attachments/MotionControl_en_2010-03.pdf

   A newer version of the manual is available `in a huge zip file from the
   Schunk website`__ (have a look in the directory ``Manuals/Motion Control/``)

__ http://www.schunk.com/schunk_files/attachments/MTS_v_1_56_20130904.zip

Disclaimer
----------

This is *not* a commercial product and the author has *no relation whatsoever*
to `SCHUNK GmbH & Co. KG`__.

__ http://schunk.com/

**Use at your own risk!**

Devices
-------

Only 1 device was tested: `Schunk PR-70 Servo Electric Swivel Unit`__.

__ http://tinyurl.com/schunk-pr/

Defaults for this device: serial (RS232), baudrate=9600, module ID 11 (0x0B).

Other devices may or may not work.

Only firmware version 1.56 was tested, other versions may or may not work.

Requirements
------------

Obviously, Python_ is required.  Any version >= 2.7 should do.

Typically, PySerial_ handles the serial connection,
but any library with a similar API can be used.

py.test_ is used for the tests.

.. _Python: http://www.python.org/
.. _PySerial: http://pyserial.sf.net/
.. _py.test: http://pytest.org/

Limitations
-----------

Only a subset of the Schunk Motion Protocol is supported.

Only the direct response to a command can be obtained, *impulse messages* are
not supported.
One exception is the "CMD POS REACHED" impulse message which is used to realize
movement commands which are waiting until the movement is finished, e.g.
``move_pos_blocking()``.

Only floating point unit systems are supported.

The connection is opened and closed for each message.
Keeping the connection open is not supported.

Only serial communication is implemented. No CAN, no Profibus.

Installation
------------

Using `pip <http://www.pip-installer.org/en/latest/installing.html>`_, you can
download and install the latest release with a single command::

   pip install --user SchunkMotionProtocol

If you want to install it system-wide for all users (assuming you have the
necessary rights), you can just drop the ``--user`` option.

To un-install, use::

   pip uninstall SchunkMotionProtocol

If you prefer, you can also download the package from
`PyPI <https://pypi.python.org/pypi/SchunkMotionProtocol/>`_, extract it, change
to the main directory and install it using::

   python setup.py install --user

If you want to get the newest development version from
`Github <http://github.com/spatialaudio/schunk/>`_::

   git clone https://github.com/spatialaudio/schunk.git
   cd schunk
   python setup.py install --user

Alternatively, you can just copy ``schunk.py`` to your working directory.

If you want to make changes to the code, you should type::

   python setup.py develop --user

or, alternatively::

   pip install --user -e .

... where ``-e`` stands for ``--editable``.

Tests
-----

Tests are implemented using py.test_, run this in the main directory::

   python setup.py test

Examples
--------

This should get you started::

   import schunk
   import serial

   mod = schunk.Module(schunk.SerialConnection(
       0x0B, serial.Serial, port=0, baudrate=9600, timeout=1))

   mod.move_pos(42)

Use the ID of your Schunk module instead of ``0x0B``.

See the documentation of PySerial_ for all possible
serial port options.
You probably only have to change ``port``, e.g. ``port='/dev/ttyS1'`` or
``port='COM3'``.

It is useful to specify a *timeout*, otherwise you may have to wait forever for
the functions to return if there is an error.
On the other hand, if you want to use the blocking commands (``*_blocking()``),
you should disable the timeout (or make it longer than the expected movement
times).

If the parameters for your setup don't change, you can write them into a
separate file, e.g. with the name ``myschunk.py``::

   import schunk
   import serial
   
   module1 = schunk.Module(schunk.SerialConnection(
       0x0B, serial.Serial, port=0, baudrate=9600, timeout=1))

and then use it like this in all our scripts::

   from myschunk import module1
   module1.move_pos(42)

The file ``myschunk.py`` must be in the current directory for this to work.

If you are an object-oriented kind of person, you can of course also write your
own class::

   import schunk
   import serial
   
   class MySchunkModule(schunk.Module):
       def __init__(self):
           schunk.Module.__init__(self, schunk.SerialConnection(
               0x0B, serial.Serial, port=0, baudrate=9600, timeout=1))
   
   module1 = MySchunkModule()
   module1.move_pos(42)

.. vim:textwidth=80
