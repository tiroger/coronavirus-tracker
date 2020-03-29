import dash
import folium
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import datetime

base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"

tick_font = {
    'size': 12,
    'color': "rgb(30,30,30)",
    'family': "Helvetica, sans-serif"
}

colors = {'background': '#111111', 'text': '#7FDBFF'}


def loadData(fileName, columnName):
    data = pd.read_csv(base_url + fileName) \
             .melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], var_name='date', value_name=columnName) \
             .fillna('<all>')
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


all_data = loadData("time_series_covid19_confirmed_global.csv", "CumConfirmed") \
    .merge(loadData("time_series_covid19_deaths_global.csv", "CumDeaths")) \
    .merge(loadData("time_series_covid19_recovered_global.csv", "CumRecovered"))

all_data['location'] = list(zip(all_data['Lat'], all_data['Long']))

countries = sorted(all_data['Country/Region'].unique())

# Grouping data by country
grouped_country = all_data.groupby('Country/Region').max().reset_index()
grouped_country.drop('Province/State', axis=1, inplace=True)
total_confirmed = grouped_country['CumConfirmed'].sum().astype(str)
total_deaths = grouped_country['CumDeaths'].sum().astype(str)
#print(total_confirmed)
#print(total_deaths)
last_updated = grouped_country.date.iloc[-1].strftime("%d-%B-%Y")

# For map
# latitude = 34.717911
# longitude = -40.819474

# locations = all_data['location']
# confirmed_cases = all_data.CumConfirmed
# deaths = all_data.CumDeaths
# countries = all_data['Country/Region']

def map_locations():

    # For map
    latitude = 34.717911
    longitude = -40.819474

    locations = all_data['location']
    confirmed_cases = all_data.CumConfirmed
    deaths = all_data.CumDeaths
    countries = all_data['Country/Region']
    corona_map = folium.Map(location=[latitude, longitude], zoom_start=3)

    for location, confirmed, death, country in zip(locations, confirmed_cases,
                                                   deaths, countries):
        folium.CircleMarker(
            location,
            color='#3186cc',
            weight=0.1,
            fill_color='#C23208',
            fill=True,
            fill_opacity=0.1,
            tooltip=('<H6>' + country + '</H6>' + '<br>'
                     'Confirmed: ' + '<strong style="color:#C23208;">' +
                     str(confirmed) + '</strong>' + '<br>'
                     'Deaths: ' + '<strong style="color:#C23208;">' +
                     str(death) + '</strong>' + '<br>')).add_to(corona_map)
    return corona_map

location_map = map_locations() # Uncomment if timeout
location_map.save(outfile='location_map.html') # Uncomment if timeout