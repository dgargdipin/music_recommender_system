import re
import numpy as np
import pandas as pd
import os
import pickle5 as pickle
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.manifold import TSNE
from sklearn.metrics import euclidean_distances
from scipy.spatial.distance import cdist

KMEANSFILENAME = "kmeansmodel.pkl"
DATA_LOCATION = "data.csv"

spotify_data = pd.read_csv(DATA_LOCATION)

number_cols = [
    "acousticness",
    "danceability",
    "duration_ms",
    "energy",
    "explicit",
    "instrumentalness",
    "key",
    "liveness",
    "loudness",
    "mode",
    "popularity",
    "speechiness",
    "tempo",
    "valence",
    "year",
]

metadata_cols = ['name', 'year', 'artists']
song_cluster_pipeline=None
def train_model():
    global song_cluster_pipeline
    if os.path.exists(KMEANSFILENAME) and song_cluster_pipeline is None:
        print("AAA")
        with open(KMEANSFILENAME, "rb") as f:
            song_cluster_pipeline = pickle.load(f)
        return
    song_cluster_pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=20, verbose=2)),
        ],
        verbose=True,
    )
    X = spotify_data.select_dtypes(np.number)

    number_cols = list(X.columns)
    print(X.columns)
    song_cluster_pipeline.fit(X)
    with open(KMEANSFILENAME, "wb") as f:
        pickle.dump(song_cluster_pipeline, f)

## list of dict-> pandas
# song_list-> list of dicts returned from  get_top_songs
def getPandasFrame(song_list):
    pandas_frame = pd.DataFrame(song_list, columns=number_cols)
    # print(pandas_frame.iloc[0])
    return pandas_frame

# returns pandas mean series
# def getMean(data_frame):
#     # print(type(data_frame))
#     # print(type(data_frame.mean(axis='index')))
#     return data_frame.mean(axis="index")

def add_cluster_labels(data_frame):
    global song_cluster_pipeline
    song_cluster_labels = song_cluster_pipeline.predict(data_frame)
    data_frame["cluster_label"] = song_cluster_labels

def song_group_mean(data_frame):
    return data_frame.groupby('cluster_label').mean()

def recommend_songs(song_list):
    train_model()
    numeric_frame=getPandasFrame(song_list)
    add_cluster_labels(numeric_frame)
    grouped_mean_df=song_group_mean(numeric_frame)
    song_name_list = [a["song_name"] for a in song_list]
    rec_song_groups=[]
    for index, row in grouped_mean_df.iterrows():
        rec_song_groups+=predict_for_mean(row, song_name_list)
    return rec_song_groups
    

def predict_for_mean(song_center,song_name_list):
    metadata_cols = ['name', 'year', 'artists']
    global song_cluster_pipeline
    scaler = song_cluster_pipeline.steps[0][1]
    scaled_data = scaler.transform(spotify_data[number_cols])
    scaled_song_center = scaler.transform(np.array(song_center).reshape(1, -1))
    distances = cdist(scaled_song_center, scaled_data, 'cosine')
    index = list(np.argsort(distances)[:, :5][0])
    rec_songs = spotify_data.iloc[index]
    rec_songs = rec_songs[~rec_songs['name'].isin(song_name_list)]
    return rec_songs[metadata_cols].to_dict(orient='records')
