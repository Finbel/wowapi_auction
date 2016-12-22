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