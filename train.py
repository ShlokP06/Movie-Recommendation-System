import pandas as pd
import pickle
import numpy as np
from ast import literal_eval
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import linear_kernel, cosine_similarity
from nltk.stem.wordnet import WordNetLemmatizer
from surprise import Reader, Dataset, SVD, accuracy
from surprise.model_selection import train_test_split
import nltk

def filter_keywords(x):
    words = []
    for i in x:
        if i in s:
            words.append(lemmatizer.lemmatize(i))
    return words

def weighted_rating(x):
    v = x['vote_count']
    R = x['vote_average']
    return (v/(v+m) * R) + (m/(m+v) * C)

def get_director(x):
    for i in x:
        if i['job'] == 'Director':
            return i['name']
    return np.nan

def user_based(userId, algo, n=5):
    all_movie_ids = smd['id'].unique()
    predictions = [(movie_id, algo.predict(userId, movie_id).est) for movie_id in all_movie_ids]
    predictions.sort(key=lambda x: x[1], reverse=True)
    valid_movies = [id_map.loc[id_map['id'] == movie_id, 'movieId'].values[0] for movie_id, _ in predictions if movie_id in id_map['id'].values]
    valid_movies = [m for m in valid_movies if m in indices_map.index]
    top_movies = indices_map.loc[valid_movies[:n], 'title'].tolist()
    return top_movies

def convert_int(x):
    try:
        return int(x)
    except:
        return np.nan

def improved_recommendations(title):
    idx = indices[title]
    sim_scores = list(enumerate(cosine_sim[idx]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:26]
    movie_indices = [i[0] for i in sim_scores]
    movies = smd.iloc[movie_indices][['title', 'vote_count', 'vote_average', 'year']]
    vote_counts = movies[movies['vote_count'].notnull()]['vote_count'].astype('int')
    vote_averages = movies[movies['vote_average'].notnull()]['vote_average'].astype('int')
    C = vote_averages.mean()
    m = vote_counts.quantile(0.75)
    qualified = movies[(movies['vote_count'] >= m) & (movies['vote_count'].notnull()) & (movies['vote_average'].notnull())].copy()
    qualified['vote_count'] = qualified['vote_count'].astype('int')
    qualified['vote_average'] = qualified['vote_average'].astype('int')
    qualified['wr'] = qualified.apply(weighted_rating, axis=1)
    qualified = qualified.sort_values('wr', ascending=False).head(5)
    return qualified["title"]

def hybrid(userId, title):
    idx = indices[title]
    tmdbId = id_map.loc[title]['id']
    movie_id = id_map.loc[title]['movieId']
    sim_scores = list(enumerate(cosine_sim[int(idx)]))
    sim_scores = sorted(sim_scores, key=lambda x: x[1], reverse=True)
    sim_scores = sim_scores[1:26]
    movie_indices = [i[0] for i in sim_scores]
    movies = smd.iloc[movie_indices][['title', 'vote_count', 'vote_average', 'year', 'id']]
    movies = movies.merge(id_map[['id', 'movieId']], on='id', how='left') 
    movies = movies.dropna(subset=['movieId'])  
    movies['est'] = movies['movieId'].apply(lambda x: algo.predict(userId,x).est)
    movies = movies.sort_values('est', ascending=False)
    result=movies["title"]
    return result.head(5)

md = pd. read_csv('data/movies_metadata.csv',low_memory=False).copy()
md['genres'] = md['genres'].fillna('[]').apply(literal_eval).apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])
vote_counts = md[md['vote_count'].notnull()]['vote_count'].astype('int')
vote_averages = md[md['vote_average'].notnull()]['vote_average'].astype('int')
C = vote_averages.mean()
m = vote_counts.quantile(0.95)
md['year'] = pd.to_datetime(md['release_date'], errors='coerce').apply(lambda x: str(x).split('-')[0] if x != np.nan else np.nan)
qualified = md[(md['vote_count'] >= m) & (md['vote_count'].notnull()) & (md['vote_average'].notnull())][['title', 'year', 'vote_count', 'vote_average', 'popularity', 'genres']]
qualified=qualified.copy()
qualified['vote_count'] = qualified['vote_count'].astype('int')
qualified['vote_average'] = qualified['vote_average'].astype('int')
qualified['wr'] = qualified.apply(weighted_rating, axis=1)
qualified = qualified.sort_values('wr', ascending=False).head(250)
s = md.apply(lambda x: pd.Series(x['genres']),axis=1).stack().reset_index(level=1, drop=True)
s.name = 'genre'
gen_md = md.drop('genres', axis=1).join(s)
links_small = pd.read_csv('data/links_small.csv',low_memory=False).copy()
links_small = links_small[links_small['tmdbId'].notnull()]['tmdbId'].astype('int')
md = md.drop([19730, 29503, 35587])
md['id'] = md['id'].astype('int')
smd = md[md['id'].isin(links_small)]
smd=smd.copy()
smd['tagline'] = smd['tagline'].fillna('')
smd['description'] = smd['overview'] + smd['tagline']
smd['description'] = smd['description'].fillna('')
tf = TfidfVectorizer(analyzer='word',ngram_range=(1, 2),min_df=1, stop_words='english')
tfidf_matrix = tf.fit_transform(smd['description'])
cosine_sim = linear_kernel(tfidf_matrix, tfidf_matrix)
smd = smd.reset_index()
titles = smd['title']
indices = pd.Series(smd.index, index=smd['title'])
credits = pd.read_csv('data/credits.csv',low_memory=False).copy()
keywords = pd.read_csv('data/keywords.csv',low_memory=False).copy()
keywords['id'] = keywords['id'].astype('int')
credits['id'] = credits['id'].astype('int')
md['id'] = md['id'].astype('int')
md = md.merge(credits, on='id')
md = md.merge(keywords, on='id')
smd = md[md['id'].isin(links_small)].copy()
smd['cast'] = smd['cast'].apply(literal_eval)
smd['crew'] = smd['crew'].apply(literal_eval)
smd['keywords'] = smd['keywords'].apply(literal_eval)
smd['cast_size'] = smd['cast'].apply(lambda x: len(x))
smd['crew_size'] = smd['crew'].apply(lambda x: len(x))
smd['director'] = smd['crew'].apply(get_director)
smd['cast'] = smd['cast'].apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])
smd['cast'] = smd['cast'].apply(lambda x: x[:3] if len(x) >=3 else x)
smd['keywords'] = smd['keywords'].apply(lambda x: [i['name'] for i in x] if isinstance(x, list) else [])
smd['cast'] = smd['cast'].apply(lambda x: [str.lower(i.replace(" ", "")) for i in x])
smd['director'] = smd['director'].astype('str').apply(lambda x: str.lower(x.replace(" ", "")))
smd['director'] = smd['director'].apply(lambda x: [x,x,x])
s = smd.apply(lambda x: pd.Series(x['keywords']),axis=1).stack().reset_index(level=1, drop=True)
s.name = 'keyword'
s = s.value_counts()
s = s[s > 1]
lemmatizer=WordNetLemmatizer()
smd['keywords'] = smd['keywords'].apply(filter_keywords)
smd['keywords'] = smd['keywords'].apply(lambda x: [lemmatizer.lemmatize(i) for i in x])
smd['keywords'] = smd['keywords'].apply(lambda x: [str.lower(i.replace(" ", "")) for i in x])
smd['soup'] = smd['keywords'] + smd['cast'] + smd['director'] + smd['genres']
smd['soup'] = smd['soup'].apply(lambda x: ' '.join(x))
count = CountVectorizer(analyzer='word',ngram_range=(1, 2),min_df=1, stop_words='english')
count_matrix = count.fit_transform(smd['soup'])
cosine_sim = cosine_similarity(count_matrix, count_matrix)
smd = smd.reset_index()
indices = pd.Series(smd.index, index=smd['title'])
titles = smd['title']
reader = Reader()
ratings = pd.read_csv('data/ratings_small.csv',low_memory=False).copy()
data=Dataset.load_from_df(ratings[['userId','movieId','rating']],reader)
trainset, testset = train_test_split(data, test_size=.25)
algo=SVD()
algo.fit(trainset)
predictions=algo.test(testset)
print(accuracy.rmse(predictions))
print(accuracy.mae(predictions))
id_map = pd.read_csv('data/links_small.csv',low_memory=False)[['movieId', 'tmdbId']].copy()
id_map['tmdbId'] = id_map['tmdbId'].apply(convert_int)
id_map.columns = ['movieId', 'id']
id_map.dropna().astype(int)
id_map = id_map.merge(smd[['title', 'id']], on='id',how="left")
indices_map=id_map.set_index('movieId')[['title']]
id_map = id_map.reset_index().set_index('title')

np.save('cosine_sim.npy',cosine_sim)
md.to_csv("processed/processed_metadata.csv",index=False)
links_small.to_csv("processed/processed_links.csv",index=False)
credits.to_csv("processed/processed_credits.csv",index=False)
ratings.to_csv("processed/processed_ratings.csv",index=False)
id_map.to_csv("processed/map.csv",index=False)
smd.to_csv("processed/smd.csv",index=False)
print("Processing done successfully......")
with open("svd.pkl","wb") as f:
    pickle.dump(algo,f)
print("Model stored successfully.....")