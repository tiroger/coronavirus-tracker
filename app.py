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


# def usData(fileName, columnName):
#     data = pd.read_csv(base_url + fileName) \
#              .melt(id_vars=['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Province_State',
#        'Country_Region', 'Lat', 'Long_', 'Combined_Key'], var_name='date', value_name=columnName) \
#              .fillna('<all>')
#     # Get names of indexes for which column Date has extra strings has value 30
#     indexNames = data[data['date'] == 'Population'].index
#     # Delete these row indexes from dataFrame
#     data.drop(indexNames, inplace=True)
#     #data['date'] = data['date'].astype('datetime64[ns]')
#     return data

# ########################

# # US data
# us_data = usData("time_series_covid19_confirmed_US.csv", "Confirmed") \
#     .merge(usData("time_series_covid19_deaths_US.csv", "Deaths"))
# us_data.head()

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
grouped['fatalityRate'] = grouped.Deaths / grouped.Confirmed * 100
top_10 = list(grouped.Country[0:10])

grouped['fatalityRate'] = round(grouped.Deaths / grouped.Confirmed * 100, 2)

# grouped['newConfirmed'] = grouped['Confirmed'].diff().fillna(0)
# grouped['newDeaths'] = grouped['Deaths'].diff().fillna(0)

grouped_country = world_data.groupby(['Country', 'Date']).agg({
    'Confirmed': 'max',
    'Deaths': 'max'
}).reset_index()
grouped_country['newConfirmed'] = grouped_country['Confirmed'].diff().fillna(0)
grouped_country['newDeaths'] = grouped_country['Deaths'].diff().fillna(0)

df_select = world_data[world_data['Country'].isin(top_10)].copy()

# grouped_states = us_data.groupby(
#     ['date', 'Province_State', 'FIPS', 'Lat', 'Long_']).agg({
#         'Confirmed': 'max',
#         'Deaths': 'max'
#     }).reset_index()

# Opening pickled country code dictionary and Mapping codes to countries in dataset
complete_country_code_dict = pd.read_pickle(
    'pickled_files/complete_country_code_dict.pkl')
# print(complete_country_code_dict)
grouped['code'] = grouped['Country'].map(complete_country_code_dict)
# Double checking missing values
# missing_codes = len(grouped[grouped.code == 'Unknown code'][['Country']])
# print(f'There are {missing_codes} missing 3-letter codes in dataset')
# print('-------')
# #grouped.head()

# Adding population data
complete_country_pop_dict = pd.read_pickle(
    'pickled_files/complete_country_pop_dict.pkl')

# Mapping population data to countries
grouped['over_65'] = grouped['Country'].map(complete_country_pop_dict)

# Opening pickled dictionary with population data and mapping to countries
pop_dict = pd.read_pickle('./pickled_files/population_dict.pkl')

# Mapping populations to countries in dataset
world_data['population'] = world_data['Country'].map(pop_dict)

# Double checking missing values
missing_populations = len(
    world_data[world_data.population.isna()][['population']])
# print(f'There are {missing_populations} missing populations in dataset')
# print('-------')
# world_data.head()

# # Calculating cases per 100,000 population
# world_data['casesPerCapita'] = world_data['Confirmed'] / world_data[
#     'population'] * 100000
# world_data['deathsPerCapita'] = world_data['Deaths'] / world_data[
#     'population'] * 100000

# # Last time data was updated
last_update = world_data.Date.max().strftime("%d-%b-%Y")

print('Data Loaded')

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
        color=np.log10(grouped["Confirmed"]),
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
    ]),
]

##############
# LINE CHART #
##############

def lineChart(country, metrics, yaxis_type, yaxisTitle=""):

    fig = px.line(world_data,
                  x=world_data[world_data['Country'] == country]['Date'],
                  y=world_data[world_data['Country'] == country][metrics])
    fig.update_xaxes(title='')
    fig.update_yaxes(title='Cummulative Cases')
    # fig.update_traces(textposition='top center')

    # fig.update_traces(texttemplate='%{text:.2s}')
    fig.update_layout(
        hovermode='x',
        title="",
        template="plotly_dark",
        legend_orientation="h",
        margin={
            "r": 0,
            "t": 50,
            "l": 0,
            "b": 0
        },
        #transition={'duration': 500},
    )
    fig.update_xaxes(showspikes=False, spikethickness=1)
    fig.update_yaxes(showspikes=False, spikethickness=1, type=yaxis_type)

    fig.update_traces(hovertemplate='Total Cases: ' + grouped_country[
        grouped_country['Country'] == country][metrics].astype(str))

    return fig

# line_chart = lineChart()


# def perCapita():

#     fig = px.line(df_select, x="Date", y="confirmedPerCapita", color='Country')
#     fig.update_xaxes(title='')
#     fig.update_yaxes(title='Cummulative Cases per 100,000')
#     # fig.update_traces(textposition='top center')

#     # fig.update_traces(texttemplate='%{text:.2s}')
#     fig.update_layout(template="plotly_dark")

#     fig.update_traces(hovertemplate='<b>' + df_select['Country'] + '</b>' +
#                       '<br>' + 'Date: ' + df_select['Date'].astype(str) +
#                       '<br>' + 'Confirmed Cases: ' +
#                       df_select['Confirmed'].astype(str))

#     return fig


#############
# BAR CHART #
#############

def newCases(country, metrics, yaxis_type, yaxisTitle=""):

    figure = px.bar(
        grouped_country,
        x=grouped_country[grouped_country['Country'] == country]['Date'][1:],
        y=grouped_country[grouped_country['Country'] == country]['new' +
                                                                 metrics][1:])

    figure.update_layout(hovermode='closest',
                         template="plotly_dark",
                         legend_orientation="h",
                         margin={
                             "r": 0,
                             "t": 50,
                             "l": 0,
                             "b": 50
                         },
                         #transition={'duration': 500}
                         )
    figure.update_xaxes(title='')
    figure.update_yaxes(title='New Cases per Day', type=yaxis_type)

    figure.update_traces(hovertemplate='Date: ' + grouped_country[
        grouped_country['Country'] == country]['Date'][1:].astype(str) +
                         '<br>' + 'New Cases: ' +
                         grouped_country[grouped_country['Country'] == country]
                         ['new' + metrics][1:].astype(str))

    return figure


# bar_chart = newCases()

######################
# Fatality Bar Chart #
######################

def fatalityRate():
    # Limiting graph to countries with more than 1000 cases
    x = grouped[grouped.Confirmed > 1000]["Country"]
    y = grouped[grouped.Confirmed > 1000]["fatalityRate"]

    fig = px.bar(grouped,
                 x=x,
                 y=y,
                 text=grouped[grouped.Confirmed > 1000]["fatalityRate"])
    fig.update_traces(texttemplate='%{text:.2s}',
                      textposition='outside',
                      marker_color='crimson',
                      marker_line_color='crimson',
                      marker_line_width=1.5,
                      opacity=0.6)
    fig.update_layout(
        xaxis={
            'categoryorder': 'total descending',
            'title': ''
        },
        template="plotly_dark",
        yaxis={'title': 'Current Fatality Rates (%) <br> Countries with >1000 cases'},
        uniformtext_minsize=9,
        uniformtext_mode='hide',
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        },
        transition={'duration': 500})
    fig.update_traces(
        hovertemplate='Country: ' +
        grouped[grouped.Confirmed > 1000]["Country"].astype(str) + '<br>' +
        'Fatality Rate: ' + round(
            grouped[grouped.Confirmed > 1000]["fatalityRate"], 2).astype(str) +
        '%')

    return fig

fatalityChart = fatalityRate()


####################
# CFR bubble chart #
####################

# Scatter of fatality rate vs population over 65
grouped['fatalityRate'] = grouped.Deaths / grouped.Confirmed * 100
grouped.loc[grouped['Deaths'] > 3000, 'Annotation'] = grouped['Country']
grouped.loc[grouped['Deaths'] <= 3000, 'Annotation'] = ''


def fatalityRate_65():
    # Limiting graph to countries with more than 1000 cases
    x = grouped["over_65"]
    y = grouped["fatalityRate"]

    fig = px.scatter(grouped,
                     x=x,
                     y=y,
                     size=grouped['Deaths'],
                     hover_name=grouped["Country"],
                     text='Annotation')
    fig.update_traces(marker_color='purple',
                      marker_line_color='red',
                      marker_line_width=1.5,
                      opacity=0.8,
                      textposition='top right')
    fig.update_layout(
        template="plotly_dark",
        yaxis={'title': 'Case Fatality Rate (%)'},
        xaxis={
            'title': 'Population of age 65 and above (% of total population)'
        },
        uniformtext_minsize=14,
        uniformtext_mode='hide',
        margin={
            "r": 0,
            "t": 0,
            "l": 0,
            "b": 0
        })

    fig.update_traces(hovertemplate='<b>' + grouped['Country'] + '</b>' +
                      '<br>' + 'CFR (%): ' +
                      round(grouped['fatalityRate'], 2).astype(str) + '<br>' + 'Population over 65: ' + grouped['over_65'].astype(str) + '<br>' +
                      'Confirmed Cases: ' + grouped['Confirmed'].astype(str) +
                      '<br>' + 'Deaths: ' + grouped['Deaths'].astype(str))
    return fig


fatalityRate_65 = fatalityRate_65()


#########################################
print(grouped)

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
    html.H5("Global confirmed COVID-19 cases and deaths",
            id="choropleth-title"),
    html.
    P("Note: Confirmed counts are lower than the total counts due to limited testing and challenges in the attribution of the cause of death.",
      id="note"),
    dbc.Row([
        dbc.Col(html.Div(
            dcc.Graph(id='choropleth',
                      figure=world_map,
                      config={'displayModeBar': False})),
                width='16'),
        dbc.Col(children=[
            dbc.Row(
                dbc.Col(dbc.Card(card_content1, color="dark", inverse=True),
                        width="12")),
            dbc.Row(
                dbc.Col(dbc.Card(card_content2, color="dark", inverse=True),
                        width="12"))
        ]),
    ]),
    html.
    H5("Confirmed COVID-19 cases and deaths - (Select country and metric below)",
       id="chart-title"),
    html.
    P("Note: Confirmed counts are lower than the total counts due to limited testing and challenges in the attribution of the cause of death.",
      id="note1"),
    dbc.Row([
        dbc.Col(
            dcc.RadioItems(id='metrics',
                           options=[{
                               'label': m,
                               'value': m
                           } for m in ['Confirmed', 'Deaths']],
                           value='Confirmed',
                           labelStyle={'display': 'inline-block'})),
        dbc.Col(
            dcc.RadioItems(id='yaxis_type',
                           options=[{
                               'label': i,
                               'value': i
                           } for i in ['linear', 'log']],
                           value='linear',
                           labelStyle={'display': 'inline-block'})),
        dbc.Col(
            dcc.Dropdown(id='country',
                         options=[{
                             'label': c,
                             'value': c
                         } for c in world_data.Country.unique()],
                         value='US',
                         multi=False))
    ]),
    dbc.Row([
        dbc.Col(html.Div(
            dcc.Graph(id='lineChart', config={'displayModeBar': False})),
                width='6'),
        dbc.Col(html.Div(
            dcc.Graph(id='barChart', config={'displayModeBar': False})),
                width='6'),
    ]),
    html.Div([
        html.
        H5("Current confirmed Case Fatality Rates (CFR) for countries with more than 1000 confirmed cases)",
           id="fatality-chart"),
        html.
        P("Note: During an outbreak of a pandemic the CFR is a poor measure of the mortality risk of the disease as there may be factors that account for increased death rates such as coinfection, access to healthcare, patient demographics (i.e., older patients might be more prevalent in countries such as Italy).",
          id="note2"),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='fatalityChart',
                          figure=fatalityChart,
                          config={'displayModeBar': False}))
        ]),
        html.
        H5("Case fatality rate (CFR) of COVID-19 vs proportion of population over 65 years old)",
           id="fatality65-chart"),
        html.
        P("Note: The size of the bubble corresponds to the total confirmed deaths up to that date.",
          id="note3"),
        dbc.Row([
            dbc.Col(
                dcc.Graph(id='fatalityRate_65',
                          figure=fatalityRate_65,
                          config={'displayModeBar': False}))
        ])
    ])
])


#######################
# CALL BACK FUNCTIONS #
#######################


@app.callback(Output('barChart', 'figure'), [
    Input('country', 'value'),
    Input('metrics', 'value'),
    Input('yaxis_type', 'value'),
])
def update_plot(country, metrics, yaxis_type):
    return newCases(country, metrics, yaxis_type, yaxisTitle="Daily Increase")


@app.callback(Output('lineChart', 'figure'), [
    Input('country', 'value'),
    Input('metrics', 'value'),
    Input('yaxis_type', 'value'),
])
def update_plot_total(country, metrics, yaxis_type):
    return lineChart(country, metrics, yaxis_type, yaxisTitle="Daily Increase")


if __name__ == '__main__':
    app.run_server(debug=False)

server = app.server