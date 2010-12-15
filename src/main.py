#!/usr/bin/env python

import datetime
import tweepy

from operator import attrgetter

# importing settings like this is bad?
from retroFollow import settings
from retroFollow.models import RFUser, RetroFollowing, RetroTweet, FollowSettings

def login_user():
    auth = tweepy.OAuthHandler(settings.CONSUMER_KEY, settings.CONSUMER_SECRET)
    '''
    auth_url = auth.get_authorization_url()
    print 'Authorize: ' + auth_url
    verifier = raw_input('PIN: ').strip()
    auth.get_access_token(verifier)
    print 'key %s' % auth.access_token.key
    print 'secret %s' % auth.access_token.secret
    '''
    auth.set_access_token(settings.ACCESS_KEY, settings.ACCESS_SECRET)
    return auth.get_username(), tweepy.API(auth)

def get_latest_tweets(api):
    return api.home_timeline()

def display_tweets(tweets):
    for t in tweets:
        print '%s %s' % (t.created_at, t.text)

def store_tweets(user, author, tweets):
    follow_settings = FollowSettings.objects.get(user=user, following=author)
    startFollow = follow_settings.startFollowTime
    now = datetime.datetime.now()
    first_tweet_time = author.first_tweet_time
    for t in tweets:
        time_delta = t.created_at - first_tweet_time
        rt = RetroTweet(tweeter=author, text=t.text, created_at=t.created_at, re_tweet_time= now + time_delta)
        rt.save()
    latest_tweet_time = RetroTweet.objects.filter(created_at=tweets[0].created_at)[0].re_tweet_time
    author.latest_re_tweet_time = latest_tweet_time
    author.save()

if __name__ == '__main__':
    username, api = login_user()
    new_tweets = get_latest_tweets(api)
    user = RFUser.objects.get(username=username)
    following = user.following.all()
    old_tweets = []
    print "starting to run through twits we're following"
    for rt in following: 
        if datetime.datetime.now() > rt.latest_re_tweet_time:
        # after fetching and storing, update latestTweetTime
            tweets = rt.fetch_initial_tweets(api, rt.username)
            store_tweets(user, rt, tweets)
        author = RetroFollowing.objects.get(username=rt.username)
        now = datetime.datetime.now()
        # possible to query across FollowSettings for user, instead of iterating over author?
        tweets = RetroTweet.objects.filter(re_tweet_time__gt = new_tweets[-1].created_at).filter(re_tweet_time__lt = now).filter(tweeter=author)
        if tweets:
            old_tweets = old_tweets + [t for t in tweets]
    if old_tweets:
        print 'we have some old tweets'
        new_tweets = new_tweets + old_tweets
        new_tweets = sorted(new_tweets, key=attrgetter('created_at'), reverse=True)
    display_tweets(new_tweets[:20])
