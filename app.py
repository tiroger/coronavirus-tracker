import dash
import folium
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import datetime
# from update_map import loadData

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
# latitude = 37.0902
# longitude = -95.7129


# locations = all_data['location']
# confirmed_cases = all_data.CumConfirmed
# deaths = all_data.CumDeaths
# countries = all_data['Country/Region']

# def map_locations():

#     locations = all_data['location']
#     confirmed_cases = all_data.CumConfirmed
#     deaths = all_data.CumDeaths
#     countries = all_data['Country/Region']
#     corona_map = folium.Map(location=[latitude, longitude], zoom_start=3)

#     for location, confirmed, death, country in zip(locations, confirmed_cases,
#                                                    deaths, countries):
#         folium.CircleMarker(
#             location,
#             color='#3186cc',
#             weight=0.1,
#             fill_color='#C23208',
#             fill=True,
#             fill_opacity=0.1,
#             tooltip=('<H6>' + country + '</H6>' + '<br>'
#                      'Confirmed: ' + '<strong style="color:#C23208;">' +
#                      str(confirmed) + '</strong>' + '<br>'
#                      'Deaths: ' + '<strong style="color:#C23208;">' +
#                      str(death) + '</strong>' + '<br>')).add_to(corona_map)
#     return corona_map


#location_map = map_locations()
#location_map.save(outfile='location_map.html')


colors = {'background': '#111111', 'text': '#BF4025'}

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)
#app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = html.Div(
    style={'font-family': "Helvetica, sans-serif"},
    children=[
        html.H1('Tracking Coronavirus (COVID-19) Cases'),
        html.P(f'Updated on {last_updated}'),
        html.Iframe(id='map', srcDoc = open('location_map.html', 'r').read(), width='95%', height='500'),
        #html.Button(id='map-submit-button', n_clicks=0, children='Refresh Map'),
        html.Div(className="row",
                 children=[
                     html.Div(className="two columns",
                              children=[
                                  html.H5(
                                      total_confirmed,
                                      style={
                                          'color': colors['text'],
                                          'font-size': '50px',
                                          'text-align': 'left',
                                          'font-weight': '400'
                                      },
                                  ),
                                  html.P("GLOBAL CONFIRMED CASES")
                              ]),
                     html.Div(className="two columns",
                              children=[
                                  html.H5(
                                      total_deaths,
                                      style={
                                          'color': colors['text'],
                                          'font-size': '50px',
                                          'text-align': 'left',
                                          'font-weight': '400'
                                      },
                                  ),
                                  html.P("GLOBAL DEATHS")
                              ]),
                     html.Div(className="two columns",
                              children=[
                                  html.H5('Country'),
                                  dcc.Dropdown(id='country',
                                               options=[{
                                                   'label': c,
                                                   'value': c
                                               } for c in countries],
                                               value='US')
                              ]),
                     html.Div(className="two columns",
                              children=[
                                  html.H5('State / Province'),
                                  dcc.Dropdown(id='state')
                              ]),
                     html.Div(className="three columns",
                              children=[
                                  html.H5('Selected Metrics'),
                                  dcc.Checklist(
                                      id='metrics',
                                      options=[{
                                          'label': m,
                                          'value': m
                                      } for m in ['Confirmed', 'Deaths']],
                                      value=['Confirmed', 'Deaths'])
                              ])
                 ]),
        dcc.Graph(id="plot_new_metrics", config={'displayModeBar': False}),
        dcc.Graph(id="plot_cum_metrics", config={'displayModeBar': False}),
    ])


@app.callback([Output('state', 'options'),
               Output('state', 'value')], [Input('country', 'value')])

def update_states(country):
    states = sorted(
        list(all_data.loc[all_data['Country/Region'] == country]
             ['Province/State'].unique()))
    states.insert(0, '<all>')
    state_options = [{'label': s, 'value': s} for s in states]
    state_value = state_options[0]['value']
    return state_options, state_value


def nonreactive_data(country, state):
    data = all_data.loc[all_data['Country/Region'] == country]
    if state == '<all>':
        data = data.drop('Province/State',
                         axis=1).groupby("date").sum().reset_index()
    else:
        data = data.loc[data['Province/State'] == state]
    new_cases = data.select_dtypes(include='int64').diff().fillna(0)
    new_cases.columns = [
        column.replace('Cum', 'New') for column in new_cases.columns
    ]
    data = data.join(new_cases)
    data['dateStr'] = data['date'].dt.strftime('%b %d, %Y')
    return data


def linechart(data, metrics, prefix="", yaxisTitle=""):
    figure = go.Figure(data=[
        go.Scatter(name=metric,
                   x=data.date,
                   y=data[prefix + metric],
                   marker_line_color='rgb(0,0,0)',
                   marker_line_width=0.5,
                   marker_color={
                       'Deaths': 'firebrick',
                       'Recovered': 'forestgreen',
                       'Confirmed': 'darkslateblue'
                   }[metric],
                   mode='lines+markers') for metric in metrics
    ])
    figure.update_layout(
              barmode='group', legend=dict(x=.05, y=0.95, font={'size':15}, bgcolor='rgba(0,0,0,0)'),
              plot_bgcolor='#FFFFFF', font=tick_font) \
          .update_xaxes(
              title="", tickangle=-90, type='category', showgrid=False, gridcolor='#DDDDDD',
              tickfont=tick_font, ticktext=data.dateStr, tickvals=data.date) \
          .update_yaxes(
              title=yaxisTitle, showgrid=True, gridcolor='#DDDDDD')
    return figure


def barchart(data, metrics, prefix="", yaxisTitle=""):
    figure = go.Figure(data=[
        go.Bar(
            name=metric,
            x=data.date,
            y=data[prefix + metric],
            marker_line_color='rgb(0,0,0)',
            marker_line_width=0.5,
            marker_color={
                'Deaths': 'firebrick',
                #'Recovered': 'forestgreen',
                'Confirmed': 'darkslateblue'
            }[metric]) for metric in metrics
    ])
    figure.update_layout(
              barmode='group', legend=dict(x=.05, y=0.95, font={'size':15}, bgcolor='rgba(0,0,0,0)'),
              plot_bgcolor='#FFFFFF', font=tick_font) \
          .update_xaxes(
              title="", tickangle=-90, type='category', showgrid=False, gridcolor='#DDDDDD',
              tickfont=tick_font, ticktext=data.dateStr, tickvals=data.date) \
          .update_yaxes(
              title=yaxisTitle, showgrid=True, gridcolor='#DDDDDD')
    return figure


@app.callback(Output('plot_new_metrics', 'figure'), [
    Input('country', 'value'),
    Input('state', 'value'),
    Input('metrics', 'value')
])
def update_plot_new_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return barchart(data,
                    metrics,
                    prefix="New",
                    yaxisTitle="New Cases per Day")


@app.callback(Output('plot_cum_metrics', 'figure'), [
    Input('country', 'value'),
    Input('state', 'value'),
    Input('metrics', 'value')
])
def update_plot_cum_metrics(country, state, metrics):
    data = nonreactive_data(country, state)
    return linechart(data,
                     metrics,
                     prefix="Cum",
                     yaxisTitle="Cumulative Cases")


# @app.callback(dash.dependencies.Output('map', 'srcDoc'),
#               [dash.dependencies.Input('map-submit-button', 'n_clicks')])
# def update_map(n_clicks):
#     if n_clicks is None:
#         return dash.no_update
#     else:
#         return open('location_map.html', 'r').read()


if __name__ == '__main__':
    app.run_server(debug=True)

server = app.server
