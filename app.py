import streamlit as st
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import csv
import re
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import matplotlib.pyplot as plt
from wordcloud import WordCloud, STOPWORDS
import pandas as pd
from collections import Counter
from webdriver_manager.chrome import ChromeDriverManager

st.set_page_config(layout="wide")
# Initialize list to hold reviews and set the review limit
reviews = []
review_limit = 100

# Function to scrape reviews from the current page
def scrape_reviews(driver):
    page_source = driver.page_source
    soup = BeautifulSoup(page_source, "html.parser")
    review_elements = soup.select("div[id^='customer_review-'] span.a-size-base.review-text.review-text-content span")
    
    with open("Amazon_reviews.csv", "a", newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for review_element in review_elements:
            if len(reviews) >= review_limit:
                return True  # Stop if limit reached
            review_text = review_element.get_text(strip=True)
            writer.writerow([review_text])  # Write each review as a new row
            reviews.append(review_text)
            print(review_text + '\n')
    
    return False  # Continue if limit not reached

# Function to click the "Next" button
def click_next_page(driver):
    try:
        next_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "li.a-last a"))
        )
        next_button.click()
        time.sleep(3)  # Wait for the next page to load
        return True
    except Exception as e:
        print(f"Error clicking next page: {e}")
        return False

# Function to initialize WebDriver
# def init_driver():
#     driver_path = r"C:\Users\aksha\Selenium\chromedriver-win64\chromedriver.exe"
#     service = Service(executable_path=driver_path)
#     options = webdriver.ChromeOptions()
#     driver = webdriver.Chrome(service=service, options=options)
#     return driver


def init_driver():
    options = webdriver.ChromeOptions()
    service = webdriver.chrome.service.Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver



# Function to get product reviews
def get_product_reviews(product_name, review_limit=100):
    driver = init_driver()
    link = "https://www.amazon.in/"
    driver.get(link)
    search_box = driver.find_element(By.ID, 'twotabsearchtextbox')
    search_box.send_keys(product_name)
    search_box.submit()
    try:
        first_product = driver.find_element(By.XPATH, "(//div[@data-component-type='s-search-result']//h2/a)[1]")
        first_product.click()
    except:
        print("First product not clicked")
        driver.quit()
        return []

    try:
        window_handles = driver.window_handles
        if len(window_handles) > 1:
            driver.switch_to.window(window_handles[1])

            product_title = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "productTitle"))
        )
            print("Product Title on new page:", product_title.text)

            product_price = driver.find_element(By.CSS_SELECTOR, "span.a-price.aok-align-center.reinventPricePriceToPayMargin.priceToPay span.a-price-whole")
            print("Product Price:", product_price.text)

            total_rating = driver.find_element(By.CSS_SELECTOR, "a[role='button'] span.a-size-base.a-color-base")
            print("Total Rating:", total_rating.text)
        
        # Extract number of reviews
            no_of_review = driver.find_element(By.ID, "acrCustomerReviewText")
            print("Number of Reviews:", no_of_review.text)
        
        # Click on 'See all reviews'
            all_review = driver.find_element(By.CSS_SELECTOR, "a#askATFLink span.a-size-base")
            all_review.click()
            print("All reviews page loaded")

            see_more_button = WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, ".a-link-emphasis.a-text-bold"))
            )
            see_more_button.click()
            print("Clicked 'See More' to load more reviews")

            WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "span[id='a-autoid-3-announce'] span[class='a-dropdown-prompt']"))
            ).click()
            print("Top Review Dropdown Clicked")

            WebDriverWait(driver, 15).until(
            EC.element_to_be_clickable((By.CSS_SELECTOR, "#sort-order-dropdown_1"))
            ).click()
            print("Most Recent Sort Option Clicked")
            # Click on "Most recent" sort option
            # most_recent = WebDriverWait(driver, 10).until(
            #     EC.element_to_be_clickable((By.XPATH, "//span[@data-action='reviews:filter-action:apply']"))
            # )
            # most_recent.click()
            time.sleep(5)  # Wait for the reviews to load

            # Main loop to handle pagination and scraping
            while len(reviews) < review_limit:
                if scrape_reviews(driver):
                    break  # Exit loop if review limit is reached
                if not click_next_page(driver):
                    break  # Exit loop if no more pages
        else:
            driver.quit()
            return []
    except Exception as e:
        driver.quit()
        return []
    driver.quit()
    return reviews

# Function to analyze sentiments
def analyze_sentiments(reviews):
    analyzer = SentimentIntensityAnalyzer()
    sentiments = [analyzer.polarity_scores(review)["compound"] for review in reviews]
    positive = [score for score in sentiments if score > 0.05]
    neutral = [score for score in sentiments if -0.05 <= score <= 0.05]
    negative = [score for score in sentiments if score < -0.05]
    return positive, neutral, negative

# Function to create word cloud
def create_wordcloud(reviews):
    text = ' '.join(reviews)
    eliminate = {"Amazon","iPhone","Apple","new","product","Phone"}
    stopwords = set(STOPWORDS).union(eliminate)
    wordcloud = WordCloud(width=800, height=400, background_color='white', stopwords=stopwords).generate(text)
    return wordcloud

# Function to extract and display most common sentences
def extract_sentences(reviews):
    analyzer = SentimentIntensityAnalyzer()
    sentences = {'positive': [], 'negative': []}
    for review in reviews:
        sentiment_score = analyzer.polarity_scores(review)['compound']
        review_sentences = re.split(r'(?<!\w\.\w.)(?<![A-Z][a-z]\.)(?<=\.|\?)\s', review)
        for sentence in review_sentences:
            if sentiment_score > 0.05:
                sentences['positive'].append(sentence.strip())
            elif sentiment_score < -0.05:
                sentences['negative'].append(sentence.strip())
    return sentences


def get_most_common(sentences, top_n=10):
    positive_counts = Counter(sentences['positive'])
    negative_counts = Counter(sentences['negative'])
    return positive_counts.most_common(top_n), negative_counts.most_common(top_n)

def display_most_common_sentences(common_sentences, sentiment_type):
    df = pd.DataFrame(common_sentences, columns=['Sentence', 'Frequency'])
    st.write(f"\nMost Common {sentiment_type} Sentences:")
    st.dataframe(df)
    
    # Plot bar chart
    plt.figure(figsize=(10, 6))
    plt.barh(df['Sentence'], df['Frequency'], color='blue' if sentiment_type == 'Positive' else 'red')
    plt.xlabel('Frequency')
    plt.title(f'Most Common {sentiment_type} Sentences')
    plt.gca().invert_yaxis()  # Invert y-axis to display the highest frequency at the top
    st.pyplot(plt)

# Streamlit app

st.markdown(
       """
    <style>
    .stApp {
        background-color: #dbfaf9; /* General background color of the app */
    }
    .stTextInput > div > div > input {
        background-color: #fff9ef; /* Very light blue */
        color: black;
        border: 2px solid #c8820a;
        padding: 8px; 
    }
    div.stButton > button {
        background-color: blue; /* Light blue */
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 20px;
        font-size: 16px;
    }
    div.stButton > button:hover {
        background-color: #87CEEB; /* Light sky blue */
        color: black;
    }
    </style>
    """,
    unsafe_allow_html=True
)



col1, col2 = st.columns([1,10])

# Display the logo in the first column
with col1:
    st.image('Logo.png', width=100)

# Display the title in the second column
with col2:
    st.title('Amazon Product Review Analyzer')

col1, col2 = st.columns([3, 1])  # Adjust the ratios as needed

with col1:
    product_name = st.text_input('Enter a product name:', 'Iphone')

if st.button('Analyze'):
    # st.header(f'Fetching reviews for "{product_name}"...')
    # st.subheader('Please wait for sometime....:)')
    reviews = get_product_reviews(product_name)

    if reviews:
        st.write(f'Total reviews fetched: {len(reviews)}')
        
        # Sentiment analysis
        positive, neutral, negative = analyze_sentiments(reviews)
        st.write(f"Positive reviews: {len(positive)}")
        st.write(f"Neutral reviews: {len(neutral)}")
        st.write(f"Negative reviews: {len(negative)}")

        col1, col2, col3 = st.columns(3)

        with col1:
        # Visualize sentiments
            st.write("Sentiments Analysis")
            labels = ['Positive', 'Neutral', 'Negative']
            sizes = [len(positive), len(neutral), len(negative)]
            colors = ['green', 'blue', 'red']
            explode = (0.1, 0, 0)
            fig, ax = plt.subplots()
            ax.pie(sizes, explode=explode, labels=labels, colors=colors, autopct='%1.1f%%', shadow=True, startangle=140)
            ax.axis('equal')
            st.pyplot(fig)
        
        with col2:
        #Word Cloud
            st.write('Generating word cloud...')
            wordcloud = create_wordcloud(reviews)
            fig, ax = plt.subplots()
            ax.imshow(wordcloud, interpolation='bilinear')
            ax.axis('off')
            st.pyplot(fig)

        with col3:
        # Most common sentences
            st.write('Extracting most common sentences...')
            sentences = extract_sentences(reviews)
            positive_common, negative_common = get_most_common(sentences)
        
            display_most_common_sentences(positive_common, 'Positive')
            display_most_common_sentences(negative_common, 'Negative')
    else:
        st.write('No reviews found or an error occurred.')
