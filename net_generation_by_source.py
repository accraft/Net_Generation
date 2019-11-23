#! python
import requests 
import pprint
import pandas as pd
import plotly.graph_objs as go
import plotly.plotly as py
import plotly 
import sys
from datetime import datetime

pp = pprint.PrettyPrinter(indent=4)

eia_api_key = open(".\eia_api_key.txt", "r").read() 

def get_url (url):
	r = requests.get(url)
	return r.json()
	
def get_childseries (category_num):
	url = "http://api.eia.gov/category/?api_key=" + eia_api_key + "&category_id=" + str(category_num)
	return_json = get_url(url)
	return {'title':return_json['category']['name']
			,'data':return_json['category']['childcategories']}
#sample call below. I know 3 is the category number for net generation by source
#get_childseries(3) 

def get_seriesid_by_geo_time(series,geography='United States',timeperiod='monthly'):
	series_json = get_url("http://api.eia.gov/category/?api_key=" + eia_api_key + "&category_id=" + str(series))
	try: 
		return [x for x in series_json['category']["childseries"] if geography in x['name'] and timeperiod in x['name']][0]['series_id']
	except IndexError:
		return "Does not exist"
#returns the category ID, which is used to actually pull the data. Sample call below:
#get_seriesid_by_geo_time(4,"Oregon","quarterly")
		
def get_series_by_geo_time(series,geography='United States',timeperiod='monthly'):
	series_id = get_seriesid_by_geo_time(series,geography,timeperiod)
	if series_id == 'Does not exist':
		return 'Does not exist'
	else:
		series_id_results = get_url("http://api.eia.gov/series/?api_key=" + eia_api_key + "&series_id=" + series_id)
		return series_id_results['series'][0]
#sample call, returns the series ID for coal. 
#coal_series_test = get_series_by_geo_time(4,'United States','monthly')

	
def prep_scatter(in_x,indata,title,visible=True):
	return go.Scatter( x = [datetime.strptime(d,'%Y%m') for d in in_x]
		, y = indata
		, mode='lines+markers'
		, name=title
		, visible=visible
		, hoverlabel = dict(namelength = -1)) 
#function to prepare the scatter plot 

def prep_source_df(geo_series_by_geo_time_result,name):
	date_list = []
	value_list = []
	
	for rec in geo_series_by_geo_time_result['data']:
		date_list.append(rec[0])
		value_list.append(rec[1])
	df_results = pd.DataFrame(data={'date':date_list,name:value_list})
	return df_results	
#gets source data and converts it into a two column dataframe: date, value. 


def return_geographies(category_num=3,include_totals=False):
	url = "http://api.eia.gov/category/?api_key=" + eia_api_key + "&category_id=" + str(category_num)
	return_json = get_url(url)
	
	all_geographies_list = [x['name'].split(":")[2] for x in return_json['category']['childseries']]
	#a sample name looks like this 'Net generation : all fuels : Arizona : all sectors : monthly', so it's necessary to only snag the geography
	
	all_geographies_list = list(set(all_geographies_list))
	#de-dup because there are options to pull monthly, quarterly and annual data.
	
	#remove regional totals
	all_geographies_list_extotals = [x for x in all_geographies_list if x.find('total') == -1]
	
	
	if include_totals==0:
		all_geographies_list_extotals.sort()
		return all_geographies_list_extotals
	else:
		all_geographies_list.sort()
		return all_geographies_list
#returns a list of all geographies you can pull. 

#takes as set of results from get_childseries, loops through them, and then appends the resulting data to a list
#two_cat_sample = [x for x in get_childseries(3) if x['category_id'] < 8]
#dataseries_sample = return_childseries_tograph(two_cat_sample)
	
def main():
	#I know 3 is net generation by source
	all_resultlist = get_childseries(3)
	pp.pprint(return_geographies(include_totals=True))
	geography_input = input('Input Geography from the above list: ')
	#relevent_resultlist = [x for x in all_resultlist if x['category_id'] < 100 ]
	#data_to_graph = return_childseries_tograph(relevent_resultlist)
	
	all_resultlist_tograph = [x for x in all_resultlist['data'] if (len(str(x['category_id'])) < 3 or x['name'] == 'All fuels') and x['name'] != 'Other renewables (total)' ]
	#create shell of dataframe to join source data to. 
	df_net_gen_results = pd.DataFrame(columns={'date'})
	df_net_gen_results_ttm = pd.DataFrame(columns={'date'})
	for source in all_resultlist_tograph:
		series_data = get_series_by_geo_time(source['category_id'],geography_input,'monthly')
		if series_data == 'Does not exist':
			continue
		df_tojoin = prep_source_df(series_data,source['name'])
		df_net_gen_results = df_net_gen_results.merge(df_tojoin,how='outer',on='date')
		
		df_tojoin_ttm = pd.DataFrame({'date':df_tojoin['date'] , source['name']:df_tojoin[source['name']][::-1].rolling(window=12).mean()[::-1]})
		df_net_gen_results_ttm = df_net_gen_results_ttm.merge(df_tojoin_ttm,how='outer',on='date')
	
	chart_data = []
	non_ttm_visible = []
	for column in df_net_gen_results:
		if column != 'date' and column != 'All fuels':
			chart_data.append(prep_scatter(df_net_gen_results['date'],df_net_gen_results[column],column))	
			non_ttm_visible.append(True)
	
	for column in df_net_gen_results_ttm:
		if column != 'date' and column != 'All fuels':
			chart_data.append(prep_scatter(df_net_gen_results_ttm['date'],df_net_gen_results_ttm[column],column,visible=False))	
			non_ttm_visible.append(False)
	
	ttm_visible = [not i for i in non_ttm_visible]
	
	updatemenus = list([
		dict(active=0,
			 buttons=list([   
				dict(label = 'Actual',
					 method = 'update',
					 args = [{'visible': non_ttm_visible}]),
				dict(label = 'TTM',
					 method = 'update',
					 args = [{'visible': ttm_visible}])
				])
			)])

	
	layout = dict(title = 'Net Generation By Source - ' + geography_input,
              xaxis = dict(title = 'Month'),
              yaxis = dict(title = 'thousand megawatthours'),
			  hovermode = 'closest',
              updatemenus = updatemenus
			  )
	
	plotly.offline.plot({
			'data': chart_data,
			"layout": layout}
		,filename='Net Gen by Source - line chart'
		)

if __name__ == '__main__':
	main()

'''	
#get list of all localities
#coal_test = get_url("http://api.eia.gov/category/?api_key=a6b68dab9928c665bccd9a853c544092&category_id=4")
#set([x['name'].split(":")[2].strip() for x in coal_test['category']["childseries"]])


for cat in parent['category']['childcategories']:
	category_id = cat['category_id']
	url="http://api.eia.gov/category/?api_key=a6b68dab9928c665bccd9a853c544092&category_id=" + str(category_id)
	print(url)
'''
	
	

	
