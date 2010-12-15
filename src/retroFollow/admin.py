from django.contrib import admin
from retroFollow.models import UserTwitter

class UserTwitterAdmin(admin.ModelAdmin):
    pass

admin.site.register(UserTwitter, UserTwitterAdmin)