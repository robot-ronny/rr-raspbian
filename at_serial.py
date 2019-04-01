#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import datetime
import os
import sys
import time
import re
import logging
import serial
import decimal
import platform
from ctypes import *
from threading import Condition, Lock, Thread, Event
try:
    import fcntl
except ImportError:
    fcntl = None

class ATSerial:

    def __init__(self, device):
        self._ser = None
        self._device = device
        self.on_line = None

        self._command = Lock()
        self._event = Event()
        self._response = None

        logging.info("Connecting on device %s", self._device)
        self._ser = serial.Serial(self._device, baudrate=115200, timeout=3)

        self._lock()
        self._speed_up()

        logging.info("Success connect on device %s", self._device)

        self._ser.flush()
        self._ser.reset_input_buffer()
        self._ser.reset_output_buffer()
        time.sleep(0.5)
        self._ser.write(b'\x1b')

        self.is_run = False

    def __del__(self):
        self._unlock()
        try:
            self._ser.close()
        except Exception as e:
            pass
        self._ser = None

    def run(self):
        self.is_run = True
        while self.is_run:
            self._loop()

    def _loop(self):
        try:
            line = self._ser.readline()
        except serial.SerialException as e:
            logging.error("SerialException %s", e)
            self._ser.close()
            raise

        if line:
            logging.debug("Read line %s", line)

            line = line.decode().strip()

            if line[0] == '{':
                return

            if line[0] == '#':
                return

            if self.on_line:
                self.on_line(line)

            elif self._response is not None:
                if line == 'OK':
                    self._event.set()
                elif line == 'ERROR':
                    self._response = None
                    self._event.set()
                else:
                    self._response.append(line)

    def command(self, command):
        with self._command:
            logging.debug("Command %s", command)
            self._event.clear()
            command = 'AT' + command + '\r\n'
            self._response = []
            self._ser.write(command.encode('ascii'))
            if self.is_run:
                self._event.wait()
            else:
                while not self._event.is_set():
                    self._loop()
            response = self._response
            self._response = None
            return response

    def start(self):
        """Run in thread"""
        Thread(target=self.run, args=[]).start()

    def _lock(self):
        if not fcntl or not self._ser:
            return
        try:
            fcntl.flock(self._ser.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except Exception as e:
            raise Exception('Could not lock device %s' % self._device)

    def _unlock(self):
        if not fcntl or not self._ser:
            return
        fcntl.flock(self._ser.fileno(), fcntl.LOCK_UN)

    def _speed_up(self):
        if not fcntl:
            return
        if platform.system() != 'Linux':
            return

        TIOCGSERIAL = 0x0000541E
        TIOCSSERIAL = 0x0000541F
        ASYNC_LOW_LATENCY = 0x2000

        class serial_struct(Structure):
            _fields_ = [("type", c_int),
                        ("line", c_int),
                        ("port", c_uint),
                        ("irq", c_int),
                        ("flags", c_int),
                        ("xmit_fifo_size", c_int),
                        ("custom_divisor", c_int),
                        ("baud_base", c_int),
                        ("close_delay", c_ushort),
                        ("io_type", c_byte),
                        ("reserved_char", c_byte * 1),
                        ("hub6", c_uint),
                        ("closing_wait", c_ushort),
                        ("closing_wait2", c_ushort),
                        ("iomem_base", POINTER(c_ubyte)),
                        ("iomem_reg_shift", c_ushort),
                        ("port_high", c_int),
                        ("iomap_base", c_ulong)]

        buf = serial_struct()

        try:
            fcntl.ioctl(self._ser.fileno(), TIOCGSERIAL, buf)
            buf.flags |= ASYNC_LOW_LATENCY
            fcntl.ioctl(self._ser.fileno(), TIOCSSERIAL, buf)
        except Exception as e:
            pass
