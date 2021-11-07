# -*- coding: utf-8 -*-
import urllib.request, urllib.parse, urllib.error
import urllib.request, urllib.error, urllib.parse
import http.cookiejar
import re
import queue
import string
import _thread
import threading
import time
import os
import sys
import io
import json
import platform

import demjson

import log
import db
import utils
import conf

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
        self.jsonStr=''
        self.jsonData=''


MainPage = "http://www.pixiv.net/"
LoginPage = "https://accounts.pixiv.net/login"
LoginPage_Post = "https://accounts.pixiv.net/api/login?lang=zh"
pixiv_url_login_post = "https://accounts.pixiv.net/api/login"

USER_AGENT = 'Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Mobile Safari/537.36'

# 在 GetIllustationListViaPixivId 中修改，用以控制保存文件路径
FileSaveDirectory = ''



Logindata = {
    'pixiv_id':'',
    'password':'',
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
    'User-Agent': USER_AGENT
}

Proxy = urllib.request.ProxyHandler({'http': '127.0.0.1:8087'})


################################################################################


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
    if os.path.exists(conf.GetCookiePath()):
        os.remove(conf.GetCookiePath())
    global GlobalCookie
    GlobalCookie = http.cookiejar.MozillaCookieJar(conf.GetCookiePath())
    cp = urllib.request.HTTPCookieProcessor(GlobalCookie)
    op = urllib.request.build_opener(cp)
    h = []
    for key, value in list(header.items()):
        elem = (key, value)
        h.append(elem)
    op.addheaders = h
    return op


def GetOpenerFromCookie(header):
    global GlobalCookie
    GlobalCookie = http.cookiejar.MozillaCookieJar()
    if os.path.exists(conf.GetCookiePath()):
        GlobalCookie.load(conf.GetCookiePath())
    cp = urllib.request.HTTPCookieProcessor(GlobalCookie)
    op = urllib.request.build_opener(cp)
    h = []
    for key, value in list(header.items()):
        elem = (key, value)
        h.append(elem)
    op.addheaders = h
    return op


def IsLoggedIn(opener):
    res = opener.open(MainPage)
    status = re.findall('pixiv.user.loggedIn = ([\w]*);', utils.Gzip(res.read()), re.S)
    res.close()
    if len(status) > 0:
        b = re.search('true', status[0], re.IGNORECASE)
        return bool(b)
    else:
        return True


def UpdatePostKey(opener):
    response = opener.open(LoginPage)
    data = utils.Gzip(response.read())
    response.close()
    post_key = re.findall('name="post_key" value="(.*?)"', data, re.S)
    if len(post_key) == 0:
        log.warn('not found post_key! maybe is logged in.')
        return ''
    else:
        return post_key[0]


def Login():
    opener = GenerateOpener(Header)
    pixiv_key = UpdatePostKey(opener)

    post_data = {
        'pixiv_id': conf.GetAccountName(),
        'password': conf.GetAccountPwd(),
        'post_key': pixiv_key,
        'source': 'accounts'
    }
    post_data = urllib.parse.urlencode(post_data).encode('utf-8')

    try:
        op_login = opener.open(pixiv_url_login_post, post_data)
        op_login.close()
    except urllib.error.URLError as e:
        PrintUrlErrorMsg(e)
    except:
        log.exception('others error occurred while loggin.')
    else:
        return opener


################################################################################


def SaveToFile(opener, img_url, full_path, overwrite = False):
    if not overwrite and utils.IsFileExists(full_path):
        log.info('`SaveToFile` file [%s] existing, skip', img_url)
        return True
    else:
        try:
            ii = opener.open(img_url)
            length = 0
            if 'content-length' in ii.headers:
                length = int(ii.headers['content-length'])
            with open(full_path, 'wb') as o:
                o.write(ii.read())

            if length > 0 and os.path.getsize(full_path) != length:
                log.warn('saving %s imcomplete', img_url)
                os.remove(full_path)
                return False

            return True

        except urllib.error.URLError as e:
            if hasattr(e, 'code') and e.code == 404:
                log.debug('http 404: %s', img_url)
            else:
                PrintUrlErrorMsg(e)
            return False
        except:
            log.error_stack('failed saving %s to file.', img_url)
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


def HandleManga(opener, img):
    manga_list_url = 'https://www.pixiv.net/ajax/illust/%d/pages' %(img.illustId)

    values = {
        'Referer':img.webUrl,
        'User-Agent':USER_AGENT
    }

    try:
        # 获得列表
        request = urllib.request.Request(manga_list_url, headers=values)
        response = opener.open(request)

        try:
            data = response.read()
            img_id_str_list = json.loads(utils.Gzip(data))
        except IOError as e:
            log.error('error manga list of %d', img.illustId)

        index = 0
        result = True
        for i in img_id_str_list['body']:
            url = i['urls']['original']
            log.debug('manga url: %s', url)
            name = '%d_p%d_%s%s' %(img.illustId, index, utils.ValidFileName(img.title), url[url.rfind('.'):])
            log.debug('generate file name: %s', name)
            index = index + 1
            full_path = os.path.join(FileSaveDirectory, name)
            if utils.IsFileExists(full_path):
                log.info('file [%s] existing, skip', full_path)
                continue
            result &= SaveToFile(opener, url, full_path)

        return result

    except urllib.error.URLError as e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def HandleGif(opener, img):
    gif_url = 'https://www.pixiv.net/ajax/illust/%d/ugoira_meta' %(img.illustId)

    values = {
        'Referer':img.webUrl,
        'User-Agent':USER_AGENT
    }

    try:
        # 获得列表
        request = urllib.request.Request(gif_url, headers=values)
        response = opener.open(request)

        try:
            data = response.read()
            img_id_str_list = json.loads(utils.Gzip(data))
        except IOError as e:
            log.error('error gif of %d', img.illustId)
            return False

        url = img_id_str_list['body']['originalSrc']
        log.debug('gif url: %s', url)
        name = '%s_%s%s' %(url[url.rfind('/')+1:url.rfind('.')], utils.ValidFileName(img.title), url[url.rfind('.'):])
        log.debug('generate file name: %s', name)

        full_path = os.path.join(FileSaveDirectory, name)
        if utils.IsFileExists(full_path):
            log.info('file [%s] existing, skip', full_path)
            return True

        return SaveToFile(opener, url, full_path)

    except urllib.error.URLError as e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def SaveSingleImage(opener, img):
    assert(img.type == 'single' and img.pageCount == 1)

    url = img.jsonData['urls']['original']
    title = '%d_p0_%s%s' %(img.illustId, img.title, url[url.rfind('.'):])
    full_path = os.path.join(FileSaveDirectory, utils.ValidFileName(title))
    if utils.IsFileExists(full_path):
        log.info('file [%s] existing, skip', url)
        return True

    try:
        return SaveToFile(opener, url, full_path)
    except urllib.error.URLError as e:
        PrintUrlErrorMsg(e)
        return False


################################################################################


def DetermineIllustPageType(img):
    type = img.jsonData['illustType']
    img.pageCount = img.jsonData['pageCount']

    if type == 0 or type == 1:
        if img.pageCount == 1:
            img.type = 'single'
        elif img.pageCount > 1:
            img.type = 'manga'
    elif type == 2:
        img.type = 'gif'
    else:
        img.type = 'unknown'
        log.error('unknown illust type %d', type)

    log.debug('`DetermineIllustPageType` illustType=%d, pageCount=%d', type, img.pageCount)
    return


################################################################################


def DetermineIllustTags(img):
    tags = img.jsonData['tags']['tags']
    img.tags = ''
    for t in tags:
        img.tags += ',' + t['tag']

    # remove first ','
    img.tags = img.tags[1:]
    log.debug('`DetermineIllustTags` find tags = %s', img.tags)


################################################################################


def TrimImageJsonBlob(jstr):
    j = json.loads(jstr)['body']
    if 'userIllusts' in j:
        del j["userIllusts"]
    if 'fanboxPromotion' in j:
        del j["fanboxPromotion"]
    if 'extraData' in j:
        del j["extraData"]
    if 'zoneConfig' in j:
        del j["zoneConfig"]
    if 'noLoginData' in j:
        del j["noLoginData"]
    return j


def ParsePage(opener, img):
    log.debug('`ParsePage` open ' + img.webUrl)
    try:
        values = {
            'Referer': "https://www.pixiv.net/artworks/%d" %(img.illustId),
            'User-Agent': USER_AGENT
        }
        request = urllib.request.Request(img.webUrl, headers=values)
        response = opener.open(request)
        img.jsonStr = utils.Gzip(response.read())

        log.debug('`ParsePage` json = %s', img.jsonStr)
        img.jsonData = TrimImageJsonBlob(img.jsonStr)

        img.title = img.jsonData['illustTitle']
        DetermineIllustPageType(img)
        DetermineIllustTags(img)

        if img.type == 'manga':
            return HandleManga(opener, img)
        elif img.type == 'gif':
            return HandleGif(opener, img)
        elif img.type == 'single':
            return SaveSingleImage(opener, img)
        else:
            log.warn('parse page error - %s', img.webUrl)
            return False

    except urllib.error.URLError as e:
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
        img.webUrl = 'https://www.pixiv.net/ajax/illust/%d' %(img_id)
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

    page_url = "http://www.pixiv.net/users/%s" %(author_id)
    illus_list_url = 'https://www.pixiv.net/ajax/user/%s/profile/all' %(author_id)

    values = {
        'Referer':page_url,
        'User-Agent':USER_AGENT
    }

    try:
        # 获得列表
        request = urllib.request.Request(illus_list_url, headers=values)
        response = opener.open(request)

        try:
            img_id_str_list = []
            data = response.read()
            json_data = json.loads(utils.Gzip(data))
            log.debug('creator json: %s', json_data)
            for i in json_data['body']['illusts']:
                img_id_str_list.append(i)
            for i in json_data['body']['manga']:
                img_id_str_list.append(i)

        except IOError as e:
            log.info('creator %s illust is empty, maybe this ID is not valid any more', author_id)
            # img_id_str_list = json.loads(data)

        return img_id_str_list

    except urllib.error.URLError as e:
        PrintUrlErrorMsg(e)
        return []


################################################################################


def SetupSavingFolder(opener, author_id):
    # 创建储存插画的文件夹，并保存至全局变量 FileSaveDirectory
    log.debug("`SetupSavingFolder` process Id: %s", author_id)
    page_url = "http://www.pixiv.net/users/%s" %(author_id)
    try:
        response = opener.open(page_url)
        html = utils.Gzip(response.read())
        creator = db.FindCreatorInfoViaID(author_id)
        if creator['name'] is None:
            result = re.findall('<title>「(.*?)」.*?</title>', html, re.S)
            if len(result) > 0:
                title = result[0]
            else:
                title = re.findall('<title>(.*?)</title>', html, re.S)[0]
            db.UpdateCreatorName(author_id, title)
        else:
            title = creator['name']

        global FileSaveDirectory
        FileSaveDirectory = os.path.join(conf.GetDownloadsDir(), utils.ValidFileName(title) + ' ' + str(author_id))

        if not os.path.exists(FileSaveDirectory):
            os.makedirs(FileSaveDirectory)

        return True

    except urllib.error.URLError as e:
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
            if SetupSavingFolder(opener, id):
                ProcessCreator(opener, id, imgs)
                try:
                    os.rmdir(FileSaveDirectory)
                    log.info('empty folder %s removed', FileSaveDirectory)
                except OSError:
                    pass

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
        log.info('file `' + PixivDownloadedImagesFileName + '` is missing or empty, skip.')
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
        log.info('it may take a long time if there is a lot of imgs...please wait')
        newest = {}
        for id in creators_in_txt:
            time.sleep(0.5)
            illusts = GetAllIllustOfCreator(opener, id)
            log.debug('creator %d downloaded', id)
            for i in illusts:
                newest[int(i)] = int(id)
        log.info('done, start import...')

        to_db = []
        some_failed = False
        for img in illust_in_txt:
            if int(img) in newest:
                to_db.append((int(img), newest[int(img)],))
            else:
                some_failed = True
                log.info('cannot find illust %d info on web, please add manually', int(img))
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
        log.debug('************************** log start **************************')

        if len(sys.argv) > 1:
            if sys.argv[1] == '--import':
                ImportOldDataToDB()
            else:
                log.info('unknown argument: ' + ' '.join(sys.argv))
        else:
            NormalDownload()
    except:
        log.exception('unhandled exception.')

