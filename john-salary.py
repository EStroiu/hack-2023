import requests
import pandas as pd

import plotly.express as px

from dash import Dash, dcc, html, Output, Input

# Provided data
data = requests.get('https://www.levels.fyi/js/salaryData.json').json()
job_data = pd.DataFrame(data)

# defucking data
job_data["yearsofexperience"] = pd.to_numeric(job_data["yearsofexperience"])
job_data["yearsatcompany"] = pd.to_numeric(job_data["yearsatcompany"])

for i, row in job_data.iterrows():
    if int(row["totalyearlycompensation"]) < 10000:
        job_data.at[i, 'totalyearlycompensation'] = int(row["totalyearlycompensation"]) * 1000
    if str(row["gender"]) == "":
        job_data.at[i, 'gender'] = "Other"


# scores_df = job_data

def get_company_entries(search_company, df):
    result_df = df.loc[df['company'].str.lower() == search_company.lower()]
    return result_df


def get_position_entries(search_position, df):
    result_df = df.loc[df['title'].str.lower() == search_position.lower()]
    return result_df


def get_sorted():
    women_count = {}
    men_count = {}

    for row in job_data.iterrows():
        company = row[1]["company"]
        compensation = row[1]["totalyearlycompensation"]
        content = row[1]["title"]
        gender = row[1]["gender"]

        men_count.setdefault(company, [0])
        women_count.setdefault(company, [0])

        if gender == "Female":
            women_count[company][0] += 1
        elif gender == "Male":
            men_count[company][0] += 1

    reindex = {"company": list(women_count.keys()),
               "Women Count": [wc[0] for wc in women_count.values()],
               "Men Count": [mc[0] for mc in men_count.values()],
               "wm-ratio": []
               }

    # Calculate the ratio per country and add it to the reindex dictionary
    for i, company in enumerate(reindex['company']):
        women_count = reindex['Women Count'][i]
        men_count = reindex['Men Count'][i]
        if women_count == 0 and men_count == 0:
            ratio = 0
        elif women_count != 0 and men_count == 0:
            ratio = 1
        else:
            ratio = women_count / men_count  # Calculate the ratio, handle division by zero
        reindex['wm-ratio'].append(ratio)

    d = pd.DataFrame(reindex)
    d = d.drop(d[d['Women Count'] + d['Men Count'] < 20].index)
    return d
    # print(d)

    # maybe an idea for later
    # 0.6 (0.6 > 0.5) - meh (1 - 0.6 = 0.4)
    # 0.5 - ideal
    # 0.4 - meh

def get_top_best():
    d = get_sorted()
    top_ten = d.sort_values(by=['wm-ratio'], ascending=False).head(10)
    ret = []

    for row in top_ten.iterrows():
        cstr = str(row[1]["company"]) + " | " + str(row[1]["wm-ratio"])
        ret.append(cstr)

    return ret

def get_top_worst():
    d = get_sorted()
    top_ten = d.sort_values(by=['wm-ratio'], ascending=False).tail(10)
    ret = []

    for row in top_ten.iterrows():
        cstr = str(row[1]["company"]) + " | " + str(row[1]["wm-ratio"])
        ret.append(cstr)

    return ret

def get_frame(search_company=None, search_position=None, years="years_of_experience"):
    # get_top_best()
    final_df = job_data
    if search_company:
        final_df = get_company_entries(search_company, final_df)
    if search_position:
        final_df = get_position_entries(search_position, final_df)

    return final_df


app = Dash(__name__)

app.layout = html.Div([
    html.H4('Summary of the data'),

    html.P("Search by company:"),
    dcc.Textarea(id='search_company', value='', style={'width': '20%', 'height': '15px'}),

    html.P("Search by position:"),
    dcc.Textarea(id='search_position', value='', style={'width': '20%', 'height': '15px'}),

    dcc.RadioItems(id='years', options=[
        {"label": "Years at the Company", "value": "years_at_company"},
        {"label": "Years of experience", "value": "years_of_experience"}
    ], value="years_of_experience", inline=True),

    dcc.Graph(id="graph"),

    html.H4("Top 10 worst companies"),
    html.Div(
        className="trend",
        children=[
            html.Ul(id='my-list', children=[html.Li(i) for i in get_top_best()])
        ],
    ),
    html.H4("Top 10 best companies"),
    html.Div(
        className="trend",
        children=[
            html.Ul(id='my-list', children=[html.Li(i) for i in get_top_worst()])
        ],
    )

])


@app.callback(
    Output("graph", "figure"),
    Input("search_company", "value"),
    Input("search_position", "value"),
    Input("years", "value")
)
def display(search_company, search_position, years):
    df = get_frame(search_company=search_company if search_company != "" else None,
                   search_position=search_position if search_position != "" else None,
                   years=years)

    df["totalyearlycompensation"] = pd.to_numeric(df["totalyearlycompensation"])
    df = df.sort_values("totalyearlycompensation", ascending=True)

    df["yearsofexperience"] = pd.to_numeric(df["yearsofexperience"])
    df["yearsatcompany"] = pd.to_numeric(df["yearsatcompany"])

    df = df.sort_values("yearsofexperience", ascending=True)
    fig = px.scatter(df, y="totalyearlycompensation", x="yearsofexperience", color="gender")

    if years == "years_at_company":
        df = df.sort_values("yearsatcompany", ascending=True)
        fig = px.scatter(df, y="totalyearlycompensation", x="yearsatcompany", color="gender")

    for scat in fig.data:
        if scat.legendgroup == "Title: Senior Software Engineer":
            scat.visible = "legendonly"

    return fig


app.run_server(debug=True)
print("done")
