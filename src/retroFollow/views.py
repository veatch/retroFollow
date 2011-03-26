import tweepy

from django.shortcuts import render_to_response
from django.template import RequestContext

from util import fetch_page

def user_timeline(request, username, page_num=1):
    # ignore favicon requests
    if username == 'favicon.ico':
        return None
    # if user is protected, offer oauth

    user, tweets = fetch_page(username, page_num) #also fetch if user !created, but tweets not in db

    return render_to_response('user_timeline.html',
                             {'tweets':tweets, 'user':user, 'next_page':int(page_num)+1,},#detect when there are no more pages
                             context_instance=RequestContext(request),)# prev page