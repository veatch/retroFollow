from datetime import datetime, timedelta
from django.core.management.base import BaseCommand

from retroFollow.models import Following, RetroTweetSchedule, Tweet, TweetSchedule, UserTwitter
from retroFollow.util import fetch_page, send_retro_tweets
from settings import tweets_per_page

class Command(BaseCommand):
    def handle(self, *args, **options):
        user = UserTwitter.objects.get(username_slug='veatch')
        now = datetime.now()

        retro_tweet_schedule = RetroTweetSchedule.objects.get(user=user)#order_by('last_tweet_attempt_time',)[0]#ever not 0?
        #if retro_tweet_schedule.next_update_time < now:# update next_update_time after update somehow
        users_to_update = [following.author for following in Following.objects.filter(follower=user).exclude(tweetschedule__scheduled_time__gt=now)]
        if users_to_update:
            for author in users_to_update:
                tweet_count = Tweet.objects.filter(user=author).count()

                following = Following.objects.get(author=author, follower=user)
                scheduled_tweet_count = TweetSchedule.objects.filter(follow=following).count()

                if scheduled_tweet_count >= tweet_count:
                    page = tweet_count / tweets_per_page or 1
                    fetch_page(author.username_slug, page)# for now, don't allow retroFollowing of protected accounts
                    # todo: some kind of check that everything is, in fact, up to date

                tweet_schedules = TweetSchedule.objects.filter(follow__author=author).order_by('tweet_id')
                if tweet_schedules:
                    min_id = tweet_schedules[0].tweet_id
                else:
                    min_id = 0
                tweets_to_schedule = Tweet.objects.filter(user=author).filter(tweet_id__gt=min_id).order_by('tweet_id')[:tweets_per_page]
                for tweet in tweets_to_schedule:
                    tweet.create_schedule(follow=following, scheduled_time=tweet.created_at+timedelta(days=following.tweet_time_delta))

        # if latest scheduled time is less than now, pull more

        # todo: need to be able to add users to a list to follow, and then base delta on earliest tweet
        #
        # update last_successful_tweet_time so future runs will work
        #

        tweets = TweetSchedule.objects.filter(follow__follower=user,
            scheduled_time__range=(retro_tweet_schedule.last_successful_tweet_time, now)).order_by('tweet_id')#orderby # why select_related?
        if tweets:
            send_retro_tweets(tweets)
            retro_tweet_schedule.last_successful_tweet_time = now
            retro_tweet_schedule.save()
        # select tweets with foreign key, or should we store ids and select with list of ids?

        # need to know when we've reached end of timeline so we don't keep trying to pull new stuff