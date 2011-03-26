#!/usr/bin/env python

import tweepy

from django.shortcuts import render_to_response

from tweepy.error import TweepError

# importing settings like this is bad?
import settings
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

def user_timeline(request, username, page_num=1):
    # ignore favicon requests
    if username == 'favicon.ico':
        return None
    # if user is protected, offer oauth
    user, created = UserTwitter.objects.get_or_create(username=username)
    manager, created = Manager.objects.get_or_create(user=user)
    tweets = manager.fetch_page(page_num) #also fetch if user !created, but tweets not in db

    return render_to_response('user_timeline.html', {'tweets':tweets, 'user':user, 'next_page':int(page_num)+1,})

def old_user_timeline(request, username):
    print 'why?'
    try:
        api = login_user()
        twit = RetroFollowing(username=username)
        tweets = twit.fetch_initial_tweets(api, username)
    except (TweepError):
        return render_to_response('user_timeline.html', {'error_message':'oh nooooooooo'})
    return render_to_response('user_timeline.html', {'tweets':tweets})#'next_page':True/False
