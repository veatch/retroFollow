import re

from django import template
from django.template.defaultfilters import stringfilter
from django.utils.safestring import mark_safe
from functools import partial

register = template.Library()

# This was taken from readmindme and modified.
# http://code.google.com/p/readmindme/
# readmindme.templatetags.tags

AT_RE = re.compile(r'(?P<prefix>(?:\W|^)@)(?P<username>[a-zA-Z0-9_]+)\b')
#TWITTER_LINK = ('%(prefix)s<a href="http://twitter.com/%(username)s">'
#                '%(username)s</a>')

def user_page_link(host):
    link_sub_strings = ['%(prefix)s<a href="http://', host, '/%(username)s">%(username)s</a>']
    return ''.join(link_sub_strings)

def _SubAtReply(match, host):
    #return TWITTER_LINK % match.groupdict()
    return user_page_link(host) % match.groupdict()

@register.filter
@stringfilter
def atreply(value, host):
    return mark_safe(AT_RE.sub(partial(_SubAtReply, host=host), value))

# end readmindme
#################################################

# need to validate input, check for javascript, etc?