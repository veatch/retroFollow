import tweepy

from django.db import models

from settings import tweets_per_page
    
class UserTwitter(models.Model):
    '''
    #class Meta:
    #    app_label='retroFollow'
    '''
    username = models.CharField(unique=True, max_length=32)
    old_timer_and_or_gabber = models.BooleanField(default=False)
    #first_tweet_time = models.DateTimeField()
    #followers = models.ManyToManyField(RFUser, related_name='following')
    # first tweet time and id for use with new users?

    def fetch_initial_tweets(self, api, username):
        locale.setlocale(locale.LC_ALL, "")
        tweets = api.user_timeline(username, include_rts=True)
        if len(tweets) < 20:
            return tweets
        low_id = 0
        max_id = tweets[0].id
        search_id = (max_id-low_id)/2
        print locale.format('%d', search_id, True)
        while len(tweets) >= 20 or len(tweets) == 0:
            tweets = api.user_timeline(username, include_rts=True, max_id=search_id)
            #handle TweepError such as 503s
            if not tweets:
                low_id = search_id
                search_id = search_id + (max_id - low_id)/2
                print 'LOW'
                print locale.format('%d', search_id, True)
            else:
                max_id = search_id
                search_id = search_id - (max_id - low_id)/2 
                print 'HIGH'
                print locale.format('%d', search_id, True)
        # trying to get first tweet at beginning so we can grab first tweet time
        # this may blow up
        tweets.reverse()
        self.first_tweet_time = tweets[0].created_at
        #self.save()
        #tweets.reverse()
        return tweets

class Tweet(models.Model):
    user = models.ForeignKey(UserTwitter, related_name='tweets')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField()
    tweet_id = models.BigIntegerField()

class Manager(models.Model):
    user = models.ForeignKey(UserTwitter)
    #following = models.ForeignKey(RetroFollowing, related_name='follow_settings')
    #startFollowTime = models.DateTimeField()
    #latest_re_tweet_time = models.DateTimeField()

    def fetch_twitter_page(self, page_num):
        print 'fetching page %d with tweepy' % page_num
        api = tweepy.API()
        tweets = api.user_timeline(self.user.username, include_rts=True, page=page_num, count=tweets_per_page)

        #except (TweepError):
        #    return render_to_response('user_timeline.html', {'error_message':'shit'})
        # also show join date
        for tweet in tweets:
            Tweet.objects.get_or_create(user=self.user, text=tweet.text, created_at=tweet.created_at, tweet_id=tweet.id)

    def search_for_first_tweets(self, min_page, max_page):
        print 'searching for first tweets'
        api = tweepy.API()
        search_page = (max_page - min_page) / 2
        print "trying page %d" % search_page
        tweets = api.user_timeline(self.user.username, include_rts=True, page=search_page, count=tweets_per_page)
        # handle no tweets returned... test that this doesn't blow up
        if not tweets:
            return search_for_first_tweets(min_page=min_page, max_page=search_page)
        # if exactly 20, max_id search with oldest tweet
        if tweets == 20:
            pass
        return tweets
        

    #                                       REFACTOR THIS SHIT
    def fetch_first_page(self):
        print 'fetching first page...'
        tweets_per_user = 3200
        max_page = 3200 / 20

        tweets = Tweet.objects.filter(user=self.user).order_by('created_at')[:tweets_per_page]
        if len(tweets) == tweets_per_page:
            return tweets

        api = tweepy.API()
        api_user = api.get_user(self.user.username)
        user_tweet_count = api_user.statuses_count
        #make sure this only happens at creation
        if user_tweet_count > tweets_per_user:
            self.user.old_timer_and_or_gabber=True
            self.user.save()

	    #except (TweepError):
	    #    return render_to_response('user_timeline.html', {'error_message':'shit'})
	    # also show join date
        first_page_num = user_tweet_count / tweets_per_page
        if first_page_num > max_page:
            first_page_num = max_page
        self.fetch_twitter_page(first_page_num)

        if user_tweet_count % tweets_per_page != 0 and first_page_num != max_page:
            first_page_num = first_page_num + 1
       	    self.fetch_twitter_page(first_page_num)

        tweets = Tweet.objects.filter(user=self.user).order_by('created_at')[:tweets_per_page]
        if len(tweets) == tweets_per_page:
            return tweets_per_page

        tweets = self.search_for_first_tweets(min_page=0, max_page=first_page_num)
        for tweet in tweets:
            Tweet.objects.get_or_create(user=self.user, text=tweet.text, created_at=tweet.created_at, tweet_id=tweet.id)

        return Tweet.objects.filter(user=self.user).order_by('created_at')[:tweets_per_page]