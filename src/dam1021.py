# -*- coding: utf-8 -*-

"""This library streamlines communication with a dam1012. The dam1021 is a DAC module based on a discrete R-2R sign magnitude DAC design, with FPGA based FIFO buffering/reclocking and custom digital filters."""

__author__ = "Forta(a)"
__copyright__ = "Copyright 2015, Forta(a)"

__license__ = "GPL 3.0"
__version__ = "0.1"
__maintainer__ = "Forta(a)"
__status__ = "Alpha"

#you may change these values to meet your requirements
DEFAULT_SERIAL_DEVICE="/dev/ttyUSB0"
DEFAULT_SERIAL_TIMEOUT=1

VOLUME_INF=-99
VOLUME_SUP=15
INPUT_SRC_SET=range(3)

import logging
import time
import StringIO
import hashlib

#not included in std python library
import serial
import xmodem

log=logging.getLogger('dam1021')

class Dam1021Error(Exception):
    """General exception class that covers all high level errors."""

    pass


class Connection(object):
    """Creates object for serial communication with a DAC.
    
    :param device: serial device to use
    :param timeout: default timeout for serial communication
    :param cautious: additional safeguards for non umanager command
    
    Usage::
   
    >>> import dam1021
    >>> conn = dam1021.Connection('/dev/ttyS0')
    >>> conn.download('newfilter.skr')
    >>> conn.set_current_volume_level(-14)
    >>> conn.set_flash_volume_level(-22)
    >>> conn.set_input_source(0)
    """

    def __init__(self,device=DEFAULT_SERIAL_DEVICE,timeout=DEFAULT_SERIAL_TIMEOUT,cautious = False):
      
        self.ser = serial.Serial(device,115200,timeout=timeout)
      
        self.cautious = cautious

        #cmdlist
        self.cmd_umanager_invocation = '+++'
        self.cmd_umanager_termination = 'exit'
        self.cmd_download = 'download'
        self.cmd_flash_volume = 'set volume={:+03d}'
        self.cmd_current_volume = 'V{:+03d}'
        self.cmd_input_selection = 'I{:d}'

        #internal stuff
        self.cr = '\r'
        self.umanager_prompt = '# '
        self.umanager_errtxt = 'invalid command'
        self.umanager_opened = False
        self.buf_on_exit = '{}\r\n'.format(self.cmd_umanager_termination)
        self.readsize = 300
        self.umanager_waitcoeff = 2.5
        self.intercmd = 1
        self.volume_inf = VOLUME_INF
        self.volume_sup = VOLUME_SUP
        self.input_src_set = INPUT_SRC_SET
        self.xmodem_crc = 'C'
        self.reprogram_ack = 'programmed'

        def putc_generator(ser):
            def putc(data,timeout=1):
                instance_timeout = ser.timeout
                ser.timeout = timeout
                rv = ser.write(data)
                ser.timeout = instance_timeout
                return rv if rv else None
            return putc
    
        def getc_generator(ser):
            def getc(size,timeout=1):
                instance_timeout = ser.timeout
                ser.timeout = timeout
                rv = ser.read(size)
                ser.timeout = instance_timeout
                return rv if rv else None
            return getc

        self.xmodem = xmodem.XMODEM(getc_generator(self.ser),putc_generator(self.ser))

        log.debug("Serial port opened")

    def close(self):
        """Closes serial port
      
        """

        self.close_umanager()
        self.ser.close()
        log.debug("Serial port closed")

    def open_umanager(self):
        """Used to open an uManager session.
        
        """

        if self.umanager_opened:
            return
        self.ser.write(self.cmd_umanager_invocation)
        time.sleep(self.intercmd*self.umanager_waitcoeff)
        #if we are already in umanager, this will give us a fresh prompt
        self.ser.write(self.cr)
        buf = self.ser.read(self.readsize)
        log.debug(buf)
        if buf.endswith(self.umanager_prompt):
            log.debug("uManager opened")
            self.umanager_opened = True
        else:
            raise Dam1021Error(1,"Failed to open uManager")

    def close_umanager(self, force=False):
        """Used to close an uManager session.
        
        :param force: try to close a session regardless of a connection object internal state
        """
      
        if not (force or self.umanager_opened):
            return
        # make sure we've got a fresh prompt
        self.ser.write(self.cr)
        time.sleep(self.intercmd)
        self.ser.write(''.join((self.cmd_umanager_termination,self.cr)))
        buf = self.ser.read(self.readsize)
        log.debug(buf)
        if buf.endswith(self.buf_on_exit):
            log.debug("uManager closed")
            self.umanager_opened = False
        else:
            raise Dam1021Error(2,"Failed to close uManager")

    def download(self,data):
        """Used to download firmware or filter set.
        
        :param data: binary string to push via serial 
        """
        
        self.open_umanager()
        self.ser.write(''.join((self.cmd_download,self.cr)))
        time.sleep(self.intercmd)
        buf = self.ser.read(self.readsize)
        log.debug(buf)
        if buf.endswith(self.xmodem_crc):
            if self.xmodem.send(StringIO.StringIO(data)):
                log.info("Data sent")
            else:
                raise Dam1021Error(4,"Error during file download")
        else:
            raise Dam1021Error(3,"uManager is not ready to accept a data")
      
        buf = self.ser.read(self.readsize*3)
        log.debug(buf)
        if buf.find(self.reprogram_ack) != -1:
            skr_sum = hashlib.sha1(data).hexdigest()
            log.info("DAC reprogrammed. Data SHA-1 checksum: {}".format(skr_sum))
        else:
            raise Dam1021Error(5,"uManager accepted data and not reprogrammed")
         
        self.close_umanager()

        return skr_sum

    def set_current_volume_level(self,level):
        """Used to set current volume level. Not to be confused with a volume level stored in flash.
        
        :param level: volume level; accepted values: [{},{}] 
        """.format(VOLUME_INF,VOLUME_SUP)

        if level < self.volume_inf or level > self.volume_sup:
            raise Dam1021Error(6,"Forbbiden volume level")
         
        if self.cautious:
            self.close_umanager(True)
         
        tries = 2
        while tries:
            self.ser.write(''.join((self.cmd_current_volume.format(level),self.cr)))
            time.sleep(self.intercmd)
            buf = self.ser.read(self.readsize)
            log.debug(buf.__repr__())
            if buf.rstrip().endswith(self.cmd_current_volume.format(level)):
                log.info("Current volume level set to {0:d}".format(level))
                break
            else:
                tries -= 1
        if tries == 0:
            raise Dam1021Error(7,"Failed to set current volume level")
      

    def set_flash_volume_level(self,level): 
        """Used to set volume level on flash. Not to be confused with current volume level. Current volume is set to this value during power-up.
        
        :param level: volume level; accepted values: [{},{}] 
        """.format(VOLUME_INF,VOLUME_SUP)

        if level < self.volume_inf or level > self.volume_sup:
            raise Dam1021Error(6,"Forbbiden volume level")

        self.open_umanager()
        self.ser.write(''.join((self.cmd_flash_volume.format(level),self.cr)))
        time.sleep(self.intercmd)
        buf = self.ser.read(self.readsize)
        log.debug(buf)
        if buf.rstrip().lower().endswith(self.umanager_errtxt):
            raise Dam1021Error(8,"Failed to set flash volume level")
        else:
            log.info("Flash volume level set to {0:d}".format(level))
        self.close_umanager()


    def set_input_source(self,input_src):
        """Used to set input source for a DAC.
        
        :param input_src: volume level; accepted values: [{},{}] 
        """.format(min(INPUT_SRC_SET),max(INPUT_SRC_SET))

        if input_src not in self.input_src_set:
            raise Dam1021Error(9,"Forbbiden input source")
         
        if self.cautious:
            self.close_umanager(True)
         
        tries = 2
        while tries:
            self.ser.write(''.join((self.cmd_input_selection.format(input_src),self.cr)))
            time.sleep(self.intercmd)
            buf = self.ser.read(self.readsize)
            log.debug(buf)
            if buf.rstrip().endswith(self.cmd_input_selection.format(input_src)):
                log.info("Input source set to {0:d}".format(input_src))
                break
            else:
                tries -= 1
        if tries == 0:
            raise Dam1021Error(10,"Failed to set input source")  

def run():
    from argparse import ArgumentParser,FileType
    import sys

    logging.basicConfig()

    description = "This script is designed to operate with a dam1021 DAC. Four operations are available. Exclusive access to a serial device is a prerequisite."
   
    epilog =  "Example: python %(prog)s -s /dev/ttyUSB0 -f firmware.skr"

   
    parser = ArgumentParser(description=description,epilog=epilog)

    parser.add_argument("-v", "--verbose", help="increase output verbosity",action="store_true")
    parser.add_argument("-V","--Version", action="version", version="%(prog)s {}".format(__version__))
    parser.add_argument("-s", "--serial-device", dest="serial",
                        help="serial device to use [default: {}]".format(DEFAULT_SERIAL_DEVICE),
                        default=DEFAULT_SERIAL_DEVICE)
    parser.add_argument("-t", "--timeout",
                        help="serial device to use in seconds [default: {}]".format(DEFAULT_SERIAL_TIMEOUT),
                        default=DEFAULT_SERIAL_TIMEOUT,type=float)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-d","--download", help="download a new firmware or filter set",
                       type=FileType('rb'))
    group.add_argument("-l","--volume-level", 
                       help="set a current volume level [{},{}]".format(VOLUME_INF,VOLUME_SUP),
                   )
    group.add_argument("-f","--flash-volume-level", 
                       help="set a volume level on flash [{},{}]".format(VOLUME_INF,VOLUME_SUP),
                   )
    group.add_argument("-i","--input-source", 
                       help="set input source [{},{}]".format(min(INPUT_SRC_SET),max(INPUT_SRC_SET)),
                   )

       
    args = parser.parse_args()

    if args.verbose:
        log.level = logging.DEBUG
    else:
        log.level = logging.INFO

    try:
        conn = Connection(args.serial,args.timeout)
        try:
            if args.download:
                conn.download(args.download.read())
            elif args.volume_level:
                conn.set_current_volume_level(int(args.volume_level))
            elif args.flash_volume_level:
                conn.set_flash_volume_level(int(args.flash_volume_level))
            elif args.input_source:
                conn.set_input_source(int(args.input_source))
        except Exception as e:
            log.error(e)
        finally:
            conn.close()
    except Exception as e:
        log.error(e)

if __name__ == "__main__":
    run()
