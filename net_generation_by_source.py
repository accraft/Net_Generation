#! python
import requests 
import pprint
import plotly.graph_objs as go
import plotly.plotly as py
import plotly 
from datetime import datetime


pp = pprint.PrettyPrinter(indent=4)

eia_api_key = "a6b68dab9928c665bccd9a853c544092"

def get_url (url):
	r = requests.get(url)
	return r.json()

	
def get_childseries (category_num):
	url = "http://api.eia.gov/category/?api_key=" + eia_api_key + "&category_id=" + str(category_num)
	return_json = get_url(url)
	return return_json['category']['childcategories'] 
#sample call below. I know 3 is the category number for net generation by source
#get_childseries(3) 

def get_seriesid_by_geo_time(series,geography='United States',timeperiod='monthly'):
	series_json = get_url("http://api.eia.gov/category/?api_key=" + eia_api_key + "&category_id=" + str(series))
	return [x for x in series_json['category']["childseries"] if geography in x['name'] and timeperiod in x['name']][0]['series_id']

def get_series_by_geo_time(series,geography='United States',timeperiod='monthly'):
	series_id = get_seriesid_by_geo_time(series,geography,timeperiod)
	series_id_results = get_url("http://api.eia.gov/series/?api_key=" + eia_api_key + "&series_id=" + series_id)
	return series_id_results['series'][0]

#sample call, returns the series ID for coal. 
#coal_series_test = get_series_by_geo_time(4,'United States','monthly')

def return_childseries_tograph(toloop):
	all_series = []
	for series in toloop:
		series_results = get_series_by_geo_time(series['category_id'])
		all_series.append(series_results)
	return all_series
	
def prep_scatter(indata,title):
	return go.Scatter( x = [datetime.strptime(d[0],'%Y%m') for d in indata['data']]
		, y = [d[1] for d in indata['data']]
		, mode='lines+markers'
		, name=title) 

	
#takes as set of results from get_childseries, loops through them, and then appends the resulting data to a list
#two_cat_sample = [x for x in get_childseries(3) if x['category_id'] < 8]
#dataseries_sample = return_childseries_tograph(two_cat_sample)
	
def main():
	#I know 3 is net generation by source
	all_resultlist = get_childseries(3)
	pp.pprint(all_resultlist)
	#relevent_resultlist = [x for x in all_resultlist if x['category_id'] < 100 ]
	#data_to_graph = return_childseries_tograph(relevent_resultlist)
	coal_data = get_series_by_geo_time(4,'United States','monthly')
	wind_data = get_series_by_geo_time(14,'United States','monthly')
	solar_data = get_series_by_geo_time(15,'United States','monthly')
	
	trace_coal = prep_scatter(solar_data,'Utility Scale Solar')
	trace_wind = prep_scatter(wind_data,'Wind')
	trace_solar = prep_scatter(coal_data,'Coal')
	
	data = [trace_solar,trace_wind,trace_coal]
	
	layout = dict(title = 'Net Generation By Source',
              xaxis = dict(title = 'Month'),
              yaxis = dict(title = 'thousand megawatthours'),
              )
	
	plotly.offline.plot({
			'data': data,
			"layout": layout}
		,filename='Net Gen by Source - line chart'
		)

if __name__ == '__main__':
	main()

'''	
all_resultlist = get_childseries(3)
relevent_resultlist = [x for x in all_resultlist if x['category_id'] < 100 ]
data_to_graph = return_childseries_tograph(relevent_resultlist)
	
#get list of all localities
#coal_test = get_url("http://api.eia.gov/category/?api_key=a6b68dab9928c665bccd9a853c544092&category_id=4")
#set([x['name'].split(":")[2].strip() for x in coal_test['category']["childseries"]])


for cat in parent['category']['childcategories']:
	category_id = cat['category_id']
	url="http://api.eia.gov/category/?api_key=a6b68dab9928c665bccd9a853c544092&category_id=" + str(category_id)
	print(url)
'''
	
	

	