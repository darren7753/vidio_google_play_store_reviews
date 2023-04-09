# Import libraries
import numpy as np
import pandas as pd
import os
import openai
import re
from google_play_scraper import Sort, reviews, reviews_all, app
from datetime import datetime, timedelta
from pymongo import MongoClient

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

# Update MongoDB with any new reviews that were not previously scraped
if len(new_reviews_sliced) > 0:
    new_reviews_sliced_dict = new_reviews_sliced.to_dict("records")

    batch_size = 1_000
    num_records = len(new_reviews_sliced_dict)
    num_batches = num_records // batch_size

    if num_records % batch_size != 0:
        num_batches += 1

    for i in range(num_batches):
        start_idx = i * batch_size
        end_idx = min(start_idx + batch_size, num_records)
        batch = new_reviews_sliced_dict[start_idx:end_idx]

        if batch:
            collection.insert_many(batch)

# Insert the current timestamp to MongoDB
current_datetime = datetime.now()
updated_datetime = current_datetime + timedelta(hours=7)
current_timestamp = updated_datetime.strftime("%A, %B %d %Y at %H:%M:%S")
collection2.replace_one({}, {"timestamp": current_timestamp}, upsert=True)