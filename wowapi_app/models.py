from django.db import models
from .items import item_map 

# Create your models here.
class Tracked_auction(models.Model):
    auc = models.IntegerField(default=0,primary_key=True)
    item = models.IntegerField(default=-1)
    name = models.CharField(null=True,max_length=200)
    owner = models.CharField(max_length=200)
    buyout = models.IntegerField(default=-1)
    quantity = models.IntegerField(default=-1)
    timeLeft = models.CharField(max_length=200)
    created = models.DateTimeField(auto_now_add=True)
    expires = models.DateTimeField(null=True,blank=True)

    def __str__(self):
    	return self.name

class LastTime(models.Model):
	last_time = models.IntegerField(default=1482685189000)

class Auction_history(models.Model):
	auc = models.IntegerField(default=0,primary_key=True)
	item = models.IntegerField(default=-1)
	owner = models.CharField(max_length=200)
	buyout = models.IntegerField(default=-1)
	quantity = models.IntegerField(default=-1)
	created = models.DateTimeField(null=True,blank=True)
	ended = models.DateTimeField(auto_now_add=True)
	end_type = models.CharField(max_length=200)

class Auction_stats(models.Model):
	item = models.IntegerField(default=-1)
	buyout = models.IntegerField(default=-1)
	sold = models.IntegerField(default=0)
	expired = models.IntegerField(default=0)
	relisted = models.IntegerField(default=0)

	class Meta:
		unique_together = ("item", "buyout")