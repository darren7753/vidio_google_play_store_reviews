<a name="readme-top"></a>

<h1>Analyzing Vidio's Google Play Store Reviews</h1>

<p align="center">
    <a href="https://darren7753-vidio-google-play-store-reviews-dashboard-iajwpn.streamlit.app/" target="_blank">
        <img src="https://static.streamlit.io/badges/streamlit_badge_black_white.svg" alt="Open in Streamlit">
    </a>
</p>

<p align="center">
    <img src="https://raw.githubusercontent.com/darren7753/vidio_google_play_store_reviews/main/Thumbnail.png" alt="Thumbnail">
</p>

<h2>🔍Introduction</h2>

Welcome to my GitHub repository for **Analyzing Vidio's Google Play Store Reviews**. For those who may be unfamiliar, [Vidio](https://www.vidio.com/) is an Indonesian streaming platform and the largest OTT (over-the-top) service in the country. The purpose of this project is to delve into public sentiment regarding Vidio and gain valuable insights. One of the methods I employed was analyzing reviews from sources like the Google Play Store.

This project involves the following steps: scraping all the reviews from the Google Play Store using the **google-play-scraper** library, implementing topic modeling to categorize the reviews under specific topics with the assistance of the **GPT-3.5 Turbo** model, storing the acquired reviews in a database, and presenting them through a **Streamlit** dashboard. This entire process is automated using **GitHub Actions**. More details will be shared in the following section.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<h2>🚶‍♂️Walkthrough</h2>

<h3>📲Scraping the Reviews from the Google Play Store</h3>

The first task was to acquire the data for analysis, specifically the reviews of Vidio. Fortunately, there is a Python library called **google-play-scraper** that simplifies the process of scraping reviews from the Google Play Store for any app. Initially, I scraped all available reviews up until the time of initiating this project. Subsequently, I programmed the script to scrape 5000 reviews daily and filtered out the reviews collected on the previous day.

<h3>📊Implementing Topic Modeling on the Reviews</h3>

This stage constitutes the core of the project. Simply collecting the reviews alone does not provide substantial value. To gain deeper insights, I implemented topic modeling specifically on negative and neutral reviews. The objective was to better comprehend the common complaints users have about Vidio with the aim of utilizing the findings for future improvements.

Initially, I attempted to use LDA (Latent Dirichlet Allocation) for topic modeling. However, it proved to be highly inaccurate, resulting in numerous misclassifications. This issue appeared to be attributed to the language aspect. Many language-related techniques excel in English, but not in Indonesian, which is not as widely supported. Moreover, the presence of Indonesian slangs and various typographical variations further complicated the matter.

Consequently, I decided to employ one of OpenAI's models, given their extensive training on large datasets. I opted for the **GPT-3.5 Turbo** model, which requires a fee, but is relatively affordable. The cost amounts to approximately $0.002 per 1000 tokens or around 750 words. The results were significantly better than those obtained using LDA, though not entirely perfect. Further fine-tuning could be considered, but that will be a task for future endeavors.

<h3>💾Stroring the Reviews in a Database</h3>

Once the reviews were obtained, the next step involved storing them. One option was to utilize Google BigQuery, which is widely used. However, after careful consideration, I decided to use **MongoDB Atlas**. It offers a free plan that allows for storage of up to 5 GB, which proved to be more than sufficient in this case. It is worth noting that using MongoDB entails a slightly different querying approach compared to SQL, as MongoDB is a NoSQL database.

<h3>📈Creating a Streamlit Dashboard</h3>

To present the findings in an organized and visually appealing manner, I integrated the **MongoDB Atlas** database with a **Streamlit** dashboard. **Streamlit** proved to be an ideal choice, as it offered customization options and supported various Python libraries, including Plotly, which was utilized to generate interactive plots in this project.

<h3>⚙️Automating the Entire Process</h3>

With all the components in place, the remaining task was to automate the entire process on a daily basis. Manually repeating these steps every day was not feasible. Fortunately, there are several automation options available, with **GitHub Actions** being one of them. I configured **GitHub Actions** to execute the project workflow daily at 9 AM UTC+7.

<p align="right">(<a href="#readme-top">back to top</a>)</p>

<h2>🎯Conclusion</h2>

This project demonstrates the utilization of topic modeling to analyze app reviews. While numerous techniques exist, employing GPT proves to be a viable choice, particularly for languages other than English. It is my hope that this repository serves as a valuable reference for those undertaking similar tasks in the future. Thank you for reading!

<p align="right">(<a href="#readme-top">back to top</a>)</p>