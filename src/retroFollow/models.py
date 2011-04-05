from django.core.urlresolvers import reverse
from django.db import models

class UserTwitter(models.Model):
    username = models.CharField(unique=True, max_length=32)
    old_timer_and_or_gabber = models.BooleanField(default=False)
    utc_offset = models.IntegerField(blank=True, null=True)
    is_protected = models.BooleanField(default=True)

class Tweet(models.Model):
    user = models.ForeignKey(UserTwitter, related_name='tweets')
    text = models.CharField(max_length=300)
    created_at = models.DateTimeField()#timezone?
    tweet_id = models.BigIntegerField(unique=True)

    def get_absolute_url(self):
        return reverse('rf_single_tweet', args=[self.user.username, self.tweet_id])