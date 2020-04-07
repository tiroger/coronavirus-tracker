#######################
# IMPORTING LIBRARIES #
#######################

import pandas as pd
import numpy as np

import pycountry  # To convert country names to 3 letter code
import webbrowser

import plotly.graph_objs as go
import plotly.express as px
from plotly.subplots import make_subplots

import pickle

################
# DATA PARSING #
################

# Functions for gathering datasets from John Hopkins's repository
base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"


def worldData(fileName, columnName):
    data = pd.read_csv(base_url + fileName) \
             .melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], var_name='date', value_name=columnName) \
             .fillna('<all>')
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


def usData(fileName, columnName):
    data = pd.read_csv(base_url + fileName) \
             .melt(id_vars=['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State',
       'Country_Region', 'Lat', 'Long_', 'Combined_Key'], var_name='date', value_name=columnName) \
             .fillna('<all>')
    # Get names of indexes for which column Date has extra strings has value 30
    indexNames = data[data['date'] == 'Population'].index
    # Delete these row indexes from dataFrame
    data.drop(indexNames, inplace=True)
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


########################

# US data
us_data = usData("time_series_covid19_confirmed_US.csv", "Confirmed") \
    .merge(usData("time_series_covid19_deaths_US.csv", "Deaths"))
us_data.head()

# World data
world_data = worldData("time_series_covid19_confirmed_global.csv", "Confirmed") \
    .merge(worldData("time_series_covid19_deaths_global.csv", "Deaths"))
world_data.head()

########################