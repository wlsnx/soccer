============
Soccer
============

------------
用法:
------------


scrapy crawl csqq [OPTION]


^^^^^^^^^^^^^^
配置:
^^^^^^^^^^^^^^

CLOSE_ON_IDLE::

    如果爬虫处于空闲状态，引擎就会尝试关闭爬虫，你可以将CLOSE_ON_IDLE设为False以防止爬虫因
    空闲而被关闭。无论此值是否被设置，在爬完今天的所有比赛前，爬虫 **不会** 因空闲被关闭。

DATABASE_SERVER::

    用来连接数据库服务器的字符串，格式: mysql://username:password@hostname/dataname?param=value

SCRAPE_INTERVAL::

    对一场比赛进行重复抓取，此变量为量词抓取之间的间隔，单位：秒。


