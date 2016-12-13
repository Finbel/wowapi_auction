from django.shortcuts import render
from wowapi import WowApi
import os



# Create your views here.
def front(request):
	os.environ["WOWAPI_APIKEY"] = "rcbwq4apsrc5qyu28t6ffmzhegpqx2k3"
	auctions = WowApi.get_auctions('eu', 'Darkmoon%20Faire')
	string = '{0:30}'.format(str(auctions)[0:30])
	return render(request, 'wowapi_app/front.html', {'string' : string})