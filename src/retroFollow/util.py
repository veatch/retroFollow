from datetime import timedelta
import tweepy

from models import Tweet, UserTwitter
from settings import tweets_per_page, tweets_per_user, max_page

def fetch_tweet(username, tweet_id):
    return Tweet.objects.filter(user__username=username).filter(tweet_id=long(tweet_id))[0]

# handle protected accounts
# 400 is status during rate limiting... catch consistently and display friendly message
def fetch_page(username, page_num):
    def utc_to_user_time(tweet_datetime):
        # figure out why twitter tz names don't work
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
        print 'fetching page %d with tweepy' % page_num
        api = tweepy.API()
        try:
            tweets = api.user_timeline(user.username, include_rts=True, page=page_num, count=tweets_per_page)
        except tweepy.TweepError as e:
            print '%s %s' % (e.response.status, e.response.reason)
        #    return render_to_response('user_timeline.html', {'error_message':'shit'})
        # also show join date
        else:
            for tweet in tweets:
                Tweet.objects.get_or_create(user=user, text=tweet.text, created_at=utc_to_user_time(tweet.created_at), tweet_id=tweet.id)
            if tweets:
                return True
        return False # what if 400, but next succeeds, even though this was right page? exception should be propogated instead of
        # failing silently

    def fetch_later_twitter_page(first_page_num, request_page_num):
        '''
        Like fetch_twitter_page(), but keep fetching until we hit an existing tweet.
        '''
        api = tweepy.API()
        page_num = first_page_num - request_page_num - 2
        while page_num <= first_page_num: # figure out how to make larger requests and spare some traffic
            print 'fetch later twitter page %d' % page_num
            try:
                tweets = api.user_timeline(user.username, include_rts=True, page=page_num, count=tweets_per_page)
            except tweepy.TweepError as e:
                print '%s %s' % (e.response.status, e.response.reason)
            #    return render_to_response('user_timeline.html', {'error_message':'shit'})
            # also show join date
            else:
                for tweet in tweets:
                    _, created = Tweet.objects.get_or_create(user=user, text=tweet.text, created_at=utc_to_user_time(tweet.created_at), tweet_id=tweet.id)
                    if not created:
                        return
            # if you start 400'ing, abort
            page_num = page_num + 1

    # what's faster? searching, or making one request with many tweets per page?
    def search_for_first_tweets(min_page, max_page):
        print 'binary searching for first tweets'
        api = tweepy.API()
        search_page = min_page + ((max_page - min_page) / 2) # problem with over max num tweets, step back extra page to be sure
        print "trying page %d" % search_page
        try:
            tweets = api.user_timeline(user.username, include_rts=True, page=search_page, count=tweets_per_page)
        except tweepy.TweepError as e:
            print '%s %s' % (e.response.status, e.response.reason)
        # handle no tweets returned... test that this doesn't blow up
        else:
            if not tweets:
                return search_for_first_tweets(min_page=min_page, max_page=search_page)
            # if exactly 20, max_id search with oldest tweet
            if len(tweets) == tweets_per_page:
                return search_for_first_tweets(min_page=search_page, max_page=max_page)
            return search_page, tweets

    def find_first_page(user_tweet_count):
        print 'find first page'
        def first_page_searcher(first_page_num):
            if not fetch_twitter_page(first_page_num):
                # if twitter's page count is off, search for first page
                # try next five pages
                for i in range (1, 6):
                    if first_page_num-i == 0:
                        return 0
                    print 'trying %d' % (first_page_num-i)
                    if fetch_twitter_page(first_page_num-i):
                        print 'first page is %d' % (first_page_num-i)
                        return first_page_num-i
                # if still haven't found it, binary search
                page, tweets = search_for_first_tweets(min_page=0, max_page=first_page_num)
                for tweet in tweets:
                    Tweet.objects.get_or_create(user=user, text=tweet.text, created_at=utc_to_user_time(tweet.created_at), tweet_id=tweet.id)
                print 'first page is %d' % page
                return page
            print 'first page is %d' % first_page_num
            return first_page_num

        def fetch_bounding_pages(first_page_num):
            ######
            # double check and fetch previous page here
            if first_page_num > 1:
                fetch_twitter_page(first_page_num-1)
            # just a doublecheck for earlier tweets? not sure what this is about
            if user_tweet_count % tweets_per_page != 0 and first_page_num != max_page:
           	    fetch_twitter_page(first_page_num+1)

        first_page_num = user_tweet_count / tweets_per_page
        if first_page_num > max_page:
            first_page_num = max_page

        first_page_num = first_page_searcher(first_page_num)
        fetch_bounding_pages(first_page_num)

        # timeline for user 'shah' is totally f'd... random tweet on pg23, first page is actually 18
        # too handle cases like these, keep searching for first page until you have at least 20 tweets
        while(Tweet.objects.filter(user=user).count() < tweets_per_page and first_page_num > 0):
            print 'not enough tweets, into the while loop'
            first_page_num = first_page_searcher(first_page_num-1)
            fetch_bounding_pages(first_page_num)

        return first_page_num
#################################################
    page_num = int(page_num)

    user, _ = UserTwitter.objects.get_or_create(username=username)

    if Tweet.objects.filter(user=user).count() < tweets_per_page*page_num:
        api = tweepy.API()
        try:
            api_user = api.get_user(user.username)
        except tweepy.TweepError as e:
            print '%s %s' % ((e.response.status or e.response), (e.response.reason or e.response))
        else:
            if not user.utc_offset:
                user.utc_offset = api_user.utc_offset
                user.save()
            user_tweet_count = api_user.statuses_count

            #make sure this only happens at creation
            if user_tweet_count > tweets_per_user:
                user.old_timer_and_or_gabber=True
                user.save()
            first_page_num = find_first_page(user_tweet_count)
            # fetching should start early, and then move back in time. when you hit an existing tweet, you're done.
            # so if 3rd page should be first_page_num-2, start one page before that, and keep fetching until you hit
            # existing tweet
            # Once you hit an existing tweet, should be safe to assume that all tweets before
            # that are already in our db. How to make this assumption a reality?

            # If there are 120 veatch tweets in db, you should know that those are first 120. There should be no
            # possibility that it's 80 earliest tweets, and 40 later tweets because someone hit /veatch/15
            # Need some sort of transactions... say a request is made that requires
            # 4 requests. 3rd one fails. delete tweets from first two so integrity isn't comprommised
            # maybe log username and page so that they can be manually retrieved later
            # You could also start requesting in the other direction, and if 3rd transaction fails
            # you still have first two because they were earlier. But don't like that if tweet
            # occurs during a series of requests, a tweet could get lost because of page shift.
            if Tweet.objects.filter(user=user).count() < tweets_per_page*page_num:
                fetch_later_twitter_page(first_page_num, page_num)#handle case where someone enters number > number of available tweets
    else:
        print 'already in database'
    return user, Tweet.objects.filter(user=user).order_by('created_at')[tweets_per_page*(page_num-1) : tweets_per_page*page_num]