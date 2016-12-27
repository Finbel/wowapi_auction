from .items import item_map
from django.utils import timezone
from .models import Tracked_auction, Auction_history, Auction_stats
from datetime import datetime, timedelta
from itertools import groupby, product, chain
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
					dead_auc, created = Auction_history.objects.get_or_create(
						auc = dead_auction.auc,
					)
					if created:
						dead_auc.item = dead_auction.item
						dead_auc.owner = dead_auction.owner
						dead_auc.buyout = dead_auction.buyout
						dead_auc.quantity = dead_auction.quantity
						dead_auc.created = dead_auction.created
						dead_auc.end_type = 'RELISTED'
						dead_auc.save()

					auction, created = Auction_stats.objects.get_or_create(
						item = dead_auction.item,
						buyout = dead_auction.buyout
					)
					if created:
						auction.relisted += 1
						auction.save()

					dead_auction.delete()
					break

# Since we weed out expired auctions before they actually disappear,
# we consider all auctions that we haven't identified as relisted
# to be sold.
# @param: List of auctions filtered for: item, buyout
def remove_sold_auctions(auctions):
	aucs = map(lambda d: d['auc'], auctions)
	sold_auctions = Tracked_auction.objects.exclude(auc__in=aucs)
	for sold_auction in sold_auctions:
		sold_auc, created = Auction_history.objects.get_or_create(
			auc = sold_auction.auc
		)
		if created:
			sold_auc.item = sold_auction.item
			sold_auc.owner = sold_auction.owner
			sold_auc.buyout = sold_auction.buyout
			sold_auc.created = sold_auction.created
			sold_auc.quantity = sold_auction.quantity
			sold_auc.end_type = 'SOLD'
			sold_auc.save()

		auction, created = Auction_stats.objects.get_or_create(
			item = sold_auction.item,
			buyout = sold_auction.buyout
		)
		auction.sold += 1
		auction.save()
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
	return Tracked_auction.objects.filter(timeLeft='SHORT')

# helper-function for remove_expired_auctions
# remove all auctions with less than 1h until projected expiration
# We consider these expired. 
def remove_close_to_expire():
	time_threshold_tracked = timezone.now() + timedelta(hours=1)
	return Tracked_auction.objects.filter(expires__lt=time_threshold_tracked)

# helper function for remove_expired_auctions
# remove all auctions that has been up for over 23h since recorded.
# We consider these expired
def remove_old_untracked():
	time_threshold_missed = timezone.now() - timedelta(hours=23)
	return Tracked_auction.objects.filter(created__lt=time_threshold_missed)

# removing all auctions that should expire soon
# and count these as expired
def remove_expired_auctions():
	query1 = remove_SHORT()
	query2 = remove_close_to_expire()
	query3 = remove_old_untracked()
	expired_auctions = query1 | query2 | query3
	for expired_auction in expired_auctions:
		expired_auc, created = Auction_history.objects.get_or_create(
			auc = expired_auction.auc
		)
		if created:
			expired_auc.item = expired_auction.item
			expired_auc.owner = expired_auction.owner
			expired_auc.buyout = expired_auction.buyout
			expired_auc.quantity = expired_auction.quantity
			expired_auc.created = expired_auction.created
			expired_auc.end_type = 'SOLD'
			expired_auc.save()

		auction, created = Auction_stats.objects.get_or_create(
			item = expired_auction.item,
			buyout = expired_auction.buyout
		)
		auction.expired += 1
		auction.save()
		expired_auction.delete()

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
	auctions2 = [a for a in auctions if a['auc'] not in current_ids] 
	time1 = time.time()
	for auction in auctions2:
		item = Tracked_auction(
			auc = auction['auc']#,
#			item = auction['item'],
#			owner = auction['owner'],
#			name = item_map[auction['item']],
#			buyout = int(auction['buyout']/auction['quantity']),
#			quantity = auction['quantity'],
#			timeLeft = auction['timeLeft'],
			)
		item.save()
	time2 = time.time()
	print("Does adding " + str(len(auctions2)) + "objects really take " + str(time2-time1) + "seconds?")