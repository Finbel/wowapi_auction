from django.shortcuts import render
from .items import item_map
from .functions import update_auctions, remove_relisted_auctions, item_filter, remove_sold_auctions, remove_expired_auctions, update_expire_times, auction_filter, print_status
import json
import os
import requests
import operator
from operator import itemgetter
from .models import Tracked_auction
import time

# Create your views here.
def front(request):
	return render(request, 'wowapi_app/front.html', {})

def update(request):
	# The URL as a string
	url = 'https://eu.api.battle.net/wow/auction/data/darkmoon%20faire?locale=en_GB&apikey=rcbwq4apsrc5qyu28t6ffmzhegpqx2k3'
	# Send a request for the url and get a Response object
	response = requests.get(url)
	# Turn the Response object into a json 
	json_obj = response.json()
	# Get the URL to the AH-json from the json.
	url = json_obj['files'][0]['url']
	# Send a request for the url and get a Response object
	response = requests.get(url)
	# Turn the response object into a json
	json_obj = response.json()
	# Get all of the auctions from the json
	auctions = json_obj['auctions']
	print()
	print("input | data |{0:30s}|time".format("function"))
	print_status(auctions,'start',time.time()-time.time())
	# Filter for item_list and buyout != 0
	time1 = time.time()
	auctions = item_filter(auctions)
	time2 = time.time()
	print_status(auctions,'item_filter',time2-time1)

	# Sort list primary by item, secondary on buyout
	time1 = time.time()
	auctions.sort(key=itemgetter('item','buyout'))
	time2 = time.time()
	print_status(auctions,'sort',time2-time1)

	# Remove relisted auctions from database
	time1 = time.time()
	remove_relisted_auctions(auctions)
	time2 = time.time()
	print_status(auctions,'remove_relisted_auctions',time2-time1)

	# Remove sold auctions from database
	time1 = time.time()
	remove_sold_auctions(auctions)
	time2 = time.time()
	print_status(auctions,'remove_sold_auctions',time2-time1)

	# Update time_class and expires for tracked_auctions
	time1 = time.time()
	update_expire_times(auctions)
	time2 = time.time()
	print_status(auctions,'update_expire_times',time2-time1)

	# Remove auctions that will soon expire and count as expired.
	time1 = time.time()
	remove_expired_auctions()
	time2 = time.time()
	print_status(auctions,'remove_expired_auctions',time2-time1)

	# Sort out the cheapest ones and timeLeft = 'LONG' or 'VERY_LONG'
	time1 = time.time()
	auctions = auction_filter(auctions)
	time2 = time.time()
	print_status(auctions,'auction_filter',time2-time1)
	
	# add auctions to database
	time1 = time.time()
	update_auctions(auctions)
	time2 = time.time()
	print_status(auctions,'update_auctions',time2-time1)
	print()
	return render(request, 'wowapi_app/update.html', {})

def look(request):
	auctions = Tracked_auction.objects.all().order_by('created')
	return render(request, 'wowapi_app/look.html', {'auctions' : auctions})	