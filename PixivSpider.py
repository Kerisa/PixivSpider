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


class ImgInfo:
    def __init__(self):
        self.webUrl=''
        self.webContent=''
        self.originalImgUrl=''
        self.title=''
        self.pageCount=0
        self.illustId=0
        self.type=''


MainPage = "http://www.pixiv.net/"
LoginPage = "https://accounts.pixiv.net/login"
LoginPage_Post = "https://accounts.pixiv.net/api/login?lang=zh"
pixiv_url_login_post = "https://accounts.pixiv.net/api/login"

CookieFileName = 'PixivCookie.txt'
PixivIdListFileName = "PixivIdList.txt"
PixivDownloadedImagesFileName = "PixivDownloadedImages.txt"

# 在 GetIllustationListViaPixivId 中修改，用以控制保存文件路径
FileSaveDirectory = u''

pixiv_id = '<禁则事项>'
pixiv_password ='<禁则事项>'


Logindata = {
    'pixiv_id':pixiv_id,
    'password':pixiv_password,
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


def PrintUrlErrorMsg(e):
    if hasattr(e, 'reason'):
        print '[URLError] reason: ' + str(e.reason)
    elif hasattr(e, 'code'):
        print '[URLError] code: ' + str(e.code)
    else:
        print '[URLError] Unkonwn reason.'


################################################################################


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
        PrintUrlErrorMsg(e)
    except:
        print 'others error.'
    else:
        return opener


################################################################################


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


def SaveToFile(img_url, full_path, data, overwrite = False):
    if not overwrite and os.path.exists(full_path):
        print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
    else:
        try:
            with open(full_path, 'wb') as o:
                o.write(data)
        except:
            print u'保存 %s 失败.' %(img_url)
            return False
    return True


################################################################################

DownloadedImage = set()

def LoadDownloadedImages():
    global DownloadedImage
    if not os.path.exists(PixivDownloadedImagesFileName):
        f = open(PixivDownloadedImagesFileName, 'w')
        f.close()
    else:
        with open(PixivDownloadedImagesFileName, "r") as f:
            line = f.readline()
            while line:
                DownloadedImage.add(int(line.strip('\n')))
                line = f.readline()
    print u'已下载列表加载完成，读取到%d个已下载的插画Id' %(len(DownloadedImage))


def LogFailedPage(dir, url):
    str = u'' + dir + u'*' + url + u'\n'
    with open("PixivErrorPage.txt", 'a') as ff:
        ff.write(str)


def LogSuccessPage(url):
    id = GetIllustIdFromURL(url)
    if id > 0:
        if not (id in DownloadedImage):
            DownloadedImage.add(id)
            with open("PixivDownloadedImages.txt", "a") as f:
                f.write(str(id) + '\n')
    else:
        print '[debug] log error : ' + url


################################################################################


def HandleManga(title, mag_url):
    response = opener.open(mag_url)
    html = Gzip(response.read())
    pages = re.findall('data-src="(.*?)"', html, re.S)
    totalPic = int(re.findall('<span class="total">(.*?)</span>', html, re.S)[0])
    result = True
    for i in range(len(pages)):
        if i >= totalPic:                # 按总数进行提取，以免分析到广告图片
            break
        result &= HandleImage(title, pages[i])
    return result


################################################################################


def HandleImage(title, img_url, overwrite = False):
    print '[dbg] imgUrl = ' + img_url
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
        return True

    try:
        ii = opener.open(ori_url)
        return SaveToFile(img_url, full_path, ii.read())
    except urllib2.URLError, e:
        if hasattr(e, 'code') and e.code == 404:            # 以png作为后缀重试
            try:
                new_last1 = last1[0] + '_' + last1[1] + '.png'
                ori_url = ori_url.replace(new_last, new_last1)
                title = title.replace('.jpg', '.png')

                full_path = FileSaveDirectory + ValidFileName(title)
                if IsFileExists(full_path):
                    print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
                    return True

                ii = opener.open(ori_url)
                return SaveToFile(img_url, full_path, ii.read())
            except urllib2.URLError, e:
                if hasattr(e, 'code') and e.code == 404:            # 以gif作为后缀重试
                    try:
                        new_last2 = last1[0] + '_' + last1[1] + '.gif'
                        ori_url = ori_url.replace(new_last1, new_last2)
                        title = title.replace('.png', '.gif')

                        full_path = FileSaveDirectory + ValidFileName(title)
                        if IsFileExists(full_path):
                            print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
                            return True

                        ii = opener.open(ori_url)
                        return SaveToFile(img_url, full_path, ii.read())
                    except:
                        PrintUrlErrorMsg(e)
                else:
                    PrintUrlErrorMsg(e)
        else:
            PrintUrlErrorMsg(e)
        return False


def HandleGif(title, zip_url):
    print "[Debug] zip_url %s" %(zip_url)

    tmp = zip_url.split('/')[-1].split(".")[0]
    name = tmp + title + '.zip'

    full_path = FileSaveDirectory + ValidFileName(name)
    if IsFileExists(full_path):
        print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
        return True

    ii = opener.open(zip_url)
    return SaveToFile(zip_url, full_path, ii.read())


################################################################################


def SaveImage(img):
    slashPos = img.originalImgUrl.rfind('/')
    dotPos = img.originalImgUrl.rfind('.')
    title = img.originalImgUrl[slashPos+1:dotPos] # illustId_pX 部分
    title += '_'
    title += img.title
    title += img.originalImgUrl[dotPos:len(img.originalImgUrl)]

    full_path = FileSaveDirectory + ValidFileName(title)
    if IsFileExists(full_path):
        print (u'已存在文件 ' + full_path + u', 跳过').encode('GB18030')
        return True

    try:
        ii = opener.open(img.originalImgUrl)
        return SaveToFile(img.originalImgUrl, full_path, ii.read())
    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def GetIllustPageType(img):
    img.type = 'unknown'

    js = re.findall('\(({token: ".*?})\);</script>', img.webContent, re.S)
    if len(js) == 0:
        print '[dbg] error main data not found'
        return 'unknown'

    # 去除干扰, 其他推荐的插画属性中也有 pageCount 字段
    removePart = re.findall('"userIllusts":{.*?"likeData":false,', js[0], re.S)
    if len(removePart) == 0:
        print '[dbg] removePart not found'
    for remove in removePart:
        js[0] = js[0].replace(remove, '')

    # 去除干扰, 延伸作品的插画属性中也有 illustType 字段
    removePart = re.findall('"imageResponseData":\[.*?\]', js[0], re.S)
    for remove in removePart:
        js[0] = js[0].replace(remove, '')


    pageCount = re.findall('"pageCount":([\d]+),', js[0], re.S)
    illustType = re.findall('"illustType":([\d]+)', js[0], re.S)
    if len(pageCount) != 1 or len(illustType) != 1:
        print "[dbg] error 'pageCount' or 'illustType'"
        return 'unknown'

    illustId = re.findall('"illustId":"([\d]+)"', js[0], re.S)
    if len(illustId) != 1:
        print '[dbg] error illustId'
        return 'unknown'

    img.illustId = int(illustId[0])

    url = re.findall('"original":"(.*?)"', js[0])
    if len(url) == 0:
        print '[dbg] error original url'
    img.originalImgUrl = url[0].replace('\\', '')

    if int(illustType[0]) == 0 or int(illustType[0]) == 1:
        if int(pageCount[0]) == 1:
            img.pageCount = 1
            img.type = 'single'
        elif int(pageCount[0]) > 1:
            img.pageCount = int(pageCount[0])
            img.type = 'manga'
    elif int(illustType[0]) == 2:
        img.type = 'gif'

    print '[dbg] illustType=%d, pageCount=%d' % (int(illustType[0]), int(pageCount[0]))
    return img.type


################################################################################


def ParsePage(opener, url):
    print '[Debug]: open ' + url
    img = ImgInfo()
    img.webUrl = url
    try:
        response = opener.open(url)
        img.webContent = Gzip(response.read())

        tmp = re.findall("<title>「(.*?)」.*?</title>", img.webContent, re.S)
        img.title = tmp[0].decode("utf-8")

        type = GetIllustPageType(img)
        if type == 'manga':
            return HandleManga(img.title, url.replace("medium", "manga"))
        elif type == 'gif':
            zipUrl = img.originalImgUrl
            zipUrl = zipUrl.replace('img-original', 'img-zip-ugoira')
            lastPart = zipUrl[zipUrl.rfind('/')+1:len(zipUrl)]      # 提取最后文件id相关部分，如 65922304_ugoira0.jpg
            newLastPart = lastPart[0:lastPart.find('_')+1]
            newLastPart += 'ugoira1920x1080.zip'    # 1920x1080 代表原始gif, 600x600 代表缩小后的 gif, 所以固定用最大的即可
            zipUrl = zipUrl.replace(lastPart, newLastPart)
            return HandleGif(img.title, zipUrl)
        elif type == 'single':
            return SaveImage(img)
        else:
            print '[wrn] parse page error - ' + url

    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def GetIllustationListViaPixivId(opener, pid):
    # 获取一个画师的所有插画
    print "[Debug] process Id: %s" %(pid)

    page_url = "http://www.pixiv.net/member_illust.php?id=%s" %(pid)
    img_list = []

    # 第一页
    try:
        response = opener.open(page_url)
        html = Gzip(response.read())

        title = re.findall('<title>「(.*?)」.*?</title>', html, re.S)[0].decode('utf-8')
        global FileSaveDirectory
        FileSaveDirectory = ValidFileName(title) + ' ' + pid + '\\'
        #print FileSaveDirectory
        if not os.path.exists(FileSaveDirectory):
            os.makedirs(FileSaveDirectory)

        tmp = re.findall('<li class="image-item.?"><a href="/(.*?)"', html, re.S)
        for item in tmp:
            img_list.append(MainPage + item.replace("amp;", ""))

    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        return

    page_cnt = 2
    while (re.findall('<span class="next"><a href=', html, re.S)):
        # 后续
        page_url = "http://www.pixiv.net/member_illust.php?id=%s&type=all&p=%d" %(pid, page_cnt)
        try:
            response = opener.open(page_url)
            html = Gzip(response.read())
            tmp = re.findall('<li class="image-item.?"><a href="/(.*?)"', html, re.S)      # MainPage带有一个正斜杠, 这里少配一个
            for item in tmp:
                img_list.append(MainPage + item.replace("amp;", ""))

        except urllib2.URLError, e:
            PrintUrlErrorMsg(e)
            return
        page_cnt += 1

    for url in img_list:
        id = GetIllustIdFromURL(url)
        if id > 0 and (id in DownloadedImage):
            print u'id %d 已下载.' %(id)
            continue

        result = 0
        for retry in range(3):
            result = ParsePage(opener, url)
            if result:
                break
            else:
                time.sleep(1)
                print '[Debug] retry'

        if not result:
            LogFailedPage(pid, url)
        else:
            LogSuccessPage(url)

        time.sleep(1)



################################################################################


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
    print u'完成，读取到%d个画师Id' %(len(list))

    for id in list:
        GetIllustationListViaPixivId(opener, id)


################################################################################


if __name__ == "__main__":
    LoadDownloadedImages()
    opener = GetOpenerFromCookie(Header)
    if not IsLoggedIn(opener):
        print "not founed cookie file or invalid cookie file, loggin..."
        opener = Login()
        global GlobalCookie
        GlobalCookie.save()
    if IsLoggedIn(opener):
        print "Login Succeess."
        GetIllustationListViaPixivIdList(opener)

    else:
        print "Login Error."


