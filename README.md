<h1>Scraping Vidio App Reviews from Google Play Store</h1>

<p align="center">
    <a href="https://darren7753-vidio-google-play-store-reviews-dashboard-iajwpn.streamlit.app/" target="_blank">
        <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Open in Streamlit">
    </a>
</p>

<h2>Introduction</h2>

Welcome to my GitHub repository for **Scraping Vidio App Reviews from Google Play Store**. This project is all about gathering reviews of the Vidio app from Google Play Store using the `google-play-scraper` library, automating the scraping process with `GitHub Actions`, and presenting the scraped data on a `Streamlit` dashboard that is updated daily.

Manually scraping reviews from Google Play Store can be a tedious and time-consuming task. That's why this project was created to simplify the process and make it more accessible to anyone who needs to collect reviews. In this repository, I will be sharing the steps that I took to create this project as a reference for others who may need to do something similar in the future.

<h2>Walkthrough</h2>
<h3>Create a Database in MongoDB Atlas</h3>

In order to store all the reviews I would scrape, I needed a database. While there are many cloud database services available, I decided to use MongoDB Atlas for my project, as it offers a free version that can store up to 5 GB of data. You can find more details [here](https://www.mongodb.com/pricing). Once I created my database in MongoDB Atlas, I allowed access from anywhere under the Network Access section, so that my database could be accessed through `GitHub Actions` later on.

<h3>Install Libraries</h3>

Before starting, I installed and imported the required libraries.

```python
import os
import numpy as np
import pandas as pd
from pymongo import MongoClient
from google_play_scraper import Sort, reviews, reviews_all, app
import datetime
from dateutil.relativedelta import relativedelta
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
```

<h3>Scrape Reviews from Google Play Store</h3>

For this part, I created two Python scripts as follows:

- `scraping.ipynb` for scraping all available reviews until the time I was working on this project.
- `scraping_daily.py` for scraping 5,000 reviews daily.

To begin with, I established a connection to my database using the following code:

```python
client = MongoClient(
    "mongodb+srv://USERNAME:PASSWORD@project1.lpu4kvx.mongodb.net/?retryWrites=true&w=majority",
    serverSelectionTimeoutMS=300000
)
db = client["vidio"]
collection = db["google_play_store_reviews"]
```

However, since the code contained sensitive information such as my username and password, I needed to hide them using `GitHub Secrets`. I created a secret variable called `MONGODB_URL` and passed the sensitive information to it, then I updated my code as follows:


```python
client = MongoClient(
    os.environ["MONGODB_URL"],
    serverSelectionTimeoutMS=300000
)
db = client["vidio"]
collection = db["google_play_store_reviews"]
```

Next, I used two functions to scrape the reviews from the Google Play Store. The function `reviews_all()` is used to scrape all reviews, while the function `reviews()` is used to scrape 5,000 reviews daily. Since both functions have similar codes, I will show only one of them:

```python
result = reviews(
    "com.vidio.android",
    lang="id",
    country="id",
    sort=Sort.NEWEST,
    count=5000 # note that reviews_all() doesn't have the count argument
)
```

Finally, I stored the scraped reviews in my database in batches of 1,000 reviews to prevent timeout errors using the following code:

```python
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
```

<h3>Automate using GitHub Actions</h3>

To update my database daily at 9 am UTC+7, I used `GitHub Actions`. I created an `actions.yml` file under the `.github/workflows` directory to set up the automated task. However, it's important to note that `GitHub Actions` may not execute at exactly the specified time due to factors such as high traffic or other reasons.

<h3>Create a Dashboard using Streamlit</h3>

I created a [dashboard](https://darren7753-vidio-google-play-store-reviews-dashboard-iajwpn.streamlit.app/) to visualize my findings using the `Streamlit` library and hosted it on `Streamlit Cloud`. I used the `Plotly` library to create interactive graphics for the dashboard. To enhance the dashboard's performance, I implemented a caching mechanism that stores the results of slow function calls, such that they only need to be executed once. For caching, I used the `st.cache_resource` function to cache global resources such as database connections and the `st.cache_data` function to cache computations that return data. The following code shows an example of this:

```python
@st.cache_resource
def init_connection():
    return MongoClient(
        os.environ["MONGODB_URL"],
        serverSelectionTimeoutMS=300000
    )
client = init_connection()

@st.cache_data(ttl=600)
def load_data():
    db = client["vidio"]
    collection = db["google_play_store_reviews"]
    return pd.DataFrame(list(collection.find()))
df = load_data()
```

<h2>Conclusion</h2>
Overall, this project demonstrates the power of automation and how it can simplify tedious and time-consuming tasks. I hope that this repository serves as a helpful reference for others who may need to perform similar tasks in the future. Thank you for reading!