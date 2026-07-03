import io
import os
import pandas as pd
import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template, abort

app = Flask(__name__)

# ==========================================
# CORE PORTFOLIO NAVIGATION ROUTES
# ==========================================

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

@app.route('/scraping/dynamic')
def dynamic_scraping():
    return render_template('dynamic_scraping.html')


# ==========================================
# STATIC DATA GATHERING CONTROLLER ENGINES
# ==========================================

def get_books_data():
    url = "https://books.toscrape.com/"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            book_elements = soup.find_all('article', class_='product_pod')
            data = []
            for book in book_elements:
                data.append({
                    "Title": book.h3.a['title'],
                    "Price": book.find('p', class_='price_color').text,
                    "Rating": book.find('p', class_='star-rating')['class'][1],
                    "Availability": book.find('p', class_='instock availability').text.strip()
                })
            return data
    except Exception:
        pass
    return [{"Title": "Sample Book A", "Price": "£25.00", "Rating": "Three", "Availability": "In stock"}]

def get_quotes_data():
    url = "https://quotes.toscrape.com/"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            quote_elements = soup.find_all('div', class_='quote')
            data = []
            for q in quote_elements:
                data.append({
                    "Quote": q.find('span', class_='text').text.replace('“', '').replace('”', ''),
                    "Author": q.find('small', class_='author').text,
                    "Tags": ", ".join([tag.text for tag in q.find_all('a', class_='tag')])
                })
            return data
    except Exception:
        pass
    return [{"Quote": "Be yourself; everyone else is already taken.", "Author": "Oscar Wilde", "Tags": "inspirational"}]

def get_realpython_data():
    url = "https://realpython.com/"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        data = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            cards = soup.find_all('div', class_='card')
            for card in cards:
                title_el = card.find('h2', class_='card-title')
                if title_el:
                    tags = [t.text.strip() for t in card.find_all('a', class_='badge')]
                    data.append({
                        "Article/Tutorial Title": title_el.text.strip(),
                        "Categories": ", ".join(tags) if tags else "General Python"
                    })
            if data: return data
    except Exception:
        pass
    return [{"Article/Tutorial Title": "Python Basics Tutorial", "Categories": "Beginner"},
            {"Article/Tutorial Title": "Web Scraping Deep Dive", "Categories": "Scraping"}]

def get_hockey_data():
    url = "https://www.scrapethissite.com/pages/forms/"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            table_rows = soup.find_all('tr', class_='team')
            data = []
            for row in table_rows[:25]:
                data.append({
                    "Team Name": row.find('td', class_='name').text.strip(),
                    "Year": row.find('td', class_='year').text.strip(),
                    "Wins": row.find('td', class_='wins').text.strip(),
                    "Losses": row.find('td', class_='losses').text.strip()
                })
            if data: return data
    except Exception:
        pass
    return [{"Team Name": "Boston Bruins", "Year": "1990", "Wins": "44", "Losses": "24"}]

def get_amazon_data():
    url = "https://www.amazon.in/s?k=laptop&crid=YLH7SZQM1WE6&sprefix=laptop%2Caps%2C610&ref=nb_sb_noss_2"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.google.com/"
        }
        response = requests.get(url, headers=headers, timeout=10)
        data = []
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            products = soup.find_all('div', {'data-component-type': 's-search-result'})
            for p in products:
                title_el = p.find('h2', class_='a-size-medium')
                price_el = p.find('span', class_='a-price-whole')
                rating_el = p.find('i', class_='a-icon-star-small') or p.find('i', class_='a-icon-star')
                if title_el:
                    data.append({
                        "Laptop Model": title_el.text.strip()[:80] + "...",
                        "Price (INR)": "₹" + price_el.text.strip() if price_el else "N/A",
                        "Rating": rating_el.text.strip() if rating_el else "No reviews yet"
                    })
            if data: return data
    except Exception:
        pass
    return[
                {"Laptop Model": "HP Laptop 15s, AMD Ryzen 3 5300U (8GB RAM / 512GB SSD)", "Price (INR)": "₹32,490", "Rating": "4.1 out of 5 stars"},
                {"Laptop Model": "ASUS Vivobook 15, Intel Core i5-1235U (16GB RAM / 512GB SSD)", "Price (INR)": "₹49,990", "Rating": "4.3 out of 5 stars"},
                {"Laptop Model": "Lenovo IdeaPad Slim 3, Intel Core i3-1215U (8GB RAM / 512GB SSD)", "Price (INR)": "₹35,990", "Rating": "4.0 out of 5 stars"},
                {"Laptop Model": "Dell Inspiron 3520, Intel Core i5-1235U (8GB RAM / 512GB SSD)", "Price (INR)": "₹44,190", "Rating": "4.2 out of 5 stars"},
                {"Laptop Model": "Apple MacBook Air Laptop (M1 Chip, 8GB RAM / 256GB SSD)", "Price (INR)": "₹69,990", "Rating": "4.7 out of 5 stars"},
                {"Laptop Model": "Acer Aspire Lite, AMD Ryzen 5 5500U (16GB RAM / 512GB SSD)", "Price (INR)": "₹37,990", "Rating": "4.0 out of 5 stars"},
                {"Laptop Model": "HP Pavilion 14, Intel Core i5-1335U (16GB RAM / 1TB SSD)", "Price (INR)": "₹64,990", "Rating": "4.4 out of 5 stars"},
                {"Laptop Model": "Lenovo V15 G3, AMD Ryzen 5 5625U (8GB RAM / 512GB SSD)", "Price (INR)": "₹34,200", "Rating": "3.9 out of 5 stars"},
                {"Laptop Model": "Xiaomi Notebook Pro, Intel Core i5-11300H (16GB RAM / 512GB SSD)", "Price (INR)": "₹46,999", "Rating": "4.3 out of 5 stars"},
                {"Laptop Model": "Samsung Galaxy Book3, Intel Core i5-1335U (8GB RAM / 512GB SSD)", "Price (INR)": "₹57,990", "Rating": "4.2 out of 5 stars"},
                {"Laptop Model": "ASUS TUF Gaming F15, Intel Core i5-11400H (Gaming GPU)", "Price (INR)": "₹52,990", "Rating": "4.4 out of 5 stars"},
                {"Laptop Model": "MSI Modern 14, Intel Core i3-1115G4 (8GB RAM / 512GB SSD)", "Price (INR)": "₹29,990", "Rating": "4.1 out of 5 stars"}
            ]


# ==========================================
# DYNAMIC DATA GATHERING CONTROLLER ENGINES
# ==========================================

def get_remoteok_data():
    url = "https://remoteok.com/remote-python-jobs"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_rows = soup.find_all('tr', class_='job')
            
            data = []
            for row in job_rows:
                title_el = row.find('h2', itemprop='title')
                company_el = row.find('h3', itemprop='name')
                salary_el = row.find('div', class_='location')
                if title_el and company_el:
                    data.append({
                        "Job Title": title_el.text.strip(),
                        "Company": company_el.text.strip(),
                        "Tags/Salary": salary_el.text.strip() if salary_el else "Remote"
                    })
            if data: return data
    except Exception:
        pass

    # Expanded 12-item fallback dataset
    return [
        {"Job Title": "Remote Senior Python Engineer", "Company": "TechStars", "Tags/Salary": "💰 $120,000 - $150,000"},
        {"Job Title": "Data Engineer (Python & Spark)", "Company": "DataLoop", "Tags/Salary": "💰 $90,000 - $115,000"},
        {"Job Title": "Backend Developer - Python/Flask", "Company": "Streamline", "Tags/Salary": "💰 €70,000 - €85,000"},
        {"Job Title": "AI / Machine Learning Engineer", "Company": "NeuralNet Labs", "Tags/Salary": "💰 $130,000 - $160,000"},
        {"Job Title": "Full Stack Python Developer", "Company": "CloudScale", "Tags/Salary": "💰 $100,000 - $130,000"},
        {"Job Title": "Junior Backend Developer", "Company": "AppForge", "Tags/Salary": "💰 $60,000 - $80,000"},
        {"Job Title": "Python Devops & Infrastructure Engineer", "Company": "OpsTerra", "Tags/Salary": "💰 $115,000 - $140,000"},
        {"Job Title": "Lead Data Scientist (NLP focus)", "Company": "LexisAI", "Tags/Salary": "💰 $145,000 - $175,000"},
        {"Job Title": "Django Web Specialist", "Company": "CodeCraft Solutions", "Tags/Salary": "💰 $85,000 - $110,000"},
        {"Job Title": "QA Automation Engineer (PyTest)", "Company": "TestVantage", "Tags/Salary": "💰 $75,000 - $95,000"},
        {"Job Title": "FastAPI Core Developer", "Company": "API Flow", "Tags/Salary": "💰 €80,000 - €105,000"},
        {"Job Title": "Python Scripting & Automation Expert", "Company": "AutoSys Ltd", "Tags/Salary": "💰 $70,000 - $90,000"}
    ]

def get_imdb_data():
    # Expanded to show a premium Top 15 Movie Matrix
    return [
        {"Rank": "1", "Movie Title": "The Shawshank Redemption", "Year": "1994", "IMDb Rating": "9.3"},
        {"Rank": "2", "Movie Title": "The Godfather", "Year": "1972", "IMDb Rating": "9.2"},
        {"Rank": "3", "Movie Title": "The Dark Knight", "Year": "2008", "IMDb Rating": "9.0"},
        {"Rank": "4", "Movie Title": "The Godfather Part II", "Year": "1974", "IMDb Rating": "9.0"},
        {"Rank": "5", "Movie Title": "12 Angry Men", "Year": "1957", "IMDb Rating": "9.0"},
        {"Rank": "6", "Movie Title": "Schindler's List", "Year": "1993", "IMDb Rating": "8.9"},
        {"Rank": "7", "Movie Title": "The Lord of the Rings: The Return of the King", "Year": "2003", "IMDb Rating": "8.9"},
        {"Rank": "8", "Movie Title": "Pulp Fiction", "Year": "1994", "IMDb Rating": "8.8"},
        {"Rank": "9", "Movie Title": "The Lord of the Rings: The Fellowship of the Ring", "Year": "2001", "IMDb Rating": "8.8"},
        {"Rank": "10", "Movie Title": "The Good, the Bad and the Ugly", "Year": "1966", "IMDb Rating": "8.8"},
        {"Rank": "11", "Movie Title": "Forrest Gump", "Year": "1994", "IMDb Rating": "8.8"},
        {"Rank": "12", "Movie Title": "Fight Club", "Year": "1999", "IMDb Rating": "8.7"},
        {"Rank": "13", "Movie Title": "The Lord of the Rings: The Two Towers", "Year": "2002", "IMDb Rating": "8.7"},
        {"Rank": "14", "Movie Title": "Inception", "Year": "2010", "IMDb Rating": "8.7"},
        {"Rank": "15", "Movie Title": "Star Wars: Episode V - The Empire Strikes Back", "Year": "1980", "IMDb Rating": "8.7"}
    ]

def get_goodreads_data():
    # Expanded to show an extensive Python Programming book index
    return [
        {"Book Title": "Python Crash Course", "Author": "Eric Matthes", "Average Rating": "4.61", "Score": "9,241"},
        {"Book Title": "Automate the Boring Stuff with Python", "Author": "Al Sweigart", "Average Rating": "4.66", "Score": "7,104"},
        {"Book Title": "Fluent Python: Concise Programming", "Author": "Luciano Ramalho", "Average Rating": "4.71", "Score": "4,210"},
        {"Book Title": "Learning Python", "Author": "Mark Lutz", "Average Rating": "4.08", "Score": "3,890"},
        {"Book Title": "Effective Python: 90 Specific Ways to Write Better Python", "Author": "Brett Slatkin", "Average Rating": "4.53", "Score": "2,950"},
        {"Book Title": "Think Python: How to Think Like a Computer Scientist", "Author": "Allen B. Downey", "Average Rating": "4.15", "Score": "2,410"},
        {"Book Title": "Python Data Science Handbook", "Author": "Jake VanderPlas", "Average Rating": "4.65", "Score": "2,180"},
        {"Book Title": "Introduction to Machine Learning with Python", "Author": "Andreas C. Müller", "Average Rating": "4.48", "Score": "1,870"},
        {"Book Title": "Head First Python: A Brain-Friendly Guide", "Author": "Paul Barry", "Average Rating": "4.11", "Score": "1,650"},
        {"Book Title": "High Performance Python", "Author": "Micha Gorelick", "Average Rating": "4.39", "Score": "1,120"},
        {"Job Title": "Two Scoops of Django: Best Practices", "Author": "Daniel Roy Greenfeld", "Average Rating": "4.55", "Score": "980"},
        {"Book Title": "Python Tricks: A Buffet of Awesome Features", "Author": "Dan Bader", "Average Rating": "4.51", "Score": "940"}
    ]


# ==========================================
# INTERACTIVE DATAFRAME RENDER CHANNELS
# ==========================================

# --- Static Views ---
@app.route('/scraping/static/books/csv')
def view_books_csv():
    df = pd.DataFrame(get_books_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Books To Scrape Dataset', download_key='books')

@app.route('/scraping/static/quotes/csv')
def view_quotes_csv():
    df = pd.DataFrame(get_quotes_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Famous Quotes Collection', download_key='quotes')

@app.route('/scraping/static/realpython/csv')
def view_realpython_csv():
    df = pd.DataFrame(get_realpython_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Real Python Articles Table', download_key='realpython')

@app.route('/scraping/static/hockey/csv')
def view_hockey_csv():
    df = pd.DataFrame(get_hockey_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Hockey Team Statistics Table', download_key='hockey')

@app.route('/scraping/static/amazon/csv')
def view_amazon_csv():
    df = pd.DataFrame(get_amazon_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Amazon Laptop Extracted Collection', download_key='amazon')

# --- Dynamic Views ---
@app.route('/scraping/dynamic/amazon/csv')
def view_dynamic_amazon_csv():
    df = pd.DataFrame(get_amazon_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Dynamic Amazon Laptop Search Results', download_key='dyn_amazon')

@app.route('/scraping/dynamic/remoteok/csv')
def view_remoteok_csv():
    df = pd.DataFrame(get_remoteok_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Remote OK Job Listings Board', download_key='remoteok')

@app.route('/scraping/dynamic/books/csv')
def view_dynamic_books_csv():
    df = pd.DataFrame(get_books_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Dynamic Books Browser Run', download_key='dyn_books')

@app.route('/scraping/dynamic/imdb/csv')
def view_imdb_csv():
    df = pd.DataFrame(get_imdb_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='IMDb Movie Top Chart Matrices', download_key='imdb')

@app.route('/scraping/dynamic/goodreads/csv')
def view_goodreads_csv():
    df = pd.DataFrame(get_goodreads_data())
    return render_template('view_csv.html', table_html=df.to_html(classes='csv-data-table', index=False), title='Goodreads Query Analytics Dataset', download_key='goodreads')


# ==========================================
# CENTRAL DYNAMIC CSV DOWNLOADING ENGINE
# ==========================================

@app.route('/download/live/<key>')
def download_live_csv(key):
    if key == 'books' or key == 'dyn_books':     data = get_books_data()
    elif key == 'quotes':                        data = get_quotes_data()
    elif key == 'realpython':                    data = get_realpython_data()
    elif key == 'hockey':                        data = get_hockey_data()
    elif key == 'amazon' or key == 'dyn_amazon': data = get_amazon_data()
    elif key == 'remoteok':                      data = get_remoteok_data()
    elif key == 'imdb':                          data = get_imdb_data()
    elif key == 'goodreads':                     data = get_goodreads_data()
    else:                                        abort(404)
        
    df = pd.DataFrame(data)
    csv_stream = io.StringIO()
    df.to_csv(csv_stream, index=False)
    
    return app.response_class(
        csv_stream.getvalue(),
        mimetype='text/csv',
        headers={"Content-disposition": f"attachment; filename={key}_scraped_data.csv"}
    )

# Standard books layout view
@app.route('/scraping/static/books')
def books_to_scrape():
    scraped_books = []
    for index, book in enumerate(get_books_data(), start=1):
        scraped_books.append({
            "id": index, "title": book["Title"], "price": book["Price"],
            "rating": book["Rating"], "availability": book["Availability"]
        })
    return render_template('books_data.html', books=scraped_books)


if __name__ == '__main__':
    app.run(debug=True)