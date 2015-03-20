# -*- coding: utf-8 -*-

# Define here the models for your scraped items
#
# See documentation in:
# http://doc.scrapy.org/en/latest/topics/items.html

import scrapy
from scrapy.contrib.loader.processor import Compose, TakeFirst


#def try_trans_int(s):
    #try:
        #return int(s)
    #except ValueError:
        #return 0


class DefaultValueItem(scrapy.Item):

    def __getitem__(self, key):
        try:
            return self._values[key]
        except KeyError:
            field = self.fields[key]
            if "default" in field:
                return field["default"]
            raise


class Football(DefaultValueItem):
    home_shot            = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_shot            = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_shots           = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_shots           = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_fouls           = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_fouls           = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_corner          = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_corner          = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_offside         = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_offside         = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_ball_possession = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_ball_possession = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_yellow_card     = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_yellow_card     = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_red_card        = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_red_card        = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_saving          = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_saving          = scrapy.Field(default=0 , output_processor=TakeFirst())
    home_scores          = scrapy.Field(default=0 , output_processor=TakeFirst())
    away_scores          = scrapy.Field(default=0 , output_processor=TakeFirst())
    date                 = scrapy.Field()
    time                 = scrapy.Field(output_processor=TakeFirst())
    attendance           = scrapy.Field(default=0)
    mvp                  = scrapy.Field(default="")
    mvp_id               = scrapy.Field(default=0)
    mid                  = scrapy.Field(default=0, output_processor=TakeFirst())


class FootballDetail(DefaultValueItem):
    mid             = scrapy.Field(default = 0  , output_processor = TakeFirst())
    min             = scrapy.Field(default = 0  , output_processor = TakeFirst())
    team            = scrapy.Field(default = 1  , output_processor = TakeFirst())
    type            = scrapy.Field(default = 1  , output_processor = TakeFirst())
    player_a        = scrapy.Field(default = "" , output_processor = TakeFirst())
    player_a_id     = scrapy.Field(default = 0  , output_processor = TakeFirst())
    player_a_domain = scrapy.Field(default = "" , output_processor = TakeFirst())
    player_b        = scrapy.Field(default = "" , output_processor = TakeFirst())
    player_b_id     = scrapy.Field(default = 0  , output_processor = TakeFirst())
    player_b_domain = scrapy.Field(default = "" , output_processor = TakeFirst())


class Match(DefaultValueItem):
    id          = scrapy.Field(default = 0, output_processor = TakeFirst())
    m_time      = scrapy.Field(output_processor=TakeFirst())
    home_scores = scrapy.Field(default = 0, iutput_processor   = Compose(try_trans_int), output_processor = TakeFirst())
    away_scores = scrapy.Field(default = 0, iutput_processor = Compose(try_trans_int), output_processor = TakeFirst())
    finish      = scrapy.Field(default = 0, output_processor = TakeFirst())

