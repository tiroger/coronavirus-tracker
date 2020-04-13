# Tracking coronavirus cases with Plotly, Folium and Dash

![coronavirus](Coronavirus-1.jpg)

This dashboard was build with Plotly and Dash using data from the Johns Hopkins Center for Systems Science and Engineering (JHU/CSSE) [github repository](https://github.com/CSSEGISandData/COVID-19/tree/master/csse_covid_19_data). The data is updated nightly and changes are reflected here upon app launch.

**App Features**

- Downloads and parses official data on the coronavirus pandemic (updated on a daily basis)
- World map showing cummulalative confirmed cases and deaths
- Drop-down menus allowing the user to select an individual country
- Option for metric and y-axis scale
- Line chart for cumulative cases of a selected country over time
- Bar chart for new daily cases
- Bar chart for current case fatality rates (CFR) for countries with over 1000 confirmede cases
- Bubble chart correlating (CFR) with the proportion of the population over 65 years old

Deployed on Heroku: https://coronavirus-cases.herokuapp.com/
  