# -*- coding: utf-8 -*-

import os
import sqlite3

import log
import conf

g_db = None


def InitDB():
    if not os.path.exists(conf.GetDBDefinePath()):
        log.exception('`%s` is missing!', conf.GetDBDefinePath())

    with open(conf.GetDBDefinePath()) as f:
        GetDB().executescript(f.read())


def CloseDB():
    global g_db
    if g_db is not None:
        g_db.close()
        g_db = None
        log.debug('db is closed.')


def GetDB():
    global g_db
    if not g_db:
        exist = os.path.exists(conf.GetDBPath())
        g_db = sqlite3.connect(
            conf.GetDBPath(),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g_db.row_factory = sqlite3.Row
        if not exist:
            try:
                InitDB()
            except:
                CloseDB()
                os.remove(conf.GetDBPath())
                raise

    return g_db


###############################################################################
# table `creator`

def AddCreatorID(list):
    db = GetDB()
    sql = 'INSERT INTO creator (id) VALUES (?);'
    data = []
    for id in list:
        data.append((id,))
    db.executemany(sql, data)
    db.commit()


def FindCreatorInfoViaID(id):
    creator = GetDB().execute(
        'SELECT id, name, add_time FROM creator WHERE id = ?',
        (id,)
    ).fetchone()
    return creator


def UpdateCreatorName(id, name):
    db = GetDB()
    db.execute('UPDATE creator SET name = ? WHERE id = ?', (name, id,))
    db.commit()
    log.debug('db.UpdateCreatorName %d', id)


def GetAllCreatorID():
    db = GetDB()
    all = db.execute('SELECT id FROM creator').fetchall()
    auth = []
    for i in all:
        auth.append(i['id'])
    return auth


###############################################################################
# table `illust`

def AddIllustList(list):
    db = GetDB()
    sql = 'INSERT INTO illust (id, author_id) VALUES (?,?);'
    db.executemany(sql, list)
    db.commit()


def IsIllustExist(id):
    illust = GetDB().execute('SELECT id FROM illust WHERE id = ?', (id,)).fetchone()
    return illust != None


def AddSuccessIllustRecord(img):
    db = GetDB()
    db.execute(
        'INSERT INTO illust(id, author_id, name, type, tags, sub_img_count) VALUES (?, ?, ?, ?, ?, ?)',
        (img.illustId, img.authorId, img.title, img.type, img.tags, img.pageCount,)
    )
    db.commit()
    log.debug('db.AddSuccessIllustRecord %d', img.illustId)
    # duplicate id ??


def GetAllIllustID():
    db = GetDB()
    all = db.execute('SELECT id FROM illust').fetchall()
    imgs = set()
    for i in all:
        imgs.add(i['id'])
    return imgs


###############################################################################
# table `download_failed`

def AddFailedIllustRecord(img):
    db = GetDB()
    rec = db.execute('SELECT * FROM download_failed WHERE illust_id = ?', (img.illustId,)).fetchone()
    if rec is not None:
        db.execute(
            'UPDATE download_failed SET last_time = CURRENT_TIMESTAMP WHERE illust_id = ?',
            (img.illustId,)
        )
        db.commit()
        log.debug('db.AddFailedIllustRecord old image %d', img.illustId)
    else:
        db.execute(
            'INSERT INTO download_failed(illust_id, author_id, url, last_time) VALUES (?, ?, ?, CURRENT_TIMESTAMP)',
            (img.illustId, img.authorId, img.webUrl,)
        )
        db.commit()
        log.debug('db.AddFailedIllustRecord new image %d', img.illustId)


def RemoveFailedIllustRecord(img):
    db = GetDB()
    db.execute('DELETE FROM download_failed WHERE illust_id = ?', (img.illustId,))
    db.commit()
    log.debug('db.RemoveFailedIllustRecord %d', img.illustId)

