# PixivSpider
基于 python2.7 写的P站爬虫
## 使用
1 . 在脚本的 `pixiv_id`、`pixiv_password` 处填入有效的P站帐号及密码  
2 . 添加画师 ID  
 - 首先运行一次脚本，在当前目录下会自动初始化一个空的数据库文件 `download.db`，使用 `DB Browser for SQLite`(https://sqlitebrowser.org/dl/)打开数据库中 `creator` 数据表，在 `id` 列中添加画师的 ID 即可  
 - 或在脚本目录下提供一个存有画师 ID 的文本文件 `PixivIdList.txt`(格式为每行一个 ID)，使用 `PixivSpider.py --import` 命令进行导入  

3 . P 站已经需要挂梯子访问了，所以需要自行解决梯子问题（推荐扔到 vps 上下载）  
4 . 运行脚本即可抓取每位画师的所有插画，下载成功和下载失败的插画会分别记录到数据库中的 `illust` 表和 `download_failed` 表  
5 . 其他功能有需要了再说(๑´ڡ`๑)  
## 其他
1、在当前目录自动生成的文件<br>
- `PixivCookie.txt`: 保存cookies<br>
- `record.log`: 日志<br>
- `download.db`: 数据库<br>