# trump-fox-bot

This twitter bot aims to analyze the relationship between morning tweets from the President and coverage from Fox News, specifically, Fox and Friends. The bot runs every single day, without exceptions. It runs in the mornings only, specifically between 4:00 AM EST and 9:30 AM EST, which is when Fox and Friends goes in the air. There are two pieces to this bot:

 **1. db_setter.py**
 This piece of code runs first, and only once. It does so *before* 4:00 AM EST. This code will pull down the latest 10 tweets from the President's twitter account and upload them to a .json file in a AWS bucket. The reason why this is done is because the main part of the bot needs to know what the latest tweets are so that it can figure out which ones are new. This could have also been accomplished by looking at tweet timestaps but for various reasons that direction wasn't taken.

**2. main.py**
This is the main part of the bot. It will run every minute in the timeframes described at the beginning of this document. This code will pull down the latest 10 tweets from the President as well as the 10 tweets stored in the AWS bucket that db_setter.py sets up. 
If there is a tweet that is in the 10 latest tweets but not on the bucket, that tweet will get analyzed. There will be a call to an [API that exposes chyron text information from cable news channels](https://archive.org/services/third-eye.php). 
All the chyrons from the last hour will be requested and stripped from 'stopwords' to avoid drawing relations on a tweet and a chyron based on meaningless words (see stopwords.txt). The tweet in question will also be stripped from 'stopwords'. 
Finally, the tweet will be compared to every single chyron. If there is a single chyron that passes certain threshold on the similarity between the tweet and the chyron, a tweet will be posted. Only a single chyron can be posted per tweet: the one that has the highest relation score. 

**Developer**
This bot was created and developed by [Andres Anhalzer](https://github.com/aanhalzer) for Capital News Service. 