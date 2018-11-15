# PixivSpider
基于 python2.7 写的P站爬虫
## 使用
1、在脚本的`pixiv_id`、`pixiv_password`处填入有效的P站帐号及密码<br>
2、在脚本目录下提供一个存有画师Id的文本文件`PixivIdList.txt`(格式为每行一个Id)，运行脚本即可抓取每位画师的所有插画<br>
3、其他功能有需要了再说(๑´ڡ`๑)
## 其他
1、在当前目录自动生成的文件<br>
- `PixivCookie.txt`: 保存cookies<br>
- `PixivDownloadedImages.txt`: 储存已下载的图像Id<br>
- `PixivErrorPage.txt`: 储存下载失败的链接
