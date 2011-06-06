from datetime import timedelta
from django.http import Http404
from string import lower
import tweepy

from models import Tweet, UserTwitter
from settings import tweets_per_page, tweets_per_user, max_page, consumer_key, consumer_secret, write_consumer_key, write_consumer_secret, retrofollow1_key, retrofollow1_secret

def setup_auth(request=None, key=consumer_key, secret=consumer_secret):
    auth = tweepy.OAuthHandler(key, secret)
    if request:
        access_token = request.session.get('access_token')
        if access_token:
            auth.set_access_token(access_token[0], access_token[1])
    return auth

def fetch_tweet(username, tweet_id, auth):
    try:
        user = UserTwitter.objects.get(username=username)
    except UserTwitter.DoesNotExist:
        raise Http404
    if user.is_protected:
        api = tweepy.API(auth)
        try:
            api.user_timeline(username, include_rts=True)
        except tweepy.TweepError as e:
            return None, getattr(e.response, 'status', '')
    try:
        tweet = Tweet.objects.get(user__username=username, tweet_id=long(tweet_id))
    except Tweet.DoesNotExist:
        raise Http404
    return tweet, 200

def check_rate_limit(auth=None):
    api = tweepy.API(auth)
    try:
        rate_limit_status = api.rate_limit_status()
    except tweepy.TweepError as e:
        return None, getattr(e.response, 'status', '')
    else:
        return rate_limit_status.get('remaining_hits')

def send_retro_tweets(tweets):
    write_auth = setup_auth(key=write_consumer_key, secret=write_consumer_secret)
    write_auth.set_access_token(retrofollow1_key, retrofollow1_secret)
    api = tweepy.API(write_auth)
    for tweet in tweets:
        try:
            api.retweet(id=tweet.tweet_id)
        except tweepy.TweepError:
            pass
    # what exceptions to handle, and how?

def fetch_page(username, page_num, auth=None):
    def utc_to_user_time(tweet_datetime):
        # todo: figure out why twitter tz names don't work
        # set up mapping of US tz's to standard names
        # use tz name, if fail, use offset
        # ***adjust for DST***
        if user.utc_offset:
            return tweet_datetime + timedelta(seconds=user.utc_offset)
        return tweet_datetime

    def fetch_twitter_page(page_num):
        """
        return true if tweets fetched successfully, false if not
        """
        api = tweepy.API(auth)
        try:
            tweets = api.user_timeline(user.username, include_rts=True, page=page_num, count=tweets_per_page)
        except tweepy.TweepError as e:
            pass
        else:
            for tweet in tweets:
                Tweet.objects.get_or_create(user=user, text=tweet.text, created_at=utc_to_user_time(tweet.created_at), tweet_id=tweet.id)
            if tweets:
                return True
        return False # todo: what if 400, but next succeeds, even though this was right page? exception should be propogated instead of failing silently

# todo: if oldtimer/gabber, first page will always be 160, so figuring out where later page should start from?
    def fetch_later_twitter_page(first_page_num, request_page_num):
        '''
        Like fetch_twitter_page(), but keep fetching until we hit an existing tweet.
        '''
        api = tweepy.API(auth)
        # Start fetching further in the future than necessary to give some padding. We do this by subtracting 2.
        page_num = first_page_num - request_page_num - 2
        if page_num < 0:
            page_num = 0
        while page_num <= first_page_num: # todo: figure out how to make larger requests and spare some traffic
            try:
                tweets = api.user_timeline(user.username, include_rts=True, page=page_num, count=tweets_per_page)
            except tweepy.TweepError as e:
                pass

            else:
                # 1. If user is tweeting while we fetch a series of their pages, at some point the first tweet(s) in a page will be tweet(s) we've already
                # fetched. When we hit a tweet that's already in the database, we don't want to assume we've reached the end of new tweets and return
                # prematurely, so we always start by assuming we're going back over tweets we just fetched.
                going_back_over_tweets_we_just_fetched = True
                for tweet in tweets:
                    _, created = Tweet.objects.get_or_create(user=user, text=tweet.text, created_at=utc_to_user_time(tweet.created_at), tweet_id=tweet.id)
                    if going_back_over_tweets_we_just_fetched:
                        if created:
                            # 2. As soon as we hit a tweet that isn't already in database, we know we're done going over stuff we just fetched,
                            # and we're now fetching new stuff.
                            going_back_over_tweets_we_just_fetched = False
                        continue
                    if not created:
                    # 3. After that, when we hit a tweet that's already in our database, we know we've hit the old stuff, and we can stop fetching.
                        return
            # todo: if you start 400'ing, abort... keep list of just fetched tweets and delete them if there's a failure?
            page_num = page_num + 1

    # todo: what's faster? searching, or making one request with many tweets per page?
    def search_for_first_tweets(min_page, max_page):
        api = tweepy.API(auth)
        search_page = min_page + ((max_page - min_page) / 2) # problem with over max num tweets, step back extra page to be sure
        try:
            tweets = api.user_timeline(user.username, include_rts=True, page=search_page, count=tweets_per_page)
        except tweepy.TweepError as e:
            pass
        else:
            if not tweets:
                return search_for_first_tweets(min_page=min_page, max_page=search_page)
            # if exactly 20, max_id search with oldest tweet
            if len(tweets) == tweets_per_page:
                return search_for_first_tweets(min_page=search_page, max_page=max_page)
            return search_page, tweets

    def find_first_page(user_tweet_count):
        def first_page_searcher(first_page_num):
            if not fetch_twitter_page(first_page_num):
                # if twitter's page count is off, search for first page
                # try next five pages
                for i in range (1, 6):
                    if first_page_num-i == 0:
                        return 0
                    if fetch_twitter_page(first_page_num-i):
                        return first_page_num-i
                # if still haven't found it, binary search
                page, tweets = search_for_first_tweets(min_page=0, max_page=first_page_num)
                for tweet in tweets:
                    Tweet.objects.get_or_create(user=user, text=tweet.text, created_at=utc_to_user_time(tweet.created_at), tweet_id=tweet.id)
                return page
            return first_page_num

        def fetch_bounding_pages(first_page_num):
            ######
            # double check and fetch previous page here
            if first_page_num > 1:
                fetch_twitter_page(first_page_num-1)
            # just a doublecheck for earlier tweets? not sure what this is about
            if user_tweet_count % tweets_per_page != 0 and first_page_num != max_page:
           	    fetch_twitter_page(first_page_num+1)

        first_page_num = (user_tweet_count / tweets_per_page) + 1 # see d profile
        if first_page_num > max_page:
            first_page_num = max_page

        first_page_num = first_page_searcher(first_page_num)
        fetch_bounding_pages(first_page_num)

        # timeline for user 'shah' is totally f'd... random tweet on pg23, first page is actually 18
        # to handle cases like these, keep searching for first page until you have at least 20 tweets
        while(Tweet.objects.filter(user=user).count() < tweets_per_page and first_page_num > 0):
            first_page_num = first_page_searcher(first_page_num-1)
            fetch_bounding_pages(first_page_num)

        return first_page_num
#################################################
# fetch_page starts here.
#################################################
    page_num = int(page_num)
    api = tweepy.API(auth)
    api_user = None
    # todo: twitter bot to get over 3,200 tweets, then see if all are availabe when logged in
    user, created = UserTwitter.objects.get_or_create(username_slug=lower(username))
    if user.is_protected: # is_protected defaults to True, so we'll always enter this block the first time
        try:
            api_user = api.get_user(username)
        except tweepy.TweepError as e:
            if created:
                user.delete()
            return None, None, getattr(e.response, 'status', '')
        else:
            if not api_user.protected:
                user.is_protected = False
                user.save()
            if created:
                # todo: managment command or something to fetch tweets for user close to or over 3,200 to make sure we
                # don't have any gaps if no one looks at their twarchive for awhile
                if api_user.statuses_count > tweets_per_user:
                    user.old_timer_and_or_gabber=True
                user.username = api_user.screen_name
                user.save()
            try:# todo: eliminate need to do this for users that were just created
                api.user_timeline(user.username, include_rts=True)
            except tweepy.TweepError as e:
                return user, None, getattr(e.response, 'status', '')

    if Tweet.objects.filter(user=user).count() < tweets_per_page*page_num:
        if not api_user:
            try:
                api_user = api.get_user(user.username)
            except tweepy.TweepError as e:
                return user, None, getattr(e.response, 'status', '')
        if not user.utc_offset: # this should be saved in our db on creation. if user changes timezones, tweets in out db won't be shown with new tz, right? not ideal, but nothing is
            user.utc_offset = api_user.utc_offset
            user.save()
        # todo: possible for user to change capitalization of their username?

        # at this point, if rate_limit_status < 150, set auth=None... if < 50, cut off
        # need to cache rate_limit status so it's called once every few requests, instead of for every page view
        first_page_num = find_first_page(api_user.statuses_count)

        # If there are 120 veatch tweets in db, you should know that those are first 120. There should be no
        # possibility that it's 80 earliest tweets, and 40 later tweets because someone hit /veatch/15
        # Need some sort of transactions... say a request is made that requires
        # 4 requests. 3rd one fails. delete tweets from first two so integrity isn't comprommised
        # maybe log username and page so that they can be manually retrieved later
        # You could also start requesting in the other direction, and if 3rd transaction fails
        # you still have first two because they were earlier. But don't like that if tweet
        # occurs during a series of requests, a tweet could get lost because of page shift.
        if Tweet.objects.filter(user=user).count() < tweets_per_page*page_num:
            fetch_later_twitter_page(first_page_num, page_num)
    return user, Tweet.objects.filter(user=user).order_by('created_at')[tweets_per_page*(page_num-1) : tweets_per_page*page_num], 200