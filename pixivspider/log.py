# -*- coding: utf-8 -*-

import logging
import sys

import conf

g_Log = None

def InitLogger():
    global g_Log
    #logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    g_Log = logging.getLogger()
    g_Log.setLevel(level = logging.DEBUG)

    formatter = logging.Formatter('[%(asctime)s][%(levelname)s] %(message)s')

    # stdout
    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setLevel(level = logging.INFO)
    stream_handler.setFormatter(formatter)
    g_Log.addHandler(stream_handler)

    # file
    file_handler = logging.FileHandler(conf.GetLogFilePath(), encoding = 'utf-8')
    file_handler.setLevel(level = logging.DEBUG)
    file_handler.setFormatter(formatter)
    g_Log.addHandler(file_handler)


def debug(format, *tupleArg):
    g_Log.debug(format, *tupleArg)


def info(format, *tupleArg):
    g_Log.info(format, *tupleArg)


def warn(format, *tupleArg):
    g_Log.warn(format, *tupleArg)


def error_stack(format, *tupleArg):
    g_Log.error(format, *tupleArg, exc_info = True)


def error(format, *tupleArg):
    g_Log.error(format, *tupleArg)


def exception(format, *tupleArg):
    g_Log.exception(format, *tupleArg)