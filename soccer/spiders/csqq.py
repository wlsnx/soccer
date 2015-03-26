#!/usr/bin/env python
# encoding: utf-8


#from scrapy.http import Request
from scrapy.contrib.loader import ItemLoader
from soccer.items import Match, Football, FootballDetail
import json
from itertools import chain
from soccer.spiders.cs import SoccerSpider, MatchFinished


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


class CsqqSpider(SoccerSpider):
    name="csqq"
    allowed_domains = ["sports.qq.com"]
    start_urls = []

    SQL = "SELECT id,home,away,date,time FROM `match` WHERE finish <> 2 AND date=DATE(NOW()) AND league='cn'"
    MATCH_LIST = "http://mat1.gtimg.com/apps/test2/web_shasha_208_new.json"
    #MATCH_DATA = "http://sportswebapi.qq.com/match/view?competitionId=208&matchId={0}"
    LIVE = "http://soccerdata.sports.qq.com/s/live.action?mid={0}"
    SELECT_ONE_MATCH = "SELECT id,home,away,date,time FROM `match` WHERE id={0} LIMIT 1"

    def parse(self, response):
        pass

    def generate_requests(self):
        from scrapy import Request
        yield Request(self.MATCH_LIST,
                      callback=self._generate_requests)

    def _generate_requests(self, response=None):
        #import requests
        #response = requests.get(self.MATCH_LIST).content
        #match_list = json.loads(response[21:][:-1])
        match_list = json.loads(response.body[21:][:-1])
        matches = [m for match in match_list["matches"].values() for m in match]
        for match in self.matches:
            for tmatch in matches:
                if self.same_match(tmatch, match):
                    self.fetch(match, tmatch["matchId"])
                    break
        yield

    def same_match(self,tmatch, match):
        return str(match["date"]) in tmatch["startTime"] and \
            tmatch["homeName"] in match["home"] and \
            tmatch["awayName"] in match["away"]

    def parse_match(self, response):
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
        if finish == 2:
            raise MatchFinished()

