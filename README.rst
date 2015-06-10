Python inferface for the dam1021 DAC
====================================
This library streamlines communication with a `dam1012 <http://soekris.dk/dam1021.html>`_ device. The dam1021 is a DAC module based on a discrete R-2R sign magnitude DAC design, with FPGA based FIFO buffering/reclocking and custom digital filters.

Features
--------

- Load firmware or filer set
- Digital volume control (two modes)
- Input source selection
- Command-line utility

Installation
------------

You need Python 2.7.x and additional libraries `pyserial <https://pypi.python.org/pypi/pyserial>`_ and `xmodem <https://pypi.python.org/pypi/xmodem>`_. Then fetch dam1021.py file or whole this repository and you are done.

Installation procedure step-by-step
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

* Install `Python 2.7.8 <https://www.python.org/downloads/>`_ or later from the 2.7.x branch.
* Then grab needed virtualenv package:

.. code-block:: bash

   pip install virtualenv

Windows users might find `virtualenvwrapper-win <https://github.com/davidmarble/virtualenvwrapper-win/>`_ handy.

* Create a `new virtualenv <https://virtualenv.pypa.io/en/latest/userguide.html>`_.
* In your new environment:

.. code-block:: bash
		
   pip install pyserial
   pip install xmodem
		
* Then grab `dam1021.py <https://github.com/fortaa/dam1021/raw/master/src/dam1021.py>`_ and put it on a desired path.

Command-line utility
--------------------

All API functionality is exposed via a built-in utility. So you don't need to code yourself::

    $ python dam1021.py -h
    usage: dam1021.py [-h] [-v] [-V] [-s SERIAL] [-t TIMEOUT]
                      (-d DOWNLOAD | -l VOLUME_LEVEL | -f FLASH_VOLUME_LEVEL | -i INPUT_SOURCE)
    
    This script is designed to operate with a dam1021 DAC. Four operations are
    available. Exclusive access to a serial device is a prerequisite.
    
    optional arguments:
      -h, --help            show this help message and exit
      -v, --verbose         increase output verbosity
      -V, --Version         show program's version number and exit
      -s SERIAL, --serial-device SERIAL
                            serial device to use [default: /dev/ttyUSB0]
      -t TIMEOUT, --timeout TIMEOUT
                            serial device to use in seconds [default: 1]
      -d DOWNLOAD, --download DOWNLOAD
                            download a new firmware or filter set
      -l VOLUME_LEVEL, --volume-level VOLUME_LEVEL
                            set a current volume level [-99,15]
      -f FLASH_VOLUME_LEVEL, --flash-volume-level FLASH_VOLUME_LEVEL
                            set a volume level on flash [-99,15]
      -i INPUT_SOURCE, --input-source INPUT_SOURCE
                            set input source [0,2]
    
    Example: python dam1021.py -s /dev/ttyUSB0 -f firmware.skr

  		
API
---

Obviously you can create your own too. API is pretty simple:

.. code-block:: python

		>>> import dam1021
		>>> conn = dam1021.Connection('/dev/ttyS0')
		>>> conn.download('newfilter.skr')
		>>> conn.set_current_volume_level(-14)
		>>> conn.set_flash_volume_level(-22)
		>>> conn.set_input_source(0)
		...

Serial device naming conventions
--------------------------------

POSIX systems are quite consistent in this regard. Usually your serial port is described as ``/dev/ttysomething`` (e.g. ``/dev/ttyUSB0`` in case of a USB serial converter on Linux platform).
Windows users should try either ``COMxx`` or ``\\.\COMxx`` where ``xx`` is 1,2 and so on. YMMV.

Bugs
----

Please use issue tracker for reporting.
