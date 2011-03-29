import tweepy
from django import forms
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from util import fetch_page, fetch_tweet

class UsernameForm(forms.Form):
    enter_username_here = forms.CharField()

def front_page(request):
    username = request.GET.get('enter_username_here')
    if username:# reject empty form
        return redirect('/%s' % username)
    form = UsernameForm()
    return render_to_response('front_page.html', {'form':form})

def user_timeline(request, username, page_num=1):
    # ignore favicon requests
    if username == 'favicon.ico':
        return None
    # if user is protected, offer oauth
    # take a look at IE before shipping
    # register app with twitter?
    user, tweets = fetch_page(username, page_num) #also fetch if user !created, but tweets not in db
    #  boolean for old tweets not available instead of passing user around
    # end of feed
    return render_to_response('user_timeline.html',
                             {'tweets':tweets, 'user':user, 'username':username, 'prev_page':int(page_num)-1, 'next_page':int(page_num)+1,},#detect when there are no more pages
                             context_instance=RequestContext(request),)

def single_tweet(request, username, tweet_id):
    # ignore favicon requests
    if username == 'favicon.ico':
        return None
    # if user is protected, offer oauth

    tweet = fetch_tweet(username, tweet_id)
    return render_to_response('single_tweet.html',
                              {'tweet':tweet, 'username':username,},
                              context_instance=RequestContext(request),)