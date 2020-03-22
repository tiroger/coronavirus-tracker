import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objects as go
from dash.dependencies import Input, Output
import pandas as pd

base_url = "https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/"

tick_font = {
    'size': 12,
    'color': "rgb(30,30,30)",
    'family': "Helvetica, sans-serif"
}


def loadData(fileName, columnName):
    data = pd.read_csv(base_url + fileName) \
             .drop(['Lat', 'Long'], axis=1) \
             .melt(id_vars=['Province/State', 'Country/Region'], var_name='date', value_name=columnName) \
             .fillna('<all>')
    data['date'] = data['date'].astype('datetime64[ns]')
    return data


all_data = loadData("time_series_19-covid-Confirmed.csv", "CumConfirmed") \
    .merge(loadData("time_series_19-covid-Deaths.csv", "CumDeaths")) \
    .merge(loadData("time_series_19-covid-Recovered.csv", "CumRecovered"))

countries = sorted(all_data['Country/Region'].unique())

app = dash.Dash(__name__)

app.layout = html.Div(
    style={'font-family': "Helvetica, sans-serif"},
    children=[
        html.H1('Tracking Coronavirus (COVID-19) Cases'),
        html.Div(
            className="row",
            children=[
                html.Div(className="four columns",
                         children=[
                             html.H5('Country'),
                             dcc.Dropdown(id='country',
                                          options=[{
                                              'label': c,
                                              'value': c
                                          } for c in countries],
                                          value='US')
                         ]),
                html.Div(className="four columns",
                         children=[
                             html.H5('State / Province'),
                             dcc.Dropdown(id='state')
                         ]),
                html.Div(
                    className="four columns",
                    children=[
                        html.H5('Selected Metrics'),
                        dcc.Checklist(
                            id='metrics',
                            options=[{
                                'label': m,
                                'value': m
                            } for m in ['Confirmed', 'Deaths', 'Recovered']],
                            value=['Confirmed', 'Deaths'])
                    ])
            ]),
        dcc.Graph(id="plot_new_metrics", config={'displayModeBar': False}),
        dcc.Graph(id="plot_cum_metrics", config={'displayModeBar': False})
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
        go.Bar(name=metric,
                   x=data.date,
                   y=data[prefix + metric],
                   marker_line_color='rgb(0,0,0)',
                   marker_line_width=0.5,
                   marker_color={
                       'Deaths': 'firebrick',
                       'Recovered': 'forestgreen',
                       'Confirmed': 'darkslateblue'
                   }[metric]
                   ) for metric in metrics
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


if __name__ == '__main__':
    app.run_server(debug=True)

server = app.server