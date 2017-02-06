# -*- coding: utf-8 -*-
import urllib
import urllib2
import cookielib
import re
import Queue
import string
import thread
import threading
import time
import os
import sys
import io

# for gzip
import gzip
from StringIO import StringIO


MainPage = "http://www.pixiv.net/"
LoginPage = "https://accounts.pixiv.net/login"
LoginPage_Post = "https://accounts.pixiv.net/api/login?lang=zh"
pixiv_url_login_post = "https://accounts.pixiv.net/api/login"

CookieFileName = 'PixivCookie.txt'
PixivIdListFileName = "PixivIdList.txt"

# 在 GetIllustationListViaPixivId 中修改，用以控制保存文件路径
FileSaveDirectory = u''

pixiv_id = '<禁则事项>'
pixiv_password ='<禁则事项>'


Logindata = {
    'pixiv_id':'y1598753y@126.com',
    'password':'1qazxsw2',
    'captcha':'',
    'g_recaptcha_response':'',
    'post_key':'',
    'source':'accounts',
}
Header = {
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Encoding': 'gzip, deflate, sdch',
    'Accept-Language': 'zh-CN,zh;q=0.8,en;q=0.6',
    'Connection': 'keep-alive',
    'Host': 'accounts.pixiv.net',
    'Referer': 'http://www.pixiv.net/',
    'Upgrade-Insecure-Requests': '1',
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) '
                  'Chrome/50.0.2661.102 Safari/537.36'
}


class PixivItem:
    def __init__(self):
        self.title = ''
        self.illust_id = ''
        self.img_url = ''


def Gzip(data):
    buf = StringIO(data)
    f = gzip.GzipFile(fileobj=buf)
    return f.read()


def GenerateOpener(header):
    if os.path.exists(CookieFileName):
        os.remove(CookieFileName)
    global GlobalCookie
    GlobalCookie = cookielib.MozillaCookieJar(CookieFileName)
    cp = urllib2.HTTPCookieProcessor(GlobalCookie)
    op = urllib2.build_opener(cp)
    h = []
    for key, value in header.items():
        elem = (key, value)
        h.append(elem)
    op.addheaders = h
    return op


def GetOpenerFromCookie(header):
    global GlobalCookie
    GlobalCookie = cookielib.MozillaCookieJar()
    if os.path.exists(CookieFileName):
        GlobalCookie.load(CookieFileName)
    cp = urllib2.HTTPCookieProcessor(GlobalCookie)
    op = urllib2.build_opener(cp)
    h = []
    for key, value in header.items():
        elem = (key, value)
        h.append(elem)
    op.addheaders = h
    return op


def IsLoggedIn(opener):
    res = opener.open(MainPage)
    status = re.findall('pixiv.user.loggedIn = ([\w]*);', Gzip(res.read()), re.S)
    res.close()
    assert(len(status) > 0)
    b = re.search('true', status[0], re.IGNORECASE)
    return bool(b)


def UpdatePostKey(opener):
    response = opener.open(LoginPage)
    data = Gzip(response.read())
    response.close()
    post_key = re.findall('name="post_key" value="(.*?)"', data, re.S)
    if len(post_key) == 0:
        print 'error not found post_key! maybe is logged in.'
        Logindata['post_key'] = ''
        return ''
    else:
        Logindata['post_key'] = post_key[0]
        return post_key[0]


def Login():
    opener = GenerateOpener(Header)
    pixiv_key = UpdatePostKey(opener)

    post_data = {
        'pixiv_id': pixiv_id,
        'password': pixiv_password,
        'post_key': pixiv_key,
        'source': 'accounts'
    }
    post_data = urllib.urlencode(post_data).encode('utf-8')

    try:
        op_login = opener.open(pixiv_url_login_post, post_data)
        op_login.close()
    except urllib2.URLError, e:
        if hasattr(e, 'reason'):
            print '[URLError] reason: ' + str(e.reason)
        elif hasattr(e, 'code'):
            print '[URLError] code: ' + str(e.code)
        else:
            print '[URLError] Unkonwn reason.'
    except:
        print 'others error.'
    else:
        return opener


def IsFileExists(path):
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


def SaveToFile(full_path, data, overwrite = False):
    if not overwrite:
        if os.path.exists(full_path):
            print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
    try:
        with open(full_path, 'wb') as o:
            o.write(data)
    except:
        print u'保存出错.'


def HandleManga(title, mag_url):
    response = opener.open(mag_url)
    html = Gzip(response.read())
    pages = re.findall('data-src="(.*?)"', html, re.S)
    for i in range(len(pages)):
        HandleImage(title, pages[i])


def HandleImage(title, img_url, overwrite = False):
    # 转换为原图的url
    old_last = img_url.split("/")[-1]                       # 形如 60442846_p0_master1200.jpg
    last1 = old_last.split("_")
    last2 = old_last.split(".")                             # 这里缩略图的后缀只会是jpg，所以下面才直接以png重试
    new_last = last1[0] + '_' + last1[1] + '.' + last2[1]   # 去掉 master1200  ->  60442846_p0.jpg

    ori_url = img_url[0:20]
    ori_url += "img-original/"
    ori_url += img_url.split("img-master/")[1]
    ori_url = ori_url.replace(old_last, new_last)

    title = (last1[0] + '_' + last1[1] + '_').decode('utf-8') + title + ('.' + last2[1]).decode('utf-8')

    full_path = FileSaveDirectory + ValidFileName(title)
    if IsFileExists(full_path):
        print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
        return
    try:
        ii = opener.open(ori_url)
        SaveToFile(full_path, ii.read())
    except urllib2.URLError, e:
        if hasattr(e, 'code') and e.code == 404:            # 以png作为后缀重试
            new_last1 = last1[0] + '_' + last1[1] + '.png'
            ori_url = ori_url.replace(new_last, new_last1)
            title = title.replace('.jpg', '.png')

            full_path = FileSaveDirectory + ValidFileName(title)
            if IsFileExists(full_path):
                print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
                return

            ii = opener.open(ori_url)
            SaveToFile(full_path, ii.read())


def HandleGif(title, zip_url):
    print "[Debug] zip_url %s" %(zip_url)

    tmp = zip_url.split('/')[-1].split(".")[0]
    name = tmp + title + '.zip'

    full_path = FileSaveDirectory + ValidFileName(title)
    if IsFileExists(full_path):
        print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
        return

    ii = opener.open(zip_url)
    with open(name, 'wb') as o:
        o.write(ii.read())


def ParsePage(opener, url):
    print '[Debug]: open ' + url
    try:
        response = opener.open(url)
        html = Gzip(response.read())

        tmp = re.findall("<title>「(.*?)」.*?</title>", html, re.S)
        title = tmp[0].decode("utf-8")

        manga = re.findall('<div class="works_display"><a href="', html, re.S)
        if manga:
            # 漫画模式
            HandleManga(title, url.replace("medium", "manga"))

        else:
            zip = re.findall('"src":"(.*?)"', html, re.S)
            if zip:
                # gif动画模式
                # 这里的zip包链接需要去除转义的反斜杠
                for i in range(len(zip)):
                    zip_url = zip[i].replace('\\', '')
                    HandleGif(title, zip_url)

            else:
                # 普通模式
                img_url = re.findall('<div class="works_display"><.*?><img src="(.*?)"', html, re.S)
                if len(img_url) > 1:
                    print "[Debug] multi image url in normal mode. (%s)" %(url)
                HandleImage(title, img_url[0])

    except urllib2.URLError, e:
        if hasattr(e, 'code'):
            print '[Debug] URLError, code: ' + str(e.code)
        elif hasattr(e, 'reason'):
            print '[Debug] URLError, reason: ' + str(e.reason)
        else:
            print '[Debug] URLError, Unkonwn reason.'
        return


def GetIllustationListViaPixivId(opener, pid):
    # 获取一个画师的所有插画
    print "[Debug] process Id: %s" %(pid)

    global FileSaveDirectory
    FileSaveDirectory = pid + '\\'
    if not os.path.exists(pid):
        os.makedirs(pid)

    page_url = "http://www.pixiv.net/member_illust.php?id=%s" %(pid)
    img_list = []

    # 第一页
    try:
        response = opener.open(page_url)
        html = Gzip(response.read())
        tmp = re.findall('<li class="image-item"><a href="/(.*?)"', html, re.S)
        for item in tmp:
            img_list.append(MainPage + item.replace("amp;", ""))

    except urllib2.URLError, e:
        if hasattr(e, 'code'):
            print '[Debug] URLError, code: ' + str(e.code)
        elif hasattr(e, 'reason'):
            print '[Debug] URLError, reason: ' + str(e.reason)
        else:
            print '[Debug] URLError, Unkonwn reason.'
        return

    page_cnt = 2
    while (re.findall('<span class="next"><a href=', html, re.S)):
        # 后续
        page_url = "http://www.pixiv.net/member_illust.php?id=%s&type=all&p=%d" %(pid, page_cnt)
        try:
            response = opener.open(page_url)
            html = Gzip(response.read())
            tmp = re.findall('<li class="image-item"><a href="/(.*?)"', html, re.S)      # MainPage带有一个正斜杠, 这里少配一个
            for item in tmp:
                img_list.append(MainPage + item.replace("amp;", ""))

        except urllib2.URLError, e:
            if hasattr(e, 'code'):
                print '[Debug] URLError, code: ' + str(e.code)
            elif hasattr(e, 'reason'):
                print '[Debug] URLError, reason: ' + str(e.reason)
            else:
                print '[Debug] URLError, Unkonwn reason.'
            return
        page_cnt += 1

    for url in img_list:
        ParsePage(opener, url)


def GetIllustationListViaPixivIdList(opener):
    # 通过文件读取画师ID列表
    if not os.path.exists(PixivIdListFileName):
        print u'未找到画师Id列表文件 ' + PixivIdListFileName
        return False
    print u'读取列表...',
    list = []
    with open(PixivIdListFileName, "r") as f:
        line = f.readline()
        while line:
            line = line.strip('\r\n')
            line = line.strip('\n')
            line = line.strip('\r')
            list.append(line.strip('\n'))
            line = f.readline()
    print u'完成，读取到%d个Id' %(len(list))

    for id in list:
        GetIllustationListViaPixivId(opener, id)


if __name__ == "__main__":
    opener = GetOpenerFromCookie(Header)
    if not IsLoggedIn(opener):
        print "not founed cookie file or invalid cookie file, loggin..."
        opener = Login()
        global GlobalCookie
        GlobalCookie.save()
    if IsLoggedIn(opener):
        print "Login Succeess."
        assert(opener)
        GetIllustationListViaPixivIdList(opener)

    else:
        print "Login Error."


