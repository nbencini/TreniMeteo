#!/usr/bin/env python3
# -*- coding: utf-8 -*-

##
## Stream Twitter data into MongoDB
##

import tweepy
from tweepy import OAuthHandler
from tweepy.streaming import StreamListener
from tweepy import Stream

import re

from config import mongo, twitter


import logging
logger = logging.getLogger("TweetsMongo")

auth = OAuthHandler(twitter['consumer_key'], twitter['consumer_secret'])
auth.set_access_token(twitter['access_token'], twitter['access_token_secret'])

api = tweepy.API(auth)

mongo_db = mongo.tweets_db
mongo_collection = mongo_db.tweets

REGEX_DISAGIO = "(ritard|guast|cancellazion|cancellat|soppress|fermo|fermi)"


class MongoListener(StreamListener):

    def __init__(self, mongo_collection):
        super(MongoListener, self).__init__()
        self.mongo = mongo_collection
        
    def on_status(self, status):
        tweet_text = status.text.replace("\t", " ").replace("\n", "")
        tweet_created_at = status.created_at
        tweet_id = status.id_str
        tweet_username = status.user.name
        tweet_screenname = status.user.screen_name
        if len(status.entities["hashtags"]) > 0:
            hashtags = [hashtag["text"] for hashtag in status.entities["hashtags"]]
        else:
            hashtags = []

        contains_disagio_word = re.search(REGEX_DISAGIO, tweet_text.lower())

        tweet = {
            'id': tweet_id,
            'text': tweet_text,
            'user_name': tweet_username,
            'user_screen_name': tweet_screenname,
            'hashtags': hashtags,
            'disagio': 1 if contains_disagio_word else 0,
            'created_at': tweet_created_at
        }
        
        self.mongo.insert_one(tweet)

    def on_error(self, status_code):
        logger.error("Errore - Status code {}".format(status_code))
        return 1  # 1 fa continuare l'esecuzione dello script anche in caso di errori


stream = Stream(auth = api.auth, listener=MongoListener(mongo_collection))

stream.filter(track=["Trenord"])