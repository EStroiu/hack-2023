import requests
import pandas as pd

import plotly.express as px

from dash import Dash, dcc, html, Output, Input

# Provided data
data = requests.get('https://www.levels.fyi/js/salaryData.json').json()
job_data = pd.DataFrame(data)


def get_company_entries(search_company, df):
    result_df = df.loc[df['company'].str.lower() == search_company.lower()]
    return result_df


def get_position_entries(search_position, df):
    result_df = df.loc[df['title'].str.lower() == search_position.lower()]
    return result_df


def get_frame(search_company=None, search_position=None, years="years_of_experience"):
    final_df = job_data
    if search_company:
        final_df = get_company_entries(search_company, final_df)
    if search_position:
        final_df = get_position_entries(search_position, final_df)

    for i, row in final_df.iterrows():
        if int(row["totalyearlycompensation"]) < 10000:
            final_df.at[i,'totalyearlycompensation'] = int(row["totalyearlycompensation"]) * 1000
        if str(row["gender"]) == "":
            final_df.at[i, 'gender'] = "Other"
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
