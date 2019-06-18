# PixivSpider
基于 python3.7 写的P站爬虫
## 使用
1 . 在 pixivspider-data\config.ini 的 `pixiv_id`、`pixiv_password` 处填入有效的P站帐号及密码  
2 . 添加画师 ID  
 - 首先运行一次脚本，在 `pixivspider-data` 子目录中会自动初始化一个空的数据库文件 `download.db`，使用 `DB Browser for SQLite`(https://sqlitebrowser.org/dl/) 打开数据库中的 `creator` 数据表，在 `id` 列中添加画师的 ID 即可  
 - 或在 `pixivspider` 文件夹所在目录下提供一个存有画师 ID 的文本文件 `PixivIdList.txt`(格式为每行一个 ID)，运行 `python pixivspider --import` 命令进行导入  

3 . P 站在国内已经需要挂梯子访问了，所以需要自行解决梯子问题（推荐扔到外网机器上下载）  
4 . 执行 `python pixivspider` 即可开始抓取每位画师的所有插画，下载成功和下载失败的插画会分别记录到数据库中的 `illust` 表和 `download_failed` 表  
5 . 其他功能有需要了再说(๑´ڡ`๑)  
## 导入
使用 `--import` 参数可导入原有记录文件 `PixivIdList.txt` 和 `PixivDownloadedImages.txt` 中的数据，导入前确认数据库中没有相应的记录以免冲突，最好直接导入到空的库中。至于 `PixivErrorPage.txt` 因为每次对未下载的文件都会重新尝试，所以这个记录就不需要导入了。
## 其他
1 . python 需要安装 demjson 依赖
2 . 在用户数据目录 `pixivspider-data` 下自动生成的文件<br>
- `PixivCookie.txt`: 保存cookies<br>
- `record.log`: 日志<br>
- `download.db`: 数据库<br>
- `downloads`: 下载插画保存目录
