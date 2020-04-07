import dash
import folium
import pycountry
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import datetime
import plotly.express as px
import numpy as np
# from update_map import loadData
# from update_map import map_locations

external_stylesheets = ['./style.css']  # Stylesheet for app

app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

####################################################
# GATHERING AND PARSING DATA FOR CHARTS AND GRAPHS #
####################################################

# Functions for gathering datasets from John Hopkins's repository
base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"


def worldData(fileName, columnName):
    data = pd.read_csv(base_url + fileName) \
             .melt(id_vars=['Province/State', 'Country/Region', 'Lat', 'Long'], var_name='date', value_name=columnName) \
             .fillna('<all>')
    #data['date'] = data['date'].astype('datetime64[ns]')
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
    #data['date'] = data['date'].astype('datetime64[ns]')
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

# Transforming datasets
grouped_countries = world_data.groupby(
    ['date', 'Country/Region', 'Province/State']).agg({
        'Confirmed': 'max',
        'Deaths': 'max'
    }).reset_index()
grouped_states = us_data.groupby(
    ['date', 'Province_State', 'FIPS', 'Lat', 'Long_']).agg({
        'Confirmed': 'max',
        'Deaths': 'max'
    }).reset_index()


# Opening pickled country code dictionary
complete_country_code_dict = pd.read_pickle(
    'pickled_files/complete_country_code_dict.pkl')

# Mapping codes to countries in dataset
grouped_countries['code'] = grouped_countries['Country/Region'].map(
    complete_country_code_dict) # Dictionary previously prepared (see code)
# # Double checking missing values
# missing_codes = len(
#     grouped_countries[grouped_countries.code == 'Unknown code'][[
#         'Country/Region'
#     ]])
# print(f'There are {missing_codes} missing 3-letter codes in dataset')
# print('-------')
# grouped_countries.head()


# Opening pickled country code dictionary
complete_country_code_dict = pd.read_pickle('pickled_files/complete_country_code_dict.pkl')

# Mapping codes to countries in dataset
grouped_countries['code'] = grouped_countries['Country/Region'].map(complete_country_code_dict)
# Double checking missing values
# missing_codes = len(grouped_countries[grouped_countries.code == 'Unknown code'][['Country/Region']])
# print(f'There are {missing_codes} missing 3-letter codes in dataset')
# print('-------')
# grouped_countries.head()

# Last time data was updated
last_update = grouped_countries.date.max()

##############
# CHOROPLETH #
##############

global_data = grouped_countries.groupby(['Country/Region', 'code']).agg({
    'Confirmed':
    'max',
    'Deaths':
    'max'
}).reset_index()


def world_map():

    fig = px.choropleth(
        global_data,
        locations='code',
        #title="Global COVID-19 Cases",
        hover_name="Country/Region",
        hover_data=["Confirmed", "Deaths"],
        #color=np.log10(global_data["Confirmed"]),
        color=global_data["Confirmed"],
        color_continuous_scale='Reds',
        range_color=(0, 30000),
        # labels={
        #     'Confirmed': 'Confirmed Cases <br> (x10) <br>',
        #     'Deaths': 'Deaths'
        # },
        #featureidkey="global_data.Deaths",
        scope='world',
        # animation_frame='date'
    )
    fig.update_layout(template="plotly_dark",
                      coloraxis_showscale=False,
                      margin={
                          "r": 0,
                          "t": 0,
                          "l": 0,
                          "b": 0
                      },
                      coloraxis_colorbar=dict(
                          title="<b>Confirmed Cases</b> <br>" + "(Log Scale)",
                          tickvals=[1.5, 2.5, 3.5, 4.5],
                          ticktext=["100", "1k", "10k", "100k"],
                          thicknessmode="pixels",
                          thickness=10,
                          lenmode="pixels",
                          len=200,
                      ),
                      hovermode="x",
                      hoverlabel=dict(
                          bgcolor="#20244a",
                          font_size=16,
                      ),
                      geo=dict(showframe=False,
                               showcoastlines=False,
                               projection_type='equirectangular'))

    fig.update_traces(hovertemplate='<b>' + global_data['Country/Region'] +
                          '</b>' + '<br>' + 'Confirmed Cases: ' +
                          [str((f"{num:,d}")) for num in global_data['Confirmed']] + '<br>' +
                          'Deaths: ' + [str((f"{num:,d}")) for num in global_data['Deaths']] +
                          '<extra></extra>')
    return fig


world_map = world_map()

################
# TOTALS CARDS #
################

total_confirmed = global_data.Confirmed.sum()
total_deaths = global_data.Deaths.sum()


card_content1 = [
    dbc.CardHeader("Total Confirmed Cases"),
    dbc.CardBody([
        html.H5(f'{total_confirmed:,}', className="confirmed-cases"),
        html.P(
            "This is some card content that we'll reuse",
            className="card-text",
        ),
    ]),
]

card_content2 = [
    dbc.CardHeader("Total Deaths"),
    dbc.CardBody([
        html.H5(f'{total_deaths:,}', className="deaths"),
        html.P(
            "This is some card content that we'll reuse",
            className="card-text",
        ),
    ]),
]


####################
# DASHBOARD LAYOUT #
####################

app.layout = dbc.Container([
    dbc.Jumbotron([
        html.H1("Coronavirus (COVID-19) Dashboard", className="display-3"),
        html.P(
            "Last updated: " + last_update,
            className="lead",
        )
    ]),
    dbc.Row(
        dcc.RadioItems(id='radio',
                       options=[{
                           'label': '  Confirmed Cases',
                           'value': 'confirmed'
                       }, {
                           'label': '  Deaths',
                           'value': 'deaths'
                       }],
                       value='deaths',
                       labelStyle={'display': 'inline-block'})),
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(id='choropleth', figure=world_map)),
                width='auto'),
        dbc.Col(children=[
            dbc.Row(
                dbc.Col(dbc.Card(
                    card_content1, color="secondary", inverse=True),
                        width="auto")),
            dbc.Row(' '),
            dbc.Row(
                dbc.Col(dbc.Card(card_content2, color="danger", inverse=True),
                        width="auto"))
        ]),
    ]),
])

# app.layout = html.Div(children=[
#     html.H1(children='Coronavirus (COVID-19) Dashboard'),
#     html.Div(children='''
#         Tracking world-wide cases
#     '''),
#     html.Div([dcc.Graph(id='total-cases', figure=world_map)],
#              className="eight columns"),
#     html.Div(html.Row(children='Total Cases')),
# ])



if __name__ == '__main__':
    app.run_server(debug=True)

server = app.server
