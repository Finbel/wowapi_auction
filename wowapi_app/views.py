from django.shortcuts import render
from wowapi import WowApi
import os
import requests



# Create your views here.
def front(request):
	#os.environ["WOWAPI_APIKEY"] = "rcbwq4apsrc5qyu28t6ffmzhegpqx2k3"
	#auctions = WowApi.get_auctions('eu', 'Darkmoon%20Faire')
	url = 'https://eu.api.battle.net/wow/auction/data/darkmoon%20faire?locale=en_GB&apikey=rcbwq4apsrc5qyu28t6ffmzhegpqx2k3'
	response = requests.get(url)
	string = str(response.json())
	return render(request, 'wowapi_app/front.html', {'string' : string})