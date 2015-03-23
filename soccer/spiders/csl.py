#!/usr/bin/env python
# encoding: utf-8


import dataset
from scrapy.http import Request
from scrapy import signals, Spider
from scrapy.exceptions import DontCloseSpider
from scrapy.contrib.loader import ItemLoader
from soccer.items import Match, Football, FootballDetail
from twisted.internet import reactor
import json
from datetime import datetime, date, timedelta
from itertools import chain


SQL = "SELECT id,home,away,date,time FROM `match` WHERE finish <> 2 AND date=DATE(NOW()) AND league='cn'"
MATCH_LIST = "http://mat1.gtimg.com/apps/test2/web_shasha_208_new.json"
MATCH_DATA = "http://sportswebapi.qq.com/match/view?competitionId=208&matchId={0}"
LIVE = "http://soccerdata.sports.qq.com/s/live.action?mid={0}"
SELECT_ONE_MATCH = "SELECT id,home,away,date,time FROM `match` WHERE id={0} LIMIT 1"
SHORTCUT = {
    "corner": "c",
    "shots": "so",
    "yellow_card": "yb",
    "red_card": "rb",
    "offside": "o",
    "ball_possession": "pp",
    "fouls": "f",
    "shot": "s",
}
MATCH_STATUS = {
    "fulltime": 2,
    "prematch": 0,
}


class CslSpider(Spider):
    name="csl"
    allowed_domains = ["sports.qq.com"]

    def __init__(self, id=None, mid=None, sql=None):
        self.mid = mid
        if not sql and id:
            self.sql = SELECT_ONE_MATCH.format(id)
        else:
            self.sql = sql or SQL
        self.match_list_url = MATCH_LIST
        self.match_data_url = MATCH_DATA
        self.live = LIVE

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
        interval = 24 * 3600 - (now.hour * 3600 + now.minute * 60 + now.second) + self.scrape_interval
        return interval

    def fetch(self, match, mid):
        request = Request(self.live.format(mid),
                          dont_filter=True,
                          method="POST",
                          callback=self.parse_live,
                          meta=dict(match=match))
        wait_seconds = self.wait_match(match)
        if wait_seconds >= 0:
            reactor.callLater(wait_seconds,
                              self.crawler.engine.schedule,
                              request=request,
                              spider=self)

    def load_config(self):
        self.crawler.signals.connect(self.spider_idle, signals.spider_idle)
        self.scrape_interval = self.crawler.settings.getint("SCRAPE_INTERVAL", 10)
        self.server = self.crawler.settings.get("DATABASE_SERVER")
        self.db = dataset.connect(self.server)
        self.matches = list(self.db.query(self.sql))
        self.close_on_idle = self.crawler.settings.getbool("CLOSE_ON_IDLE", True)

    def start_requests(self):
        self.load_config()
        reactor.callLater(self.wait_to_tomorrow(), self.start_requests)
        if self.mid:
            match = self.matches[0]
            self.fetch(match, self.mid)
            return
        else:
            return self.generate_requests()

    def parse(self, response):
        pass

    def generate_requests(self):
        yield Request(MATCH_LIST,
                      callback=self.parse_match_list)

    def same_match(self,tmatch, match):
        return str(match["date"]) in tmatch["startTime"] and \
            tmatch["homeName"] in match["home"] and \
            tmatch["awayName"] in match["away"]

    def parse_match_list(self, response):
        match_list = json.loads(response.body[21:][:-1])
        matches = [m for match in match_list["matches"].values() for m in match]
        for match in self.matches:
            for tmatch in matches:
                if self.same_match(tmatch, match):
                    self.fetch(match, tmatch["matchId"])
                    break
            else:
                self.task_done(match)

    def parse_live(self, response):
        live = json.loads(response.body)
        match = response.meta["match"]
        resultinfo = live["resultinfo"]
        home_player = resultinfo["lineup"]["home"]["player"]
        away_player = resultinfo["lineup"]["away"]["player"]
        player_list = {player["id"]: player for player in chain(home_player, away_player)}
        #home_player = {player["id"]: player for player in home_player}
        #away_player = {player["id"]: player for player in away_player}
        home_substitution = resultinfo["substitution"]["home"].get("player", [])
        away_substitution = resultinfo["substitution"]["away"].get("player", [])
        home_goal = resultinfo["goal"]["home"].get("player", [])
        away_goal = resultinfo["goal"]["away"].get("player", [])
        home_booking = resultinfo["booking"]["home"].get("player", [])
        away_booking = resultinfo["booking"]["away"].get("player", [])
        stat = resultinfo["stat"]

        #parse match
        period = stat["period"]
        finish = MATCH_STATUS.get(period, 1)

        match_loader = ItemLoader(Match())

        match_loader.add_value("id", match["id"])
        match_loader.add_value("home_scores", stat["homescore"])
        match_loader.add_value("away_scores", stat["awayscore"])
        match_loader.add_value("finish", finish)
        match_loader.add_value("m_time", stat["time"])

        yield match_loader.load_item()

        #parse goal
        def parse_goal(goal_list, team1, team2):
            for goal in goal_list:
                pid, gtype, gtime = goal["id"], goal["type"], goal["time"]
                if gtype == "own":
                    gtype = 5
                    team = team2
                else:
                    gtype = 1
                    team = team1
                player = player_list[pid]

                detail_loader = ItemLoader(FootballDetail())

                detail_loader.add_value("mid", match["id"])
                detail_loader.add_value("min", gtime)
                detail_loader.add_value("type", gtype)
                detail_loader.add_value("player_a", player["name"])
                detail_loader.add_value("team", team)

                yield detail_loader.load_item()

        for item in chain(parse_goal(home_goal, 1, 2), parse_goal(away_goal, 2, 1)):
            yield item

        #parse booking
        def parse_booking(booking_list, team):
            for booking in booking_list:
                pid, btype, btime = booking["id"], booking["type"], booking["time"]
                player = player_list[pid]
                btype = 2 if btype == "y" else 3

                detail_loader = ItemLoader(FootballDetail())

                detail_loader.add_value("mid", match["id"])
                detail_loader.add_value("min", btime)
                detail_loader.add_value("type", btype)
                detail_loader.add_value("player_a", player["name"])
                detail_loader.add_value("team", team)

                yield detail_loader.load_item()

        for item in chain(parse_booking(home_booking, 1), parse_booking(away_booking, 2)):
            yield item

        #parse substitution
        def parse_substitution(substitution_list, team):
            for substitution in substitution_list:
                stime, player_a, player_b = substitution["time"], substitution["off"], substitution["on"]
                stype = 4
                player_a = player_list[player_a]
                player_b = player_list[player_b]

                detail_loader = ItemLoader(FootballDetail())

                detail_loader.add_value("mid", match["id"])
                detail_loader.add_value("player_a", player_a["name"])
                detail_loader.add_value("player_b", player_b["name"])
                detail_loader.add_value("min", stime)
                detail_loader.add_value("type", stype)
                detail_loader.add_value("team", team)

                yield detail_loader.load_item()

        for item in chain(parse_substitution(home_substitution, 1), parse_substitution(away_substitution, 2)):
            yield item

        #parse stat
        football_loader = ItemLoader(Football())

        for full, short in SHORTCUT.items():
            for team in ("home", "away"):
                football_loader.add_value(team + "_" + full, stat[team].get(short, 0))
        football_loader.add_value("home_scores", stat["homescore"])
        football_loader.add_value("away_scores", stat["awayscore"])
        home_player_stat = stat["home"].get("player", [])
        away_player_stat = stat["away"].get("player", [])
        home_saving = sum([int(player_stat.get("sv", 0)) for player_stat in home_player_stat])
        away_saving = sum([int(player_stat.get("sv", 0)) for player_stat in away_player_stat])
        football_loader.add_value("home_saving", home_saving)
        football_loader.add_value("away_saving", away_saving)
        football_loader.add_value("mid", match["id"])

        yield football_loader.load_item()

        #repeat
        if finish != 2:
            reactor.callLater(self.scrape_inerval, self.crawler.engine.schedule, request=response.rquest, spider=self)
        else:
            self.task_done(match)

    def spider_idle(self, spider):
        if spider is self and (not self.close_on_idle or self.has_task()):
            raise DontCloseSpider("Dont close me! I have delay tasks now!")

    def task_done(self, match):
        if match in self.matches:
            self.matches.pop(self.matches.index(match))

    def has_task(self):
        return self.matches



