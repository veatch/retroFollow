from django.core.urlresolvers import reverse
from django.db import models

class UserTwitter(models.Model):
    username = models.CharField(unique=True, max_length=32)
    username_slug = models.CharField(unique=True, max_length=32)
    old_timer_and_or_gabber = models.BooleanField(default=False)
    utc_offset = models.IntegerField(blank=True, null=True)
    is_protected = models.BooleanField(default=True)
    retro_followers = models.ManyToManyField('self', symmetrical=False, through='Following')

class Following(models.Model):
    author = models.ForeignKey(UserTwitter, related_name='followers')
    follower = models.ForeignKey(UserTwitter, related_name='following')
    tweet_time_delta = models.FloatField()

class Tweet(models.Model):
    user = models.ForeignKey(UserTwitter, related_name='tweets')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField()#timezone?
    tweet_id = models.BigIntegerField(unique=True)

    def get_absolute_url(self):
        return reverse('rf_single_tweet', args=[self.user.username, self.tweet_id])

    def create_schedule(self, follow, scheduled_time):
        t = TweetSchedule(follow=follow, tweet_id=self.tweet_id, scheduled_time=scheduled_time)
        t.save()

class TweetSchedule(models.Model):
    follow = models.ForeignKey(Following)
    tweet_id = models.BigIntegerField()
    scheduled_time = models.DateTimeField() # just created_at + user_following_through.timedelta

# maybe pre-load everybody you follow, and keep track of update_needed_at a few hours/days early so we don't miss anything if we have failures

# I think this class might be useful when there are a lot of users.
# You could find earliest successful tweet time, and run the tweet schedule for that user.
# Let's start with just one user, and we'll worry about scheduling later
# NO. You need last successful tweet time somewhere to calculate range in management command.
class RetroTweetSchedule(models.Model):
    user = models.ForeignKey(UserTwitter)
    last_tweet_attempt_time = models.DateTimeField()
    last_successful_tweet_time = models.DateTimeField()
    next_update_time = models.DateTimeField() #... for each source, find max scheduled_time, then find min of that list... subtract a few hours to build in time for failure

#for source in everybody_on_schedule:
#    if TweetSchedule.objects.filter(scheduled_time > now).count() > 0: