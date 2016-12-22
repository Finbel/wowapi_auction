import csv 
import operator
import codecs
from urllib.request import urlopen

url = 'http://www.wowuction.com/eu/darkmoon-faire/horde/Tools/RealmDataExportGetFileStatic?type=csv&token=aD2j4zCuLSm7p3JfrbAv8A2'
response = urlopen(url)

# file to write to
items = open('items.py', 'w')

reader = csv.DictReader(codecs.iterdecode(response, 'utf-8'), delimiter=',', quotechar='|')
sortedlist = sorted(reader, key=lambda x: float(operator.itemgetter('14-day Todays PMktPrice')(x)), reverse=True)

items.write('item_map = {\n')
for row in sortedlist:
	name = row['Item Name']
	item_id = row['Item ID']
	posted = float(row['Avg Daily Posted'])
	if(posted > 10):
		if "\"" not in name: 
			items.write("\t"+item_id+' : "'+name+'",\n')
		else:
			items.write('\t'+item_id+" : '"+name+"',\n")
items.write("}")