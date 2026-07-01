from flask import Flask, render_template
import requests
from bs4 import BeautifulSoup

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/projects')
def projects():
    return render_template('projects.html')

@app.route('/experience')
def experience():
    return render_template('experience.html') 

@app.route('/scraping')
def scraping():
    return render_template('scraping.html')

@app.route('/scraping/static')
def static_scraping():
    return render_template('static_scraping.html')

# Add this new route inside your app.py file

@app.route('/scraping/static/books')
def books_to_scrape():
    # URL of the practice scraping site
    url = "https://books.toscrape.com/"
    
    # Live scraping execution
    scraped_books = []
    try:
        # 1. Fetch the raw HTML content of the website
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        
        if response.status_code == 200:
            # 2. Parse the raw HTML with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 3. Target the specific product article elements
            book_elements = soup.find_all('article', class_='product_pod')
            
            for index, book in enumerate(book_elements, start=1):
                # Extract title from the image tag alt attribute or link title attribute
                title = book.h3.a['title']
                
                # Extract price text string
                price = book.find('p', class_='price_color').text
                
                # Extract rating status from class names (e.g., class="star-rating Three")
                rating_classes = book.find('p', class_='star-rating')['class']
                rating = rating_classes[1] if len(rating_classes) > 1 else "Unknown"
                
                # Extract availability text wrapper status
                availability = book.find('p', class_='instock availability').text.strip()
                
                # Form structure to ship directly into your templates dashboard
                scraped_books.append({
                    "id": index,
                    "title": title,
                    "price": price,
                    "rating": rating,
                    "availability": availability
                })
    except Exception as e:
        print(f"Scraping error occurred: {e}")
        # Fallback empty state array if site is down or network disconnects
        scraped_books = []

    # Ship data live to the frontend page container layout
    return render_template('books_data.html', books=scraped_books)

if __name__ == '__main__':
    app.run(debug=True)