from .items import item_map
from django.utils import timezone
from .models import Tracked_auction
from datetime import datetime, timedelta
from itertools import groupby, product
import time

def print_status(auctions,func,time):
	auc = len(auctions)
	data = Tracked_auction.objects.all().count()
	print('{0:06d}|{1:06d}|{2:30s}|{3:.3f}'.format(auc,data,func,time))

# @param: List of all auctions from wow-api
# @return: Filtered list of auctions for relevant items with buyout prices
def item_filter(auctions):
	first_filter = filter(lambda auction: auction['item'] in item_map, auctions)
	second_filter = filter(lambda auction: auction['buyout'] != 0, first_filter)
	second_filter = list(second_filter)
	return second_filter

# Removes auctions from database that has both: 
# a) Disappeared from AH
# b) Appeared for a by same owner for a lower price in AH
# @param: List of auctions filtered for: item, buyout
def remove_relisted_auctions(auctions):
	aucs = map(lambda auction: auction['auc'], auctions)
	dead_auctions = Tracked_auction.objects.exclude(auc__in=aucs)
	deleted = False
	for dead_auction in dead_auctions:
		for new_auction in auctions:
			same_owner = dead_auction.owner == new_auction['owner']
			same_item = dead_auction.item == new_auction['item']
			lower_price = dead_auction.buyout > int(new_auction['buyout']/new_auction['quantity'])
			if same_owner and same_item and lower_price:
				not_in_database = Tracked_auction.objects.filter(auc=new_auction['auc']).count()==0
				if not_in_database:
					dead_auction.delete()
					break

# Since we weed out expired auctions before they actually disappear,
# we consider all auctions that we haven't identified as relisted
# to be sold.
# @param: List of auctions filtered for: item, buyout
def remove_sold_auctions(auctions):
	aucs = map(lambda d: d['auc'], auctions)
	sold_auctions = Tracked_auction.objects.exclude(auc__in=aucs)
	#update auction_stats
	sold_auctions.delete()

# Here we update expire-times for auctions that have changed their timeLeft-field.
# @param: List of auctions filtered for: item, buyout, relisted, sold
def update_expire_times(auctions):
	expire_times = {'LONG':12, 'MEDIUM':2, 'SHORT':0.5}

	auctions_to_look_at = Tracked_auction.objects.filter(expires__isnull=True).values()

	# magic to get list of auctions where timeLeft has changed
	hashed = {e['auc']: e['timeLeft'] for e in auctions_to_look_at}
	to_be_updated = [e for e in auctions if e['auc'] in hashed and hashed[e['auc']] != e['timeLeft']]
	
	for auction in to_be_updated:
		new_auction = Tracked_auction.objects.get(auc=auction['auc'])
		expire_in = timedelta(hours=expire_times[auction['timeLeft']])
		expire_time = timezone.now() + expire_in
		new_auction.expires = expire_time
		new_auction.timeLeft = auction['timeLeft']
		new_auction.save()

# helper-function for remove_expired_auctions
# remove all auctions with timeLeft == SHORT
# We consider these expired (being up for ~12h without selling)
def remove_SHORT():
	before = Tracked_auction.objects.all().count()
	results_SHORT = Tracked_auction.objects.filter(timeLeft='SHORT')
	# register as expired
	results_SHORT.delete()

# helper-function for remove_expired_auctions
# remove all auctions with less than 1h until projected expiration
# We consider these expired. 
def remove_close_to_expire():
	time_threshold_tracked = timezone.now() + timedelta(hours=1)
	close_to_expire = Tracked_auction.objects.filter(expires__lt=time_threshold_tracked)
	# register as expired
	close_to_expire.delete()

# helper function for remove_expired_auctions
# remove all auctions that has been up for over 23h since recorded.
# We consider these expired
def remove_old_untracked():
	time_threshold_missed = timezone.now() - timedelta(hours=23)
	missed_and_untracked = Tracked_auction.objects.filter(created__lt=time_threshold_missed)
	# register as expired
	missed_and_untracked.delete()

# removing all auctions that should expire soon
# and count these as expired
def remove_expired_auctions():
	remove_SHORT()
	remove_close_to_expire()
	remove_old_untracked()

# @param: List of auctions filtered for: item, buyout
# @return: List of auctions filtered for: item, buyout, cheapest, timeLeft
def auction_filter(auctions):
	first_filter = [next(auction) for _, auction in groupby(auctions, key = lambda x: x['item'])]
	second_filter = list(filter(lambda auction: auction['timeLeft'] == 'VERY_LONG' or auction['timeLeft'] == 'LONG', first_filter))
	return second_filter

# Add all auctions of our tracked items, with a buyout price, that are the 
# cheapest listed with a LONG or VERY LONG time left
# @param: List of auctions filtered for: item, buyout, cheapest, timeLeft
def update_auctions(auctions):
	current_ids = Tracked_auction.objects.values_list('auc',flat=True)
	for auction in auctions:
		if auction['auc'] not in current_ids:
			item, created = Tracked_auction.objects.get_or_create(
				auc = auction['auc'],
			)
			if created:
				item.item = auction['item']
				item.owner = auction['owner']
				item.name = item_map[auction['item']]
				item.buyout = int(auction['buyout']/auction['quantity'])
				item.quantity = auction['quantity']
				item.timeLeft = auction['timeLeft']
				item.save()