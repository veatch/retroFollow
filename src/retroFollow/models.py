from django.core.urlresolvers import reverse
from django.db import models

class UserTwitter(models.Model):
    '''
    #class Meta:
    #    app_label='retroFollow'
    '''
    username = models.CharField(unique=True, max_length=32)
    old_timer_and_or_gabber = models.BooleanField(default=False)
    utc_offset = models.IntegerField(blank=True, null=True)
    #first_tweet_time = models.DateTimeField()
    #followers = models.ManyToManyField(RFUser, related_name='following')
    # first tweet time and id for use with new users?

class Tweet(models.Model):
    user = models.ForeignKey(UserTwitter, related_name='tweets')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField()#timezone?
    tweet_id = models.BigIntegerField()

    def get_absolute_url(self):
        return reverse('rf_single_tweet', args=[self.user.username, self.tweet_id])