import tweepy
from django import forms
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

from settings import consumer_key, consumer_secret, support_email
from util import fetch_page, fetch_tweet, setup_auth

class UsernameForm(forms.Form):
    enter_username_here = forms.CharField()

def front_page(request):
    username = request.GET.get('enter_username_here')
    if username:
        return redirect('/%s' % username)
    form = UsernameForm()
    return render_to_response('front_page.html', {'form':form},
    context_instance=RequestContext(request),)

def user_timeline(request, username, page_num=1):
    # ignore favicon requests
    if username == 'favicon.ico':
        return None
    # if user is protected, offer oauth
    # take a look at IE before shipping
    # register app with twitter?
    auth = setup_auth(request)
    user, tweets, http_status = fetch_page(username, page_num, auth) #also fetch if user !created, but tweets not in db
    if not tweets:
        return general_error(request, username, http_status)
    #really need to pass user around?
    # handle accounts, like 'shit', that have no tweets
    #  boolean for old tweets not available instead of passing user around
    # end of feed
    return render_to_response('user_timeline.html',
                             {'tweets':tweets, 'user':user, 'username':username, 'prev_page':int(page_num)-1, 'next_page':int(page_num)+1,},#detect when there are no more pages
                             context_instance=RequestContext(request),)

def single_tweet(request, username, tweet_id):#linkify username back to list?
    # ignore favicon requests
    if username == 'favicon.ico':
        return None

    auth = setup_auth(request)
    tweet, http_status = fetch_tweet(username, tweet_id, auth)
    if not tweet:
        return general_error(request, username, http_status)
    return render_to_response('single_tweet.html',
                              {'tweet':tweet, 'username':username,},
                              context_instance=RequestContext(request),)

def general_error(request, username, error_status):
    return render_to_response('error.html',
                             {'username':username, 'error_status':str(error_status),},
                             context_instance=RequestContext(request),)

def auth(request):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    try:
        redirect_url = auth.get_authorization_url()
    except tweepy.TweepError as e:
        print 'Error! Failed to get request token.'
    else:
        request.session['twitter_request_token'] = (auth.request_token.key, auth.request_token.secret)
        request.session['page_pre_auth'] = request.META.get('HTTP_REFERER')
        response = HttpResponseRedirect(redirect_url)
        return response
    return HttpResponseRedirect('/')

def callback(request):
    verifier = request.GET.get('oauth_verifier')
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    token = request.session.get('twitter_request_token')
    request.session.delete('request_token')
    auth.set_request_token(token[0], token[1])
    try:
        # todo: patch tweepy to avoid two requests?
        auth.get_access_token(verifier)
        auth.get_username()
        request.session['access_token'] = (auth.access_token.key, auth.access_token.secret)
        request.session['auth_username'] = auth.username
    except tweepy.TweepError:
        print 'Error! Failed to get access token.'
    return HttpResponseRedirect(request.session.get('page_pre_auth', '/'))

def logout(request):
    request.session.flush()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))

def fourohfour(request):
    return render_to_response('404.html', {'support_email':support_email,},)