# -*- coding:utf-8 -*-

import os
import re

# for gzip
import gzip


def Gzip(data):
    return gzip.decompress(data).decode()

def GetIllustIdFromURL(url):
    res = re.findall('illust_id=([\d]+)', url)
    if len(res) == 1:
        return int(res[0])
    else:
        return 0


def IsFileExists(path, withSize = True):
    if withSize:
        return os.path.exists(path) and os.path.getsize(path) > 0
    else:
        return os.path.exists(path)


def ValidFileName(filename):
    filename = filename.replace('/', '／')
    filename = filename.replace('\\', '＼')
    filename = filename.replace(':', '：')
    filename = filename.replace('<', '＜')
    filename = filename.replace('>', '＞')
    filename = filename.replace('*', '＊')
    filename = filename.replace('|', '｜')
    filename = filename.replace('?', '？')
    filename = filename.replace('"', '＂')
    return filename