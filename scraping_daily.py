# Import libraries
import numpy as np
import pandas as pd
import os
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
current_timestamp = datetime.now().strftime("%A, %B %d %Y at %H:%M:%S")
current_timestamp += timedelta(hours=7)
collection2.replace_one({}, {"timestamp": current_timestamp}, upsert=True)