# -*- coding: utf-8 -*-

import os
import configparser

USER_DATA_DIR = ''
DOWNLOADS_DIR = ''

USER_ACCOUNT_NAME = ''
USER_ACCOUNT_PWD = ''

CONFIG_FILE_NAME = ''
COOKIE_FILE_NAME = ''
DB_FILE_NAME = ''
DB_DEF_FILE_NAME = ''
LOG_FILE_NAME = ''

def GetUserDataDir():
    global USER_DATA_DIR
    if USER_DATA_DIR == '':
        USER_DATA_DIR = os.path.join(os.path.dirname(__file__), os.path.pardir, 'pixivspider-data')
        if not os.path.exists(USER_DATA_DIR):
            os.makedirs(USER_DATA_DIR)
    return USER_DATA_DIR

def GetDownloadsDir():
    global DOWNLOADS_DIR
    if DOWNLOADS_DIR == '':
        DOWNLOADS_DIR = os.path.join(GetUserDataDir(), 'downloads')
        if not os.path.exists(DOWNLOADS_DIR):
            os.makedirs(DOWNLOADS_DIR)
    return DOWNLOADS_DIR

def GetCookiePath():
    global COOKIE_FILE_NAME
    if COOKIE_FILE_NAME == '':
        COOKIE_FILE_NAME = os.path.join(GetUserDataDir(), 'PixivCookie.txt')
    return COOKIE_FILE_NAME

def GetDBPath():
    global DB_FILE_NAME
    if DB_FILE_NAME == '':
        DB_FILE_NAME = os.path.join(GetUserDataDir(), 'download.db')
    return DB_FILE_NAME

def GetDBDefinePath():
    global DB_DEF_FILE_NAME
    if DB_DEF_FILE_NAME == '':
        DB_DEF_FILE_NAME = os.path.join(os.path.dirname(__file__), 'db_def.sql')
    return DB_DEF_FILE_NAME

def GetLogFilePath():
    global LOG_FILE_NAME
    if LOG_FILE_NAME == '':
        LOG_FILE_NAME = os.path.join(GetUserDataDir(), 'record.log')
    return LOG_FILE_NAME

