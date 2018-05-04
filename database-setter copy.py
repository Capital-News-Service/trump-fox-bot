#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import boto3
import json
import tweepy

def updateDatabase(data, my_bucket):        
    with open('tweets.json','w') as f:
        json.dump(data, f)
    
    with open('tweets.json', 'rb') as data:
        my_bucket.upload_fileobj(data, 'tweets.json')

def parse(tweets):
    to_return = []
    for status in tweets:
        print(status)
        to_return.append([status._json['full_text'], 'https://twitter.com/realDonaldTrump/status/' + status._json['id_str']])
    return to_return

def driver(api, my_bucket):
    new_tweets = parse(api.user_timeline(screen_name='realDonaldTrump', count=1, tweet_mode='extended'))
    data = {}
    data['tweets'] = []
    for tweet in new_tweets:
        data['tweets'].append(tweet)
    
    updateDatabase(data, my_bucket)
    
### CODE HERE ###
keys = {}
with open('keys.json', 'r') as f:
    keys = json.loads(f.read())

consumer_key = keys['consumer_key']
consumer_secret = keys['consumer_secret']
access_key = keys['access_key']
access_secret = keys['access_secret']
db_access = keys['db_access']
db_secret = keys['db_secret']

bucket_name = 'trump-fox-bot'

s3 = boto3.resource('s3', aws_access_key_id=db_access, aws_secret_access_key=db_secret)
my_bucket = s3.Bucket(bucket_name)

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)        
driver(api, my_bucket)