from django.contrib import admin
from .models import Tracked_auction, LastTime

# Register your models here.
admin.site.register(Tracked_auction)
admin.site.register(LastTime)
