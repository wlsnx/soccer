# -*- coding: utf-8 -*-

# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import redis
from soccer.items import Match, Football, FootballDetail
import cPickle as pickle


def equal(item, old_item):
    for key, value in item.items():
        if not (key in old_item and old_item[key] == value):
            return False
    return True

def player_info(table, player_name):
    player = table.find_one(player_name=player_name)
    yield player["id"] if player else 0
    yield player["domain"] if player else ""


class CachedDatabasePipeline(object):

    def __init__(self):
        self.cache = redis.StrictRedis()
        self.db = None

    def process_item(self, item, spider):
        self.db = spider.db
        if isinstance(item, Match):
            key = "match:{0}".format(item["id"])
        elif isinstance(item, Football):
            key = "football:{0}".format(item["mid"])
        elif isinstance(item, FootballDetail):
            key = "footballdetail:{mid}:{min}:{team}:{type}".format(**item)

        old_item = self.cache.get(key)
        if not (old_item and equal(item, pickle.loads(old_item))):
            self.cache.set(key, pickle.dumps(item))
            self.save(item)
        return item

    def save(self, item):
        if isinstance(item, Match):
            table = self.db.get_table("match")
            table.update(item, ["id"])

        elif isinstance(item, Football):
            table = self.db.get_table("match_football")
            match = table.find_one(mid=item["mid"])
            if match:
                table.update(item, ["mid"])
            else:
                match_table = self.db.get_table("match")
                match_a = match_table.find_one(id=item["mid"])
                item["date"] = match_a["date"]
                item["time"] = match_a["time"]
                table.insert(item)

        elif isinstance(item, FootballDetail):
            table = self.db.get_table("match_football_details")
            player_table = self.db.get_table("player")
            player_a_id, player_a_domain = player_info(player_table, item["player_a"])
            player_b_id, player_b_domain = player_info(player_table, item["player_b"])
            item["player_a_id"] = player_a_id
            item["player_a_domain"] = player_a_domain
            item["player_b_id"] = player_b_id
            item["player_b_domain"] = player_b_domain

            match = table.find_one(**item)
            if not match:
                table.insert(item)

