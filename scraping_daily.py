# Import libraries
import numpy as np
import pandas as pd

import os
import openai
import pickle

import re
import emoji
import string

import spacy
from spacy.lang.en.stop_words import STOP_WORDS

from google_play_scraper import Sort, reviews, reviews_all, app
from datetime import datetime, timedelta
from pymongo import MongoClient

# Loading the English model
nlp = spacy.load("en_core_web_lg")

# Create a connection to MongoDB
client = MongoClient(
    os.environ["MONGODB_URL"],
    serverSelectionTimeoutMS=300000
)
db = client["vidio"]
collection = db["google_play_store_reviews"]
collection2 = db["current_timestamp"]

# Load the data from MongoDB
df = pd.DataFrame(list(collection.find()))
df = df.drop("_id", axis=1)
df = df.sort_values("at", ascending=False)

# Collect 5000 new reviews
result = reviews(
    "com.vidio.android",
    lang="id",
    country="id",
    sort=Sort.NEWEST,
    count=5000
)
new_reviews = pd.DataFrame(result[0])
new_reviews = new_reviews.fillna("empty")

# Filter the scraped reviews to exclude any that were previously collected
common = new_reviews.merge(df, on=["reviewId", "userName"])
new_reviews_sliced = new_reviews[(~new_reviews.reviewId.isin(common.reviewId)) & (~new_reviews.userName.isin(common.userName))]

# Create a function to normalize the reviews
def normalize_text(text):
    if not re.search(r'\w', text):
        return text
    for i in range(10):
        try:
            openai.api_key = os.environ["OPENAI_API_KEY"]
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "user", "content": f'Return 2 lines where the first line is the formal Indonesian word for {text}, starting with "ID: ", followed by the output. The second line should be the English translation, starting with "EN: ", followed by the output'}
                ]
            )
            return response["choices"][0]["message"]["content"]
        except Exception as e:
            continue
    return "empty"

# Apply the function to all the reviews
indonesian, english = [], []
for row in new_reviews_sliced["content"]:
    temp = normalize_text(row)

    temp_id = temp.split("\n")[0]
    temp_id = temp_id.replace('"', '')
    temp_id = temp_id.replace("\n", "")
    temp_id = temp_id.replace("ID: ", "")
    temp_id = temp_id.replace("=> ", "")
    temp_id = temp_id.replace("= ", "")
    indonesian.append(temp_id)

    temp_en = temp.split("\n")[-1]
    temp_en = temp_en.replace('"', '')
    temp_en = temp_en.replace("\n", "")
    temp_en = temp_en.replace("EN: ", "")
    temp_en = temp_en.replace("=> ", "")
    temp_en = temp_en.replace("= ", "")
    english.append(temp_en)

# Combine the normalized reviews to the original dataframe
new_reviews_sliced["content_formal_indonesian"] = indonesian
new_reviews_sliced["content_english"] = english
new_reviews_sliced = new_reviews_sliced[["reviewId", "userName", "userImage", "content", "content_formal_indonesian", "content_english", "score", "thumbsUpCount", "reviewCreatedVersion", "at", "replyContent", "repliedAt"]]
new_reviews_sliced = new_reviews_sliced.rename(columns={"content": "content_original"})
new_reviews_sliced = new_reviews_sliced.replace("", "empty")
new_reviews_sliced = new_reviews_sliced.fillna("empty")

def not_word(text):
    if not re.search(r"\w", text["content_original"]):
        text["content_formal_indonesian"] = text["content_original"]
        text["content_english"] = text["content_original"]
    return text
new_reviews_sliced = new_reviews_sliced.apply(not_word, axis=1)

# Add topics to all reviews
net_new_revews_sliced = new_reviews_sliced.copy()
net_new_revews_sliced = net_new_revews_sliced[net_new_revews_sliced["score"] <= 3]
net_new_revews_sliced = net_new_revews_sliced[net_new_revews_sliced["content_formal_indonesian"].notna()]
net_new_revews_sliced = net_new_revews_sliced[~net_new_revews_sliced["content_original"].str.match(r"[\u263a-\U0001f645]")]
net_new_revews_sliced = net_new_revews_sliced[["reviewId", "userName", "at", "content_original", "content_formal_indonesian", "content_english", "score"]]

for i in ["content_formal_indonesian", "content_english"]:
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("Baris 1", "")
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("Baris 2", "")
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("(", "", regex=True)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace(")", "", regex=True)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].apply(lambda x: emoji.replace_emoji(x, ""))

net_new_revews_sliced["content_english"] = net_new_revews_sliced["content_english"].str.replace("ads", "advertisements")

replace1 = list(net_new_revews_sliced[net_new_revews_sliced["content_english"].str.contains("Note")].index)
replace2 = list(net_new_revews_sliced[(net_new_revews_sliced["content_english"].str.contains("Indonesian", case=False)) & (net_new_revews_sliced["content_english"].str.contains("dictionary", case=False))].index)
replace3 = list(net_new_revews_sliced[(net_new_revews_sliced["content_english"].str.contains("Indonesian", case=False)) & (net_new_revews_sliced["content_english"].str.contains("language", case=False))].index)

replace = sorted(list(set(replace1 + replace2 + replace3)))

net_new_revews_sliced.loc[net_new_revews_sliced.index.isin(replace), ["content_formal_indonesian", "content_english"]] = net_new_revews_sliced.loc[net_new_revews_sliced.index.isin(replace), "content_original"]

def clean(text):
    text = text.lower()
    text = re.sub(r'\$\w*', '',str(text ))
    text = re.sub(r'\bRT\b', '', text)
    text = re.sub('b\'', '', text)
    text = re.sub(r'\.{2,}', ' ', text)
    text = re.sub('@[^\s]+','',text)
    text = re.sub(r'^RT[\s]+', '', text)
    text = re.sub('[0-9]+', '', text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r'(\s)#\w+', r'\1', text)
    text = text.strip(' "\'')
    text = re.sub(r'\s+', ' ', text)
    text = text.translate(str.maketrans("","",string.punctuation))
    text = text.replace("\n",' ')
    return text 
net_new_revews_sliced["content_cleaned"] = net_new_revews_sliced["content_english"].apply(clean)
net_new_revews_sliced = net_new_revews_sliced[net_new_revews_sliced["content_cleaned"].str.strip().replace("\s+", "") != ""]
net_new_revews_sliced = net_new_revews_sliced[net_new_revews_sliced["content_cleaned"] != ""]

def lemmatization(text):
    doc = nlp(text)
    lemmatized_text = " ".join([token.lemma_ for token in doc if not token.is_stop and token.lang_ == 'en'])
    return lemmatized_text
net_new_revews_sliced["content_cleaned"] = net_new_revews_sliced["content_cleaned"].apply(nlp)
net_new_revews_sliced["content_cleaned"] = net_new_revews_sliced["content_cleaned"].apply(lambda x: lemmatization(x.text))

for i in ["content_cleaned"]:
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("world", "", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("cup", "", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("final", "", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("wc", "", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("football", "", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("app ", " ", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("application", "", case=False)
    net_new_revews_sliced[i] = net_new_revews_sliced[i].str.replace("apk", "", case=False)

with open("count_vectorizer.pkl", "rb") as f:
    cv = pickle.load(f)

with open("lda_model.pkl", "rb") as f:
    LDA = pickle.load(f)

topic_results = LDA.transform(cv.transform(net_new_revews_sliced["content_cleaned"]))
net_new_revews_sliced["topic"] = topic_results.argmax(axis=1)

def topic_names(x):
    if x == 0:
        return "Bad Application"
    elif x == 1:
        return "Package"
    elif x == 2:
        return "Advertisement"
    else:
        return "Watching Experience"
net_new_revews_sliced["topic"] = net_new_revews_sliced["topic"].apply(topic_names)

df_merged = pd.merge(new_reviews_sliced, net_new_revews_sliced[["topic"]], left_index=True, right_index=True, how="outer")
df_merged = df_merged.fillna("empty")

# Update MongoDB with any new reviews that were not previously scraped
if len(df_merged) > 0:
    df_merged_dict = df_merged.to_dict("records")

    batch_size = 1_000
    num_records = len(df_merged_dict)
    num_batches = num_records // batch_size

    if num_records % batch_size != 0:
        num_batches += 1

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, num_records)
        batch = df_merged_dict[start_idx:end_idx]

        if batch:
            collection.insert_many(batch)

# Insert the current timestamp to MongoDB
current_datetime = datetime.now()
updated_datetime = current_datetime + timedelta(hours=7)
current_timestamp = updated_datetime.strftime("%A, %B %d %Y at %H:%M:%S")
collection2.replace_one({}, {"timestamp": current_timestamp}, upsert=True)