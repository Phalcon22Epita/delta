import pandas as pd
import plotly.express as px
import ast
import dash
from dash import dcc
from dash import html
import json


class Song():
    
    def __init__(self, application = None):
        self.s_artists = pd.read_csv("efm_sujet/data/artists.zip", converters={2:ast.literal_eval})
        self.s_artists = self.s_artists.rename(columns={"name":"artists"})

        self.songs = pd.read_csv("efm_sujet/data/tracks.zip")
        self.songs.drop(self.songs[self.songs["popularity"] == 0].index, inplace = True)
        self.songs.drop(columns=["time_signature", "tempo", "valence", "liveness", "instrumentalness", "acousticness", "speechiness", "mode", "loudness", "key", "energy", "duration_ms"], inplace=True)
        self.songs.drop_duplicates(subset=["name", 'artists'], inplace=True)

        self.df = pd.read_csv("efm_sujet/data/album_ratings.zip")
        self.df.rename(columns={"Artist": "artists"}, inplace=True)

        self.songs['id_artists'] = self.songs['id_artists'].astype(str)
        self.songs['id_artists'] = self.songs['id_artists'].apply(lambda x: (x[2:])[:-2])
        self.songs['artists'] = self.songs['artists'].astype(str)
        self.songs['artists'] = self.songs['artists'].apply(lambda x: (x[2:])[:-2])
        
        #Join entre les datasets
        self.artists = self.df.merge(self.s_artists, how="inner", on = "artists")
        self.artists = self.artists.dropna()
        self.artists = self.artists.rename(columns={"id": "id_artists"})

        self.artists = self.artists.sort_values(by= "followers", ascending=False)

        self.Tracks = self.songs.merge(self.artists, how="inner", on = ["artists", "id_artists"])
        self.Tracks.drop_duplicates(subset="name", inplace=True, ignore_index=True)
        
        self.Tracks.sort_values(by="danceability", inplace=True, ascending=False)
        
        #???
        self.songs_pays = pd.read_csv("efm_sujet/data/songsbycountry.zip")
        
        self.songs_pays.drop(self.songs_pays[self.songs_pays["Country"] == "Global"].index, inplace = True)
        self.songs_pays.drop(columns= ["Continent", "Explicit", "Duration"], inplace=True)
        self.songs_pays.rename(columns={"Title":"name", "Artists":"artists"}, inplace=True)

        self.head_country = self.songs_pays[self.songs_pays["Rank"] == 1].reset_index()
        self.head_country["index"] = self.head_country.index
        
        self.songpopularity = self.songs_pays.merge(self.Tracks, how="inner", on=["artists", "name"])
        
        self.mymap = json.load(open('efm_sujet/custom.geo_1.json'))
        
        
        self.main_layout = html.Div(children=[
            
            dcc.Markdown('''
            ## Facteurs de popularité des musiques
            '''),
            
            html.H3(children='POPULARITE DES GENRES AU FIL DES ANNEES'),

            html.Div([
                dcc.Graph(id = "barplot"),
                dcc.Dropdown(["AOTY Critic Score", "AOTY User Score", "Metacritic Critic Score", "Metacritic User Score"],
                             "AOTY Critic Score", id = "barplot_y"),
                dcc.Dropdown(sorted(self.df["Release Year"].unique().tolist(), reverse=True), 2018, id = "barplot_year"),
                dcc.Dropdown([5, 10, 20, 50 ], 10, id = "barplot_n")]),
            
            dcc.Markdown('''
            Ajouter des commentaires ICI
            '''),
            html.H3(children='POPULARITE DES ARTISTES'),
            html.Div([
                dcc.Graph(id = "corrplot", figure = self.createcorrplot())
            ]),
            
            dcc.Markdown('''
            Ajouter des commentaires ici
            ''')
        ]), html.Div(children=[
                html.H3(children='POPULARITE PAR PAYS'),

                html.Div([
                    dcc.Graph(id = "map", figure = self.createMap(), style={"padding" : "100px" }),
                    dcc.Graph(id = "pieChart")
                ]),
            
                dcc.Markdown('''
                    Ce graphique est interractif...
                '''),
                dcc.Markdown('''
                   #### À propos

                   * Données : 
                       - [Spotify Dataset 1921-2020, 600k+ Tracks](https://www.kaggle.com/datasets/yamaerenay/spotify-dataset-19212020-600k-tracks)
                       - [Contemporary album ratings and reviews](https://www.kaggle.com/datasets/kauvinlucas/30000-albums-aggregated-review-ratings)
                       - [Top 50 Spotify songs BY EACH COUNTRY](https://www.kaggle.com/datasets/leonardopena/top-50-spotify-songs-by-each-country)
                   * (c) 2022 Alexandre Castello & Jacky Wu
               ''')

            ])

        

        if application:
            self.app = application            
        else:
            self.app = dash.Dash(__name__)
            self.app.layout = self.main_layout
        self.app.callback(
            dash.dependencies.Output("barplot", "figure"),
            [dash.dependencies.Input("barplot_y", "value"),
            dash.dependencies.Input("barplot_year", "value"),
            dash.dependencies.Input("barplot_n", "value") ])(self.createbarplot)
        
        self.app.callback(
            dash.dependencies.Output("pieChart", "figure"),
            [dash.dependencies.Input("map", "clickData")])(self.getCountry)


        
    def createbarplot(self, y , year, n):
        x= "Genre"

        Review_2015 =  self.df[self.df["Release Year"] == year].groupby(x).mean().sort_values(by = [y, x], ascending=False).head(n)
        
        return px.bar(Review_2015 , y = y, title = f"Best {x} by {y} in {year}", log_y=True, height=800, width=1100)
        
    def createcorrplot(self):
        return px.scatter(self.artists.head(5000),x= 'popularity', y='followers', color="Genre", hover_name = "artists")
    
    def createMap(self):
        fig = px.choropleth_mapbox(self.head_country,
                            geojson=self.mymap, locations='Country',
                            featureidkey = 'properties.name',
                            color = "index",
                            color_continuous_scale="HSV",
                            hover_name="name",
                            hover_data=["artists", "Album"],
                            mapbox_style="carto-positron",
                            zoom=1, center = {"lat": 0, "lon": 0},
                            opacity=0.5,
                            labels={'Genre le plus écouté sur Spotify selon des pays en 2020'})
        fig.update_layout(margin={"r":0,"t":0,"l":0,"b":0})
        fig.update_coloraxes(showscale=False)
        return fig
    
    def createPie(self, country):
        country =  self.songpopularity[self.songpopularity["Country"] == country]
        
        #piechart
        l = []
        for c in list(country.genres):
            l.extend(c)

        piedata = pd.DataFrame(data = l, columns=["occ"])
        piedata = pd.DataFrame(piedata.groupby("occ")['occ'].count())
        
        fig =  px.pie(piedata, values = "occ",names = piedata.index, hover_name= piedata.index, color_discrete_sequence = px.colors.sequential.Plasma)
        fig.update_traces(textinfo='percent+label')
        return fig
        
    def getCountry(self, clickData):
        if (clickData == None):
            return self.createPie("France")
        print(clickData)
        return self.createPie(clickData["points"][0]["location"])
            
    def run_server(self, debug=False, port=8050):
        self.app.run_server(debug=debug, port=port, use_reloader=False)
        
if __name__ == '__main__':
    song = Song()
    song.app.run_server(debug=True, port=8051, use_reloader=False)
    