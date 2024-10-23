import dash
from dash import dcc, html, Input, Output, callback
import plotly.express as px
import pandas as pd
import numpy as np

movies = pd.read_csv('data/imbd-movies.csv')
print(movies.shape)

fin_movies = movies[(movies['budget']!=0)&(movies['gross']!=0)]
fin_movies['rev_to_bud'] = fin_movies['gross']/fin_movies['budget']

# PLOTTING FUNCTIONS --------------------------------------------------------------------------------

def create_map():
    country_codes = pd.read_csv('data/iso3-country-codes.csv')

    country_codes_map = pd.Series(country_codes.ISO3_CODE.values, index=country_codes.LABEL_EN).to_dict()
    inv_country_codes_map =  {v: k for k, v in country_codes_map.items()}
    country_codes_map.update({'South Korea' : 'KOR', 
                            'Soviet Union' : 'RUS',
                            'Russia' : 'RUS',
                            'West Germany' :'DEU',
                            'Iran' : 'IRN',
                            'Hong Kong' : 'HKG',
                            'Taiwan' : 'TWN',})


    movies['country_iso3'] = movies['country'].map(country_codes_map)

    count_by_country = movies.groupby('country_iso3', as_index=False)['title'].count().rename({'title': 'count'}, axis=1)

    count_by_country['country'] = count_by_country['country_iso3'].map(inv_country_codes_map)

    fig = px.choropleth(locations=count_by_country["country_iso3"],
                        color=np.log10(count_by_country['count']), 
                        custom_data=[count_by_country['country'], count_by_country['count']],
                        template="plotly_white",
                        title='Number of movies by country of origin'
                        )
    fig.update_traces(
        hovertemplate="<br>".join([
            "%{customdata[0]}",
            "Count: %{customdata[1]}",
        ])
    )
    fig.update_geos(fitbounds="locations",projection_type="natural earth")
    fig.update_layout(coloraxis_showscale=False,
                      margin=dict(l=10, r=10, t=80, b=10),
                      title=dict(yref="paper",
                                 y=1,
                                 yanchor="bottom",
                                 font=dict(size=30),
                                 automargin=True)
    )

    
    return fig

#---------------------------------------------------------------------------------------------------

@callback(
    Output('graph-with-dropdown', 'figure'),
    Input('genre-dropdown', 'value'))
def create_scatterplot(selected_genre):

    df = fin_movies.copy(deep=True)

    if selected_genre != 'all_values':
        df = df[df.genre == selected_genre]

    fig = px.scatter(df, x='budget', y='rev_to_bud', color='genre',log_y=True,log_x=True,template="plotly_white",
                     opacity=0.5,
                     custom_data=['title', 'budget','rev_to_bud'],
                     labels={
                        "budget": "Budget ($)",
                        "rev_to_bud": "Gross revenue (factor of budget)",
                        'genre':'Genre'
                    },
                     title='Budget compared to gross world wide revenue'
                     )

    fig.update_traces(
        hovertemplate="<br>".join([
            "%{customdata[0]}",
            "Budget: %{customdata[1]}",
            "Gross: %{customdata[2]:.2f} times budget",
        ])
    )
    fig.update_traces(marker=dict(size=10,
    ),
                  selector=dict(mode='markers'))
    fig.update_layout(
                     margin=dict(l=10, r=10, t=90, b=10),
                      title=dict(yref="paper",
                                 y=1,
                                 yanchor="bottom",
                                 font=dict(size=30),
                                 automargin=True)
    )

    return fig

#---------------------------------------------------------------------------------------------------

def create_lineplot():
    budget_by_year = movies.groupby('year', as_index=False)['budget'].median() 

    fig = px.line(budget_by_year, x='year', y='budget', template="plotly_white",
                     labels={
                        "budget": "Median budget ($)",
                        "year": "Year",
                        },
                     title='Typical movie budget over time')
    fig.update_layout(
                     margin=dict(l=10, r=10, t=90, b=10),
                      title=dict(yref="paper",
                                 y=1,
                                 yanchor="bottom",
                                 font=dict(size=30),
                                 automargin=True)
                      )
    return fig

#---------------------------------------------------------------------------------------------------

@callback(
    Output('barplot', 'figure'),
    Input('genre-dropdown2', 'value'))
def create_barplot(selected_genre):

    df = movies.copy(deep=True)

    if selected_genre != 'all_values':
        df = df[df.genre == selected_genre]

    official_certs =['U', 'PG', '12A', '15', '18']
    update_certificates = {'A' : 'PG', 'X' : '18', 'AA' : '15', '12' : '12A'}
    df['age_restriction'] = df['age_restriction'].replace(update_certificates)
    df =  df[df['age_restriction'].isin(official_certs)]
    df['age_restriction'] = pd.Categorical(df['age_restriction'], categories=official_certs, ordered=True, )

    count_by_cert = df['age_restriction'].value_counts(sort=False).reset_index()

    fig = px.bar(count_by_cert, x='age_restriction', y='count', template="plotly_white",
                        labels={
                            "age_restriction": "Age restriction",
                            "count": "Number of movies",
                            },
                        title='Number of movies per certification type' )
    fig.update_traces(marker_color='purple')
    fig.update_layout(
                    margin=dict(l=10, r=10, t=90, b=10),
                    title=dict(yref="paper",
                                 y=1,
                                 yanchor="bottom",
                                 font=dict(size=30),
                                 automargin=True)
                      )
    return fig


app = dash.Dash(__name__)

app.layout = html.Div(children=[
    html.Div(

      html.H1('Movie dashboard'), style={'font-family':'sans-serif'} ),

    # top row
    html.Div(children =[

        # top left
        html.Div(
            dcc.Graph(figure=create_lineplot()),
            style={'width':'750px', 'display':'inline-block', 'margin':'20px', 'padding':'0px'}),

        #top right
        html.Div(
            dcc.Graph(figure=create_map()),
            style={'width':'750px', 'display':'inline-block', 'margin':'20px'}),
    ]),

    # bottom row
    html.Div(children =[

        # bottom left
        html.Div(
            html.Div(children=[
            html.Div(dcc.Graph(id='graph-with-dropdown', style={'width':'750px','margin':'0px'})),
            html.Div(dcc.Dropdown(
                id='genre-dropdown',
                value='all_values',
                options=[{'label':x, 'value':x} for x in fin_movies['genre'].unique()]+[{'label': 'All genres', 'value': 'all_values'}],
                ), style={'width':'200px', 'height':'40px', 'margin':'0px'}),
        ]), style={'width':'750px', 'display':'inline-block', 'margin':'20px'}

            ),

        #bottom right
        html.Div(
            html.Div(children=[

            html.Div(dcc.Graph(id='barplot', style={'width':'750px','margin':'0px'})),
            html.Div(dcc.Dropdown(
                id='genre-dropdown2',
                value='all_values',
                options=[{'label':x, 'value':x} for x in movies['genre'].unique()]+[{'label': 'All genres', 'value': 'all_values'}],
                ), style={'width':'200px', 'height':'40px', 'margin':'0px'}),
        ]), style={'width':'750px', 'display':'inline-block', 'margin':'20px'},
            ),
    ]),

    ],style={'text-align':'center', 'font-size':22, 'background-color':'white'})

if __name__ == '__main__':
    app.run_server(debug=True)