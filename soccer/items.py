# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.contrib.loader.processor import Compose, TakeFirst
from scrapy.contrib.loader import ItemLoader


#def try_trans_int(s):
    #try:
        #return int(s)
    #except ValueError:
        #return 0

class SoccerItemLoader(ItemLoader):

    default_output_processor = TakeFirst()


class DefaultValueItem(scrapy.Item):

    def __init__(self, *args, **kwargs):
        super(DefaultValueItem, self).__init__(*args, **kwargs)
        for key, value in self.fields.items():
            if key not in self and "default" in value:
                self[key] = value["default"]



class Football(DefaultValueItem):
    home_shot            = scrapy.Field()
    away_shot            = scrapy.Field()
    home_shots           = scrapy.Field()
    away_shots           = scrapy.Field()
    home_fouls           = scrapy.Field()
    away_fouls           = scrapy.Field()
    home_corner          = scrapy.Field()
    away_corner          = scrapy.Field()
    home_offside         = scrapy.Field()
    away_offside         = scrapy.Field()
    home_ball_possession = scrapy.Field()
    away_ball_possession = scrapy.Field()
    home_yellow_card     = scrapy.Field()
    away_yellow_card     = scrapy.Field()
    home_red_card        = scrapy.Field()
    away_red_card        = scrapy.Field()
    home_saving          = scrapy.Field()
    away_saving          = scrapy.Field()
    home_scores          = scrapy.Field()
    away_scores          = scrapy.Field()
    date                 = scrapy.Field()
    time                 = scrapy.Field()
    attendance           = scrapy.Field(default=0)
    mvp                  = scrapy.Field(default="")
    mvp_id               = scrapy.Field(default=0)
    mid                  = scrapy.Field()


class FootballDetail(DefaultValueItem):
    mid             = scrapy.Field()
    min             = scrapy.Field()
    team            = scrapy.Field()
    type            = scrapy.Field()
    player_a        = scrapy.Field(default = "")
    player_a_id     = scrapy.Field(default = 0 )
    player_a_domain = scrapy.Field(default = "")
    player_b        = scrapy.Field(default = "")
    player_b_id     = scrapy.Field()
    player_b_domain = scrapy.Field()


class Match(DefaultValueItem):
    id          = scrapy.Field()
    m_time      = scrapy.Field()
    home_scores = scrapy.Field()
    away_scores = scrapy.Field()
    finish      = scrapy.Field()

