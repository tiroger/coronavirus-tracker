#############
# LIBRARIES #
#############

import pandas as pd
import numpy as np
from datetime import datetime
import datetime
import pycountry

import plotly.express as px
import plotly.graph_objects as go
import folium

import dash

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

#############

#external_stylesheets = ['./style.css']  # Stylesheet for app

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

####################################################
# GATHERING AND PARSING DATA FOR CHARTS AND GRAPHS #
####################################################
base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"

# Functions for gathering datasets from John Hopkins's repository
def world_data():
    data = pd.read_csv(
        'https://raw.githubusercontent.com/datasets/covid-19/master/data/countries-aggregated.csv',
        parse_dates=['Date'])
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
world_data = world_data()
world_data.head()

########################

# Transforming datasets
#sorting based on confirmed cases to identify top-10 countries with highest confirmed cases
grouped = world_data.groupby(['Country']).agg({
    'Confirmed': 'max',
    'Deaths': 'max'
}).sort_values(by=['Confirmed'], ascending=False).reset_index()
top_10 = list(grouped.Country[0:10])
top_10

df_select = world_data[world_data['Country'].isin(top_10)].copy()
df_select


grouped_states = us_data.groupby(
    ['date', 'Province_State', 'FIPS', 'Lat', 'Long_']).agg({
        'Confirmed': 'max',
        'Deaths': 'max'
    }).reset_index()


# Opening pickled country code dictionary
complete_country_code_dict = pd.read_pickle(
    'pickled_files/complete_country_code_dict.pkl')

# Mapping codes to countries in dataset
# Mapping codes to countries in dataset
grouped['code'] = grouped['Country'].map(complete_country_code_dict)
# Double checking missing values
missing_codes = len(grouped[grouped.code == 'Unknown code'][['Country']])
print(f'There are {missing_codes} missing 3-letter codes in dataset')
print('-------')
grouped.head()


# # Opening pickled country code dictionary
# complete_country_code_dict = pd.read_pickle('pickled_files/complete_country_code_dict.pkl')

# # Mapping codes to countries in dataset
# grouped_countries['code'] = grouped_countries['Country/Region'].map(complete_country_code_dict)
# # Double checking missing values
# # missing_codes = len(grouped_countries[grouped_countries.code == 'Unknown code'][['Country/Region']])
# # print(f'There are {missing_codes} missing 3-letter codes in dataset')
# # print('-------')
# # grouped_countries.head()

# # Last time data was updated
last_update = world_data.Date.max()

##############
# CHOROPLETH #
##############

def world_map():

    fig = px.choropleth(
        grouped,
        locations='code',
        #title="Custom layout.hoverlabel formatting",
        hover_name="Country",
        hover_data=["Confirmed", "Deaths"],
        color=grouped["Confirmed"],
        color_continuous_scale='Reds',
        #range_color=(0, 100),
        labels={
            'Confirmed': 'Confirmed Cases <br> (x10) <br>',
            'Deaths': 'Deaths'
        },
        #featureidkey="global_data.Deaths",
        scope='world',
        #animation_frame=grouped.Date.astype(str)
    )
    fig.update_layout(
        template="plotly_dark",
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        },
        coloraxis_showscale=False,  # Set to True to show colorscale bar
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
            bgcolor="#BF4025",
            font_size=16,
        ),
        geo=dict(showframe=False,
                 showcoastlines=False,
                 projection_type='equirectangular'))

    fig.update_traces(hovertemplate='<b>' + grouped['Country'] + '</b>' +
                      '<br>' + 'Confirmed Cases: ' +
                      grouped['Confirmed'].astype(str) + '<br>' + 'Deaths: ' +
                      grouped['Deaths'].astype(str))
    return fig


world_map = world_map()

################
# TOTALS CARDS #
################

total_confirmed = grouped.Confirmed.sum()
total_deaths = grouped.Deaths.sum()


card_content1 = [
    dbc.CardHeader("CONFIRMED CASES"),
    dbc.CardBody([
        html.H5(f'{total_confirmed:,}', className="aggregates"),
        html.P(
            "                     ",
            className="card-text",
        ),
    ]),
]

card_content2 = [
    dbc.CardHeader("DEATHS"),
    dbc.CardBody([
        html.H5(f'{total_deaths:,}', className="aggregates"),
        html.P(
            "                    ",
            className="card-text",
        ),
    ]),
]


##############
# LINE CHART #
##############


def lineChart():

    fig = px.line(df_select, x="Date", y="Confirmed", color='Country')
    fig.update_xaxes(title='')
    fig.update_yaxes(title='Cummulative Cases')
    # fig.update_traces(textposition='top center')

    # fig.update_traces(texttemplate='%{text:.2s}')
    fig.update_layout(
        title="COVID-19 Cases by Country, Top 10",
        template="plotly_dark",
        legend_orientation="h",
        margin={
            "r": 0,
            "t": 25,
            "l": 0,
            "b": 0
        },
    )

    return fig


line_chart = lineChart()



#############
# BAR CHART #
#############


def newCases():

    fig = px.bar(df_select,
                 x='Date',
                 y='Confirmed',
                 color='Country',
                 barmode='group')

    fig.update_layout(template="plotly_dark",
                      legend_orientation="h",
                      margin={
                          "r": 0,
                          "t": 25,
                          "l": 0,
                          "b": 0
                      })

    fig.update_xaxes(title='')
    fig.update_yaxes(title='New Cases per Day')

    fig.update_traces(hovertemplate='<b>' + df_select['Country'] + '</b>' +
                      '<br>' + 'Date: ' + df_select['Date'].astype(str) +
                      '<br>' + 'Confirmed Cases: ' +
                      df_select['Confirmed'].astype(str))

    return fig


bar_chart = newCases()


####################
# DASHBOARD LAYOUT #
####################

app.layout = dbc.Container([
    dbc.Jumbotron([
        html.H1("COVID-19 CORONAVIRUS PANDEMIC", className="display-3"),
        html.P(
            "Last updated: " + str(last_update),
            className="lead",
        )
    ]),
    dbc.Row(
        dcc.RadioItems(id='radio',
                       options=[{
                           'label': 'Confirmed Cases',
                           'value': 'confirmed'
                       }, {
                           'label': 'Deaths',
                           'value': 'deaths'
                       }],
                       value='confirmed',
                       labelStyle={'display': 'inline-block'})),
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(id='choropleth', figure=world_map)),
                width='16'),
        dbc.Col(children=[
            dbc.Row(
                dbc.Col(dbc.Card(
                    card_content1, color="dark", inverse=True),
                        width="12")),
            dbc.Row(' '),
            dbc.Row(
                dbc.Col(dbc.Card(card_content2, color="dark", inverse=True),
                        width="12"))
        ]),
    ]),
    dbc.Row([
        dbc.Col(
            dcc.Checklist(id='checklist',
                          options=[{
                              'label': 'Confirmed Cases',
                              'value': 'Confirmed'
                          }, {
                              'label': 'Death',
                              'value': 'Deaths'
                          }],
                          value=['Confirmed'],
                          labelStyle={'display': 'inline-block'})),
        dbc.Col(
            dcc.Dropdown(id='dropdown',
                         options=[{
                             'label': 'US',
                             'value': 'US'
                         }, {
                             'label': 'China',
                             'value': 'China'
                         }, {
                             'label': 'San Francisco',
                             'value': 'SF'
                         }],
                         value=['US', 'China'],
                         multi=True))
    ]),
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(id='lineChart', figure=line_chart)),
                width='6'),
        dbc.Col(html.Div(dcc.Graph(id='barChart', figure=bar_chart)),
                width='6'),
    ])
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
##


if __name__ == '__main__':
    app.run_server(debug=True)

server = app.server
