# -*- coding:utf-8 -*-

import os
import re

# for gzip
import gzip
from StringIO import StringIO


def Gzip(data):
    buf = StringIO(data)
    f = gzip.GzipFile(fileobj=buf)
    return f.read()

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
    assert(unicode == type(filename))
    filename = filename.replace(u'/', u'／')
    filename = filename.replace(u'\\', u'＼')
    filename = filename.replace(u':', u'：')
    filename = filename.replace(u'<', u'＜')
    filename = filename.replace(u'>', u'＞')
    filename = filename.replace(u'*', u'＊')
    filename = filename.replace(u'|', u'｜')
    filename = filename.replace(u'?', u'？')
    filename = filename.replace(u'"', u'＂')
#    print filename.encode('GB18030')
    return filename