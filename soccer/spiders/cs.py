#!/usr/bin/env python
# encoding: utf-8


from scrapy import signals, Spider
import dataset
from scrapy.http import Request
from scrapy.exceptions import DontCloseSpider
from twisted.internet import reactor
from datetime import datetime, date, timedelta
from itertools import chain
import six


class MatchFinished(Exception):
    pass


class wrap_parse_match(type):

    def __new__(cls, name, bases, attrs):
        if "parse_match" in attrs and SoccerSpider in bases:
            attrs["_parse_live"] = attrs["parse_match"]
            attrs["parse_match"] = SoccerSpider._parse_match
            del SoccerSpider._parse_match
        return super(wrap_parse_match, cls).__new__(cls, name, bases, attrs)


##########################################SoccerSpider####################################################

@six.add_metaclass(wrap_parse_match)
class SoccerSpider(Spider):

    def __init__(self, mid=None, id=None, sql=None, **kwargs):
        super(SoccerSpider, self).__init__(**kwargs)
        if id:
            self.sql = self.SELECT_ONE_MATCH.format(id)
        else:
            self.sql = sql or self.SQL
        self.mid = mid
        self.tasks = 0

    @property
    def has_task(self):
        return self.tasks > 0

    def get_task(self):
        self.tasks += 1

    def task_done(self):
        self.tasks -= 1

    def wait_match(self, match):
        now = datetime.now()
        today = date(now.year, now.month, now.day)
        delta = today - match["date"]
        if delta > timedelta(0):
            return 0
        elif delta < timedelta(0):
            return -1
        match_time = match["time"]
        now = datetime.now().time()
        interval = match_time.seconds - (now.hour * 3600 + now.minute * 60 + now.second)
        return max(interval, 0)

    def wait_to_tomorrow(self):
        now = datetime.now()
        interval = 24*3600 - (now.hour*3600 + now.minute*60 + now.second) + self.SCRAPE_INTERVAL
        return interval

    def fetch(self, match, mid):
        request = Request(self.LIVE.format(mid),
                          dont_filter=True,
                          method="POST",
                          callback=self.parse_match,
                          meta=dict(match=match))
        wait_seconds = self.wait_match(match)
        if wait_seconds >= 0:
            reactor.callLater(wait_seconds,
                              self.crawler.engine.schedule,
                              request=request,
                              spider=self)
            self.get_task()

    def load_config(self):
        from soccer import settings
        reload(settings)
        self.settings.setmodule(settings)
        self.crawler.signals.connect(self.spider_idle, signals.spider_idle)
        self.SCRAPE_INTERVAL = self.crawler.settings.getint("SCRAPE_INTERVAL", 10)
        self.SERVER = self.crawler.settings.get("DATABASE_SERVER")
        self.db = dataset.connect(self.SERVER)
        self.matches = list(self.db.query(self.sql))
        self.CLOSE_ON_IDLE = self.crawler.settings.getbool("CLOSE_ON_IDLE", True)

    def generate_requests(self):
        """It must return an iterable object"""
        yield

    def start_requests(self):
        self.load_config()
        reactor.callLater(self.wait_to_tomorrow(),
                          self.restart)
        #self.crawler.signals.connect(self.spider_idle,
                                     #signals.spider_idle)
        for request in chain(self.generate_requests(),
                             super(SoccerSpider, self).start_requests()):
            if request:
                yield request

    def restart(self):
        for request in self.start_requests():
            self.crawler.engine.schedule(request=request,
                                         spider=self)

    def _parse_match(self, response):
        """It will repeat every <self.SCRAPE_INTERVAL> seconds"""
        self.task_done()
        try:
            for item in self._parse_live(response):
                yield item
            reactor.callLater(self.SCRAPE_INTERVAL,
                              self.crawler.engine.schedule,
                              request=response.request,
                              spider=self)
            self.get_task()
        except MatchFinished:
            pass
        except Exception as e:
            self.log(e)

    def spider_idle(self, spider):
        """This spider will not close if it has any tasks or you set CLOSE_ON_IDLE to False"""
        if spider is not self:
            return
        if not self.CLOSE_ON_IDLE:
            raise DontCloseSpider("This spider will not stopped while idle")
        elif self.has_task:
            raise DontCloseSpider("This spider has tasks now")


