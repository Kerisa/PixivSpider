# -*- coding: utf-8 -*-

import os
import configparser

USER_DATA_DIR = ''
DOWNLOADS_DIR = ''
COOKIE_FILE_NAME = ''
DB_FILE_NAME = ''
DB_DEF_FILE = ''
LOG_FILE = ''

def GetUserDataDir():
    global USER_DATA_DIR
    if USER_DATA_DIR == '':
        USER_DATA_DIR = os.path.join(os.path.dirname(__file__), os.path.pardir, 'pixivspider-data')
        if not os.path.exists(USER_DATA_DIR):
            os.makedirs(USER_DATA_DIR)
    return USER_DATA_DIR

def GetConfigFilePath():
    global CONFIG_FILE_NAME
    if CONFIG_FILE_NAME == '':
        CONFIG_FILE_NAME = os.path.join(GetUserDataDir(), 'config.ini')
    return CONFIG_FILE_NAME

def GetAccountName():
    global USER_ACCOUNT_NAME
    if USER_ACCOUNT_NAME == '':
        config = ConfigParser.ConfigParser()
        config.read(GetConfigFilePath())
        USER_ACCOUNT_NAME = config.get('account', 'pixiv_id')
    return USER_ACCOUNT_NAME

def GetAccountPwd():
    global USER_ACCOUNT_PWD
    if USER_ACCOUNT_PWD == '':
        config = ConfigParser.ConfigParser()
        config.read(GetConfigFilePath())
        USER_ACCOUNT_PWD = config.get('account', 'pixiv_password')
    return USER_ACCOUNT_PWD

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
    global DB_DEF_FILE
    if DB_DEF_FILE == '':
        DB_DEF_FILE = os.path.join(os.path.dirname(__file__), 'db_def.sql')
    return DB_DEF_FILE

def GetLogFilePath():
    global LOG_FILE
    if LOG_FILE == '':
        LOG_FILE = os.path.join(GetUserDataDir(), 'record.log')
    return LOG_FILE

