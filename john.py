import pandas as pd
import requests

import json
from functools import cache
import geonamescache
import numpy as np
import pandas as pd
import plotly.express as px
from dash import Dash, dcc, html, Output, Input

data = requests.get('https://www.levels.fyi/js/salaryData.json').json()
job_data = pd.DataFrame(data)
hdi_index = pd.read_csv("HDI-world.csv")
secondary_ed = pd.read_csv("secondary-ed.csv")

gapminder = px.data.gapminder().query("year==2007")
gapminder.rename(columns={"country": "Country"}, inplace=True)
loaded = json.load(open("geojson-counties-fips.json", "r"))  # , dtype={"fips": str}

religiousness = pd.read_csv("csvData.csv")
religiousness.rename(columns={"country": "Country", "percentage": "percentage_religious"}, inplace=True)

education_percentage = pd.read_csv("../hack/secondary-ed.csv")

gcache = geonamescache.GeonamesCache()

states = gcache.get_us_states_by_names()
reindex = {"code": [c['code'] for c in states.values()], "country_name": [c['name'] for c in states.values()]}
state_frame = pd.DataFrame(reindex)

usa_poverty = pd.read_csv("america_poverty.csv")
usa_religion = pd.read_csv("america_religion.csv")

@cache
def code_from_state(state):
    return gcache.get_us_states_by_names()[state]["code"]


@cache
def search_city(city):
    res = gcache.search_cities(query=city)
    if res:
        for option in res:
            if not option["admin1code"].isdecimal() and option["countrycode"] == "US":
                return option["admin1code"]

        for option in res:
            if option["countrycode"] == "US":
                return option["admin1code"]

        for option in res:
            if not option["admin1code"].isdecimal():
                return option["admin1code"]

        print("Tried to find but failed to find city " + city)
        return None
    else:
        return None


def get_frame(search=None, usa_only=False):
    # srcdf = pd.read_csv("out3.csv")
    job_data[['city', 'state', 'country']] = job_data['location'].str.split(', ', n=2, expand=True)
    job_data['country'] = job_data['country'].fillna('United States')

    location_count = {}

    for row in job_data.iterrows():
        # location = str(row.).split(", ")
        city = row[1]["city"]
        country = row[1]["country"]
        # content = row[1]["Tweet"]
        content = row[1]["title"] # Product Manager or Software Engineer

        if search is not None:
            search_words = search.split()
            found = False
            for word in search_words:
                if word.lower() in content.lower():
                    found = True
                    break
            if not found:
                continue

        if usa_only:
            res: str = search_city(city)
            if res is None:
                continue
            elif res.isdecimal():
                res = states.get(city)
                if res is None:
                    continue
                res = res["code"]
        else:
            res = country
        location_count.setdefault(res, [0])
        location_count[res][0] += 1

    reindex = {"Country": list(location_count.keys()), "Count": [c[0] for c in location_count.values()]}
    d = pd.DataFrame(reindex)
    if usa_only:
        d.rename(columns={"Country": "code"}, inplace=True)
        ret = d.merge(state_frame, on="code")
        ret = ret.merge(usa_poverty, on="country_name")
        ret = ret.merge(usa_religion, on="country_name")
    else:
        ret = gapminder.merge(d, how='left', on='Country') \
            .merge(hdi_index, how='left', on='Country') \
            .merge(religiousness, how='left', on='Country')
    return ret


app = Dash(__name__)

app.layout = html.Div([
    html.H4('Sorting by criteria'),
    html.P("Search by title:"),
    dcc.Textarea(id='search', value='', style={'width': '10%', 'height': '15px'}),
    dcc.RadioItems(
        id='category',
        options=[
            {"label": "Employees count", "value": "Count"},
            {"label": "Women Ratio", "value": "women_ratio"},
        ],
        value="Count",
        inline=True
    ),
    dcc.RadioItems(
        id='usa_only',
        options=[
            {"label": "USA only", "value": True},
            {"label": "World", "value": False},
        ],
        value=False,
        inline=True
    ),
    dcc.Graph(id="graph"),
])


@app.callback(
    Output("graph", "figure"),
    Input("search", "value"),
    Input("category", "value"),
    Input("usa_only", "value")
)
def display(search, category, usa_only):
    df = get_frame(search=search if search != "" else None, usa_only=usa_only)

    if category == "Count" and not usa_only:
        # Apply log scale to count
        df["Count"] = np.log(df["Count"])

    fig = px.choropleth(df, locations='iso_alpha' if not usa_only else 'code',
                        color=category,
                        locationmode="USA-states" if usa_only else None,
                        color_continuous_scale="Plasma",
                        scope="usa" if usa_only else "world",
                        labels={'Count': 'employees count'}
                        )

    fig.update_layout(margin={"r": 0, "t": 0, "l": 0, "b": 0})
    return fig


app.run_server(debug=True)
print("done")
