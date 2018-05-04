#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import tweepy
import urllib3
import boto3
from fuzzywuzzy import fuzz
from datetime import datetime
import pytz
from pytz import timezone
import json

def lambda_handler(event, context):
	def updateDatabase(data, my_bucket):        
		with open('/tmp/tweets.json','w') as f:
			json.dump(data, f)
	
		with open('/tmp/tweets.json', 'rb') as data:
			my_bucket.upload_fileobj(data, 'tweets.json')

	def readDatabase(my_bucket): 
		with open('/tmp/tweets.json','wb') as data:
			my_bucket.download_fileobj('tweets.json', data)
		
		old_tweets = {}
		with open('/tmp/tweets.json','r') as f:
			old_tweets = json.loads(f.read())
		
		return old_tweets['tweets']

	def checkLength(chyron, time, tweet):
		finalString = 'This chyron:\n' + chyron + '\nSeen at ' + time + ' EST\nMay have caused ' + tweet
		if (len(finalString) <= 280):
			return finalString
		else:
			difference = len(finalString) - 283
			chyron = chyron[:-difference] + '...'
			return 'This chyron:\n' + chyron + '\nSeen at ' + time + ' EST\nMay have caused ' + tweet

	def replaceForEST(date, time):
		fmt = '%Y-%m-%d %H:%M:%S'
		(year, month, day) = date.split('-')
		(hour, minute, second) = time.split(':')
		utc_dt = datetime(int(year), int(month), int(day), int(hour), int(minute), int(second), tzinfo=pytz.utc)
		loc_dt = utc_dt.astimezone(timezone('US/Eastern'))
		return loc_dt.strftime(fmt).split(' ')[1][:-3]

	def remove_stopwords(sentence, stopwords):
		result = ''
		for word in sentence.split(' '):
			if not word.lower() in stopwords:
				if len(result) == 0:
					result= result + word
				else:
					result= result + ' ' + word  
		return result            

	def chyron_cleaner(result):
		result = result.replace('\\"', '')
		result = result.replace('\\n', ' -- ')
		result = result.replace('\\', '')  
		result = result.replace('{', '')   
		result = result.replace('>', '')
		result = result.replace('[', '')    
		return result   
	
	def analyze(tweet, chyrons, api, stopwords):  
		clean_tweet = remove_stopwords(tweet[0], stopwords)     
		found_one = '' 
		higher_value = 0
		date = None
		time = None   
		for chyron in chyrons:
			clean_chyron = chyron_cleaner(chyron[5])
			edited_chyron = remove_stopwords(clean_chyron, stopwords) 
			value = fuzz.token_set_ratio(clean_tweet, edited_chyron.replace(' -- ', ' '))
			if (value > 60 and value > higher_value):
				found_one = clean_chyron
				higher_value = value	
				date = chyron[0]
				time = chyron[1]
		if (higher_value != 0):	
			api.update_status(checkLength(found_one, replaceForEST(date,time), tweet[1]))

	def parse(tweets):
		to_return = []
		for status in tweets:
			to_return.append([status._json['full_text'], 'https://twitter.com/realDonaldTrump/status/' + status._json['id_str']])
		return to_return

	def get_chyrons():
		http = urllib3.PoolManager()
		response = http.request('GET', 'https://archive.org/services/third-eye.php?last=1')
		asString = str(response.data.decode('utf-8'))
		chyrons = []
		for line in asString.split('\n'):
			record = line.split('\t')
			if (len(record) > 1 and (record[1] == 'FOXNEWSW')):
				name = ' '.join(str(x) for x in record[3].split('/')[0].split('_')[3:])
				time = record[0].split(' ')
				record[0] = time[0]
				record[3] = name
				record.insert(1, time[1])
				chyrons.append(record)
		return chyrons

	def get_stopwords():
		with open('stopwords.txt', 'r') as f:
			return f.read().splitlines()
	
	def driver(api, my_bucket):
		old_tweets = readDatabase(my_bucket)
		new_tweets = parse(api.user_timeline(screen_name='realDonaldTrump', count=10, tweet_mode='extended'))
		stopwords = get_stopwords()
		chyrons = get_chyrons()
		data = {}
		data['tweets'] = []
		for tweet in new_tweets:
			data['tweets'].append(tweet)
			if not tweet in old_tweets:
				analyze(tweet,chyrons,api,stopwords)
			
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
	return