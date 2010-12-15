#!/usr/bin/env python

import datetime
import tweepy

from django.shortcuts import render_to_response

from operator import attrgetter
from tweepy.error import TweepError

# importing settings like this is bad?
import settings
from settings import tweets_per_page
from models import UserTwitter, Tweet, Manager

# get storage set up
# setup fallback to max_id search when status count is off
# put on github


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
    return tweepy.API(auth)

def check_for_existing_tweets(username):
    return RetroFollowing.objects.filter(username=username)

def user_timeline(request, username):
    # if user is protected, offer oauth
    user, created = UserTwitter.objects.get_or_create(username=username)
    manager, created = Manager.objects.get_or_create(user=user)
    tweets = manager.fetch_first_page() #also fetch if user !created, but tweets not in db

    return render_to_response('user_timeline.html', {'tweets':tweets, 'user':user})

def old_user_timeline(request, username):
    print 'why?'
    try:
        api = login_user()
        twit = RetroFollowing(username=username)
        tweets = twit.fetch_initial_tweets(api, username)
    except (TweepError):
        return render_to_response('user_timeline.html', {'error_message':'oh nooooooooo'})
    return render_to_response('user_timeline.html', {'tweets':tweets})
