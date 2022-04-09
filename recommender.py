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

# spotify_data = pd.read_csv("./data.csv")

# song_cluster_pipeline = Pipeline(
#     [
#         ("scaler", StandardScaler()),
#         ("kmeans", KMeans(n_clusters=20, verbose=2, n_jobs=4)),
#     ],
#     verbose=True,
# )
# X = spotify_data.select_dtypes(np.number)
# number_cols = list(X.columns)
# song_cluster_pipeline.fit(X)

# song_cluster_labels = song_cluster_pipeline.predict(X)
# spotify_data["cluster_label"] = song_cluster_labels
# from sklearn.decomposition import PCA

# pca_pipeline = Pipeline([("scaler", StandardScaler()), ("PCA", PCA(n_components=2))])
# song_embedding = pca_pipeline.fit_transform(X)

# projection = pd.DataFrame(columns=["x", "y"], data=song_embedding)
# projection["title"] = spotify_data["name"]
# projection["cluster"] = spotify_data["cluster_label"]
DATA_LOCATION='data.csv'


def train_model():
    spotify_data = pd.read_csv(DATA_LOCATION)

    song_cluster_pipeline = Pipeline(
        [
            ("scaler", StandardScaler()),
            ("kmeans", KMeans(n_clusters=20, verbose=2, n_jobs=4)),
        ],
        verbose=True,
    )
    X = spotify_data.select_dtypes(np.number)
    number_cols = list(X.columns)
    song_cluster_pipeline.fit(X)
    

    
    








number_cols = [
    "valence",
    "year",
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
]


import difflib
## list of dict-> pandas
# song_list-> list of dicts returned from  get_top_songs 
def getPandasFrame(song_list):
    pandas_frame=pd.DataFrame(song_list,columns=number_cols)
    # print(pandas_frame.iloc[0])
    with open('pandas_frame','w') as f:
        f.write(str(pandas_frame))
    getMean(pandas_frame)
    return pandas_frame

# returns pandas mean series
def getMean(data_frame):
    # print(type(data_frame))
    # print(type(data_frame.mean(axis='index')))
    return data_frame.mean(axis='index')




def add_cluster_labels(data_frame):
    if not os.path.exists('kmeansmodel.pkl'):
        train_model()
        return add_cluster_labels(data_frame)
    
