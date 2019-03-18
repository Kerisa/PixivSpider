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
import json
import platform

# for gzip
import gzip
from StringIO import StringIO


import log
import db
import utils

class ImgInfo:
    def __init__(self):
        self.webUrl=''
        self.webContent=''
        self.originalImgUrl=''
        self.title=''
        self.tags=''
        self.pageCount=0
        self.illustId=0
        self.authorId=0
        self.type=''


MainPage = "http://www.pixiv.net/"
LoginPage = "https://accounts.pixiv.net/login"
LoginPage_Post = "https://accounts.pixiv.net/api/login?lang=zh"
pixiv_url_login_post = "https://accounts.pixiv.net/api/login"

CookieFileName = 'PixivCookie.txt'

SYSTEM_PATH_DIVIDER = '/'
if platform.system() == 'Windows':
    SYSTEM_PATH_DIVIDER = '\\'

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
Proxy = urllib2.ProxyHandler({'http': '127.0.0.1:8087'})




def PrintUrlErrorMsg(e):
    if hasattr(e, 'reason'):
        if hasattr(e, 'code'):
            log.info('[URLError] reason: ' + str(e.reason) + ', code: ' + str(e.code))
        else:
            log.info('[URLError] reason: ' + str(e.reason))
    elif hasattr(e, 'code'):
        log.info('[URLError] code: ' + str(e.code))
    else:
        log.info('[URLError] Unkonwn reason.')


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
    status = re.findall('pixiv.user.loggedIn = ([\w]*);', utils.Gzip(res.read()), re.S)
    res.close()
    assert len(status) > 0
    b = re.search('true', status[0], re.IGNORECASE)
    return bool(b)


def UpdatePostKey(opener):
    response = opener.open(LoginPage)
    data = utils.Gzip(response.read())
    response.close()
    post_key = re.findall('name="post_key" value="(.*?)"', data, re.S)
    if len(post_key) == 0:
        log.warn('not found post_key! maybe is logged in.')
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
        log.exception('others error occurred while loggin.')
    else:
        return opener


################################################################################


def SaveToFile(img_url, full_path, overwrite = False):
    if not overwrite and utils.IsFileExists(full_path):
        log.info('`SaveToFile` file [%s] existing, skip', img_url)
        return True
    else:
        try:
            ii = opener.open(img_url)
            length = 0
            if ii.headers.has_key('content-length'):
                length = int(ii.headers['content-length'])
            with open(full_path, 'wb') as o:
                o.write(ii.read())

            if length > 0 and os.path.getsize(full_path) != length:
                log.warn('saving %s imcomplete', img_url)
                os.remove(full_path)
                return False

            return True

        except urllib2.URLError, e:
            if hasattr(e, 'code') and e.code == 404:
                log.debug('http 404: %s', img_url)
            else:
                PrintUrlErrorMsg(e)
            return False
        except:
            log.warn('failed saving %s to file.', img_url)
            if utils.IsFileExists(full_path, withSize = False):
                os.remove(full_path)
            return False



################################################################################

DownloadedImage = set()

def LoadDownloadedImages():
    global DownloadedImage
    DownloadedImage = db.GetAllIllustID()
    log.info('download list loading success, got %d downloaded illust ID', len(DownloadedImage))


def LogFailedPage(img):
    assert img.illustId > 0 and img.authorId > 0
    db.AddFailedIllustRecord(img)
    log.debug('failed illust %d logged.', img.illustId)


def LogSuccessPage(img):
    assert img.illustId > 0
    if not (img.illustId in DownloadedImage):
        DownloadedImage.add(img.illustId)
        db.AddSuccessIllustRecord(img)
        db.RemoveFailedIllustRecord(img)
        log.info('image %d downloaded.', img.illustId)


################################################################################


def HandleManga(title, mag_url):
    response = opener.open(mag_url)
    html = utils.Gzip(response.read())
    pages = re.findall('data-src="(.*?)"', html, re.S)
    totalPic = int(re.findall('<span class="total">(.*?)</span>', html, re.S)[0])
    result = True
    for i in range(len(pages)):
        if i >= totalPic:                # 按总数进行提取，以免分析到广告图片
            break
        result &= HandleMangaImage(title, pages[i])
    return result


################################################################################


def HandleMangaImage(title, img_url, overwrite = False):
    log.debug('HandleMangaImage url = ' + img_url)
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

    full_path = FileSaveDirectory + utils.ValidFileName(title)
    if utils.IsFileExists(full_path):
        log.info('`HandleMangaImage` file [%s] existing, skip', img_url)
        return True

    if not SaveToFile(ori_url, full_path):
        # 以png作为后缀重试
        new_last1 = last1[0] + '_' + last1[1] + '.png'
        ori_url = ori_url.replace(new_last, new_last1)
        title = title.replace('.jpg', '.png')

        log.debug('retry png: ' + ori_url)
        full_path = FileSaveDirectory + utils.ValidFileName(title)
        if utils.IsFileExists(full_path):
            log.info('`HandleMangaImage` file [%s] existing, skip', ori_url)
            return True

        if not SaveToFile(ori_url, full_path):
            # 以gif作为后缀重试
            new_last2 = last1[0] + '_' + last1[1] + '.gif'
            ori_url = ori_url.replace(new_last1, new_last2)
            title = title.replace('.png', '.gif')

            log.debug('retry gif: ' + ori_url)
            full_path = FileSaveDirectory + utils.ValidFileName(title)
            if utils.IsFileExists(full_path):
                log.info('`HandleMangaImage` file [%s] existing, skip', ori_url)
                return True

            return SaveToFile(ori_url, full_path)
        else:
            return True
    else:
        return True


def HandleGif(title, zip_url):
    log.debug('HandleGif url %s', zip_url)

    tmp = zip_url.split('/')[-1].split(".")[0]
    name = tmp + title + '.zip'

    full_path = FileSaveDirectory + utils.ValidFileName(name)
    if utils.IsFileExists(full_path):
        log.info('zip file [%s] existing, skip', zip_url)
        return True

    return SaveToFile(zip_url, full_path)


################################################################################


def SaveSingleImage(img):
    slashPos = img.originalImgUrl.rfind('/')
    dotPos = img.originalImgUrl.rfind('.')
    title = img.originalImgUrl[slashPos+1:dotPos] # illustId_pX 部分
    title += '_'
    title += img.title
    title += img.originalImgUrl[dotPos:len(img.originalImgUrl)]

    full_path = FileSaveDirectory + utils.ValidFileName(title)
    if utils.IsFileExists(full_path):
        log.info('file [%s] existing, skip', img.originalImgUrl)
        return True

    try:
        return SaveToFile(img.originalImgUrl, full_path)
    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def DetermineIllustPageType(img):
    img.type = 'unknown'

    js = re.findall('\(({token: ".*?})\);</script>', img.webContent, re.S)
    if len(js) == 0:
        log.debug('`DetermineIllustPageType` error main data not found')
        return

    # 去除干扰, 其他推荐的插画属性中也有 pageCount 字段
    removePart = re.findall('"userIllusts":{.*?"likeData":false,', js[0], re.S)
    if len(removePart) == 0:
        log.warn('`DetermineIllustPageType` removePart not found')
    for remove in removePart:
        js[0] = js[0].replace(remove, '')

    # 去除干扰, 延伸作品的插画属性中也有 illustType 字段
    removePart = re.findall('"imageResponseData":\[.*?\]', js[0], re.S)
    for remove in removePart:
        js[0] = js[0].replace(remove, '')


    pageCount = re.findall('"pageCount":([\d]+),', js[0], re.S)
    illustType = re.findall('"illustType":([\d]+)', js[0], re.S)
    if len(pageCount) != 1 or len(illustType) != 1:
        log.warn("`DetermineIllustPageType` error 'pageCount' or 'illustType'")
        return

    illustId = re.findall('"illustId":"([\d]+)"', js[0], re.S)
    if len(illustId) != 1:
        log.warn('`DetermineIllustPageType` error illustId')
        return

    #img.illustId = int(illustId[0])

    url = re.findall('"original":"(.*?)"', js[0])
    if len(url) == 0:
        log.warn('`DetermineIllustPageType` error original url')
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

    log.debug('`DetermineIllustPageType` illustType=%d, pageCount=%d', int(illustType[0]), int(pageCount[0]))
    return


################################################################################


def DetermineIllustTags(img):
    tags = re.findall('"tag":"(.*?)",', img.webContent, re.S)
    assert len(tags) >= 1
    img.tags = ''
    for t in tags:
        img.tags += ',' + t.decode('unicode-escape')
    img.tags = img.tags[1:]
    log.debug('`DetermineIllustTags` find tags = %s', img.tags)


################################################################################


def ParsePage(opener, img):
    log.debug('`ParsePage` open ' + img.webUrl)
    try:
        response = opener.open(img.webUrl)
        img.webContent = utils.Gzip(response.read())

        tmp = re.findall("<title>.*?「(.*?)」.*?</title>", img.webContent, re.S)
        img.title = tmp[0].decode("utf-8")

        DetermineIllustPageType(img)
        DetermineIllustTags(img)

        if img.type == 'manga':
            url = img.webUrl
            return HandleManga(img.title, url.replace("medium", "manga"))
        elif img.type == 'gif':
            zipUrl = img.originalImgUrl
            zipUrl = zipUrl.replace('img-original', 'img-zip-ugoira')
            lastPart = zipUrl[zipUrl.rfind('/')+1:len(zipUrl)]      # 提取最后文件id相关部分，如 65922304_ugoira0.jpg
            newLastPart = lastPart[0:lastPart.find('_')+1]
            newLastPart += 'ugoira1920x1080.zip'    # 1920x1080 代表原始gif, 600x600 代表缩小后的 gif, 所以固定用最大的即可
            zipUrl = zipUrl.replace(lastPart, newLastPart)
            return HandleGif(img.title, zipUrl)
        elif img.type == 'single':
            return SaveSingleImage(img)
        else:
            log.warn('parse page error - %s', img.webUrl)

    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def ProcessCreator(opener, author_id, imgs):
    # 下载
    log.debug("`ProcessCreator` Id: %s", author_id)

    assert FileSaveDirectory.find(str(author_id)) != -1, 'should call `SetupSavingFolder` first'

    for si in imgs:
        img_id = int(si)
        if img_id > 0 and (img_id in DownloadedImage):
            log.info('image %d already downloaded, continue.', img_id)
            continue

        img = ImgInfo()
        img.illustId = img_id
        img.authorId = author_id
        img.webUrl = 'https://www.pixiv.net/member_illust.php?mode=medium&illust_id=%d' %(img_id)
        result = 0

        for retry in range(3):
            result = ParsePage(opener, img)
            if result:
                break
            else:
                time.sleep(1)
                log.info('retry %d, time %d', img_id, retry + 1)

        if not result:
            LogFailedPage(img)
        else:
            LogSuccessPage(img)

        time.sleep(1)


################################################################################


def GetAllIllustOfCreator(opener, author_id):
    # 获取一位画师的所有插画
    log.debug("`GetAllIllustOfCreator` process Id: %s", author_id)

    page_url = "http://www.pixiv.net/member.php?id=%s" %(author_id)
    illus_list_url = 'https://www.pixiv.net/touch/ajax/illust/user_illusts?user_id=%s' %(author_id)

    values = {
        'Referer':page_url,
        'User-Agent':'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Mobile Safari/537.36'
    }

    try:
        # 获得列表
        request = urllib2.Request(illus_list_url, headers=values)
        response = opener.open(request)

        try:
            data = response.read()
            img_id_str_list = json.loads(utils.Gzip(data))
        except IOError, e:
            log.debug('creator %s illust list not json data, try as plain data', author_id)
            img_id_str_list = json.loads(data)

        return img_id_str_list

    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        return []


################################################################################


def SetupSavingFolder(opener, author_id):
    # 创建储存插画的文件夹，并保存至全局变量 FileSaveDirectory
    log.debug("`SetupSavingFolder` process Id: %s", author_id)
    page_url = "http://www.pixiv.net/member.php?id=%s" %(author_id)
    try:
        response = opener.open(page_url)
        html = utils.Gzip(response.read())
        creator = db.FindCreatorInfoViaID(author_id)
        if creator['name'] is None:
            title = re.findall('<title>「(.*?)」.*?</title>', html, re.S)[0].decode('utf-8')
            db.UpdateCreatorName(author_id, title)
        else:
            title = creator['name']

        global FileSaveDirectory
        FileSaveDirectory = 'downloads' + SYSTEM_PATH_DIVIDER + utils.ValidFileName(title) + ' ' + str(author_id) + SYSTEM_PATH_DIVIDER

        if not os.path.exists(FileSaveDirectory):
            os.makedirs(FileSaveDirectory)

        return True

    except urllib2.URLError, e:
        PrintUrlErrorMsg(e)
        log.info('create saving folder [%s] failed.', FileSaveDirectory)
        return False


################################################################################


def CreateOpener():
    log.info('init connection...')
    opener = GetOpenerFromCookie(Header)
    if not IsLoggedIn(opener):
        log.info('cookie file not found or invalid, loggin...')
        opener = Login()
        global GlobalCookie
        GlobalCookie.save()

    if IsLoggedIn(opener):
        log.info('login Succeess.')
        return opener
    else:
        log.info('login Error.')
        return None


################################################################################


def NormalDownload():
    LoadDownloadedImages()

    creators = db.GetAllCreatorID()
    log.info('%d creators ID read', len(creators))

    opener = CreateOpener()
    if opener is not None:
        for id in creators:
            imgs = GetAllIllustOfCreator(opener, id)
            SetupSavingFolder(opener, id)
            ProcessCreator(opener, id, imgs)

    log.info('download finish.')


################################################################################


def ImportOldDataToDB():
    PixivIdListFileName = "PixivIdList.txt"
    PixivDownloadedImagesFileName = "PixivDownloadedImages.txt"

    creators_in_txt = set()
    if not utils.IsFileExists(PixivIdListFileName):
        log.info('file `' + PixivIdListFileName + '` is missing or empty, skip')
        # 使用数据库中的画师 ID
        creators_in_txt = db.GetAllCreatorID()
    else:
        # 读取 txt 中的画师 ID
        with open(PixivIdListFileName, "r") as f:
            line = f.readline()
            while line:
                line = line.strip('\r\n')
                line = line.strip('\n')
                line = line.strip('\r')
                if line != '':
                    creators_in_txt.add(int(line))
                line = f.readline()

        log.debug('read list' + str(creators_in_txt))
        log.info('read %d ID', len(creators_in_txt))
        db.AddCreatorID(creators_in_txt)
        log.info('import creator ID success.')
        os.rename(PixivIdListFileName, PixivIdListFileName + '.bak')
        log.info('rename `%s` to `%s`', PixivIdListFileName, PixivIdListFileName + '.bak')

    # 读取 txt 中的插画 ID
    if not utils.IsFileExists(PixivDownloadedImagesFileName):
        log.info('file' + PixivIdListFileName + 'is missing or empty, skip.')
    else:
        illust_in_txt = set()
        with open(PixivDownloadedImagesFileName, "r") as f:
            line = f.readline()
            while line:
                illust_in_txt.add(int(line.strip('\n')))
                line = f.readline()
        log.info('read %d downloaded illusts', len(illust_in_txt))

        opener = CreateOpener()
        if opener is None:
            log.info('stop import illust.')
            return

        # 获取所有画师的作品集
        log.info('it may take a long time if there is a lot of imgs...')
        newest = {}
        for id in creators_in_txt:
            time.sleep(0.7)
            illusts = GetAllIllustOfCreator(opener, id)
            log.debug('creator %d downloaded', id)
            print(illusts)
            log.debug(illusts)
            for i in illusts:
                newest[int(i)] = int(id)
        log.info('done, start import...')
        print(newest)
        to_db = []
        some_failed = False
        for img in illust_in_txt:
            if newest.has_key(int(img)):
                to_db.append((int(img), newest[int(img)],))
            else:
                some_failed = True
                log.debug('cannot find illust %d info on web, please add manually', int(img))
        if some_failed:
            log.info('some illust cannot find on web, read log for detail')
        log.info('import to db')
        db.AddIllustList(to_db)
        log.info('import illust success')
        os.rename(PixivDownloadedImagesFileName, PixivDownloadedImagesFileName + '.bak')
        log.info('rename `%s` to `%s`', PixivDownloadedImagesFileName, PixivDownloadedImagesFileName + '.bak')

    log.info('import finish')

################################################################################


if __name__ == "__main__":
    try:
        log.InitLogger()

        if len(sys.argv) > 1:
            if sys.argv[1] == '--import':
                ImportOldDataToDB()
            else:
                log.info('unknown argument: ' + ' '.join(sys.argv))
        else:
            NormalDownload()
    except:
        log.exception('unhandled exception.')

