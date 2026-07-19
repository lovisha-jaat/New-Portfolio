import io
import os
import subprocess
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

@app.route('/education')
def education():
    return render_template('education.html')

@app.route('/six-weeks-journey')
def six_weeks_journey():
    return render_template('six_weeks.html')

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
            response.encoding = 'utf-8' 
            
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
    base_amazon_url = "https://www.amazon.in"
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
                link_el = p.find('a', class_='a-link-normal s-no-outline')
                
                if title_el:
                    clean_title = title_el.text.strip()[:80] + "..."
                    product_url = base_amazon_url + link_el['href'] if link_el else url
                    clickable_title = f'<a href="{product_url}" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">{clean_title}</a>'
                    
                    data.append({
                        "Laptop Model": clickable_title,
                        "Price (INR)": "₹" + price_el.text.strip() if price_el else "N/A",
                        "Rating": rating_el.text.strip() if rating_el else "No reviews yet"
                    })
            if data: return data
    except Exception:
        pass
    
    return [
        {"Laptop Model": '<a href="https://www.amazon.in/s?k=hp+laptop+15s" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">HP Laptop 15s, AMD Ryzen 3 5300U</a>', "Price (INR)": "₹32,490", "Rating": "4.1 out of 5 stars"},
        {"Laptop Model": '<a href="https://www.amazon.in/s?k=asus+vivobook+15" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">ASUS Vivobook 15, Intel Core i5-1235U</a>', "Price (INR)": "₹49,990", "Rating": "4.3 out of 5 stars"},
        {"Laptop Model": '<a href="https://www.amazon.in/s?k=lenovo+ideapad+slim+3" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">Lenovo IdeaPad Slim 3, Intel Core i3</a>', "Price (INR)": "₹35,990", "Rating": "4.0 out of 5 stars"},
        {"Laptop Model": '<a href="https://www.amazon.in/s?k=dell+inspiron+3520" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">Dell Inspiron 3520, Intel Core i5</a>', "Price (INR)": "₹44,190", "Rating": "4.2 out of 5 stars"},
        {"Laptop Model": '<a href="https://www.amazon.in/s?k=apple+macbook+air+m1" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">Apple MacBook Air Laptop (M1 Chip)</a>', "Price (INR)": "₹69,990", "Rating": "4.7 out of 5 stars"},
        {"Laptop Model": '<a href="https://www.amazon.in/s?k=acer+aspire+lite" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">Acer Aspire Lite, AMD Ryzen 5</a>', "Price (INR)": "₹37,990", "Rating": "4.0 out of 5 stars"}
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

    return [
        {"Job Title": "Remote Senior Python Engineer", "Company": "TechStars", "Tags/Salary": "$120,000 - $150,000"},
        {"Job Title": "Data Engineer (Python & Spark)", "Company": "DataLoop", "Tags/Salary": "$90,000 - $115,000"},
        {"Job Title": "Backend Developer - Python/Flask", "Company": "Streamline", "Tags/Salary": "$70,000 - $85,000"}
    ]

def get_imdb_data():
    return [
        {"Rank": "1", "Movie Title": "The Shawshank Redemption", "Year": "1994", "IMDb Rating": "9.3"},
        {"Rank": "2", "Movie Title": "The Godfather", "Year": "1972", "IMDb Rating": "9.2"},
        {"Rank": "3", "Movie Title": "The Dark Knight", "Year": "2008", "IMDb Rating": "9.0"}
    ]

def get_goodreads_data():
    return [
        {"Book Title": "Python Crash Course", "Author": "Eric Matthes", "Average Rating": "4.61", "Score": "9,241"},
        {"Book Title": "Automate the Boring Stuff with Python", "Author": "Al Sweigart", "Average Rating": "4.66", "Score": "7,104"},
        {"Book Title": "Fluent Python: Concise Programming", "Author": "Luciano Ramalho", "Average Rating": "4.71", "Score": "4,210"}
    ]


# ==========================================
# INTERACTIVE DATAFRAME RENDER CHANNELS
# ==========================================

@app.route('/powerbi-dashboards')
def powerbi_dashboards():
    return render_template('powerbi.html', title='PowerBI Analytics Dashboards')

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
    table_html = df.to_html(classes='csv-data-table', index=False, escape=False)
    return render_template('view_csv.html', table_html=table_html, title='Amazon Laptop Extracted Collection', download_key='amazon')


# =========================================================
# NEW CRITICAL FIX: DYNAMIC INTERACTIVE WORKSPACE CONTROLLER
# =========================================================

@app.route('/ml-workspace')
def ml_workspace():
    notebooks = []
    notebooks_dir = os.path.join(app.static_folder, 'notebooks_html')
    
    # Debug lines: prints directly to your VS Code terminal window
    print("--- TESTING JUPYTER DIRECTORY SCANNER ---")
    print(f"Looking for HTML files inside: {notebooks_dir}")
    print(f"Folder exists? {os.path.exists(notebooks_dir)}")
    
    if os.path.exists(notebooks_dir):
        files = [f for f in os.listdir(notebooks_dir) if f.endswith('.html')]
        print(f"Found files count: {len(files)}")
        for idx, file in enumerate(sorted(files), start=1):
            clean_name = file.replace('.html', '').replace('_', ' ').replace('-', ' ').title()
            notebooks.append({
                "id": idx,
                "filename": file,
                "display_name": clean_name
            })
            
    return render_template('ml_workspace.html', title='Machine Learning Workspace', notebooks=notebooks)


# =========================================================
# DYNAMIC VIEW ROUTE ENDPOINTS
# =========================================================

@app.route('/scraping/dynamic/amazon/csv')
def view_dynamic_amazon_csv():
    df = pd.DataFrame(get_amazon_data())
    table_html = df.to_html(classes='csv-data-table', index=False, escape=False)
    return render_template('view_csv.html', table_html=table_html, title='Dynamic Amazon Laptop Search Results', download_key='dyn_amazon', back_url='/scraping/dynamic')

@app.route('/scraping/dynamic/remoteok/csv')
def view_remoteok_csv():
    df = pd.DataFrame(get_remoteok_data())
    table_html = df.to_html(classes='csv-data-table', index=False)
    return render_template('view_csv.html', table_html=table_html, title='Remote OK Job Listings Board', download_key='remoteok', back_url='/scraping/dynamic')

@app.route('/scraping/dynamic/books/csv')
def view_dynamic_books_csv():
    df = pd.DataFrame(get_books_data())
    table_html = df.to_html(classes='csv-data-table', index=False)
    return render_template('view_csv.html', table_html=table_html, title='Dynamic Books Browser Run', download_key='dyn_books', back_url='/scraping/dynamic')

@app.route('/scraping/dynamic/imdb/csv')
def view_imdb_csv():
    df = pd.DataFrame(get_imdb_data())
    table_html = df.to_html(classes='csv-data-table', index=False)
    return render_template('view_csv.html', table_html=table_html, title='IMDb Movie Top Chart Matrices', download_key='imdb', back_url='/scraping/dynamic')

@app.route('/scraping/dynamic/goodreads/csv')
def view_goodreads_csv():
    df = pd.DataFrame(get_goodreads_data())
    table_html = df.to_html(classes='csv-data-table', index=False)
    return render_template('view_csv.html', table_html=table_html, title='Goodreads Query Analytics Dataset', download_key='goodreads', back_url='/scraping/dynamic')


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

@app.route('/scraping/static/books')
def books_to_scrape():
    scraped_books = []
    for index, book in enumerate(get_books_data(), start=1):
        scraped_books.append({
            "id": index, "title": book["Title"], "price": book["Price"],
            "rating": book["Rating"], "availability": book["Availability"]
        })
    return render_template('books_data.html', books=scraped_books)

@app.route('/scraping/api')
def api_scraping():
    return render_template('api_scraping.html')


# ==========================================
# LIVE API DATA GATHERING CONTROLLER ENGINES
# ==========================================

def get_universities_data():
    url = "https://gyansetu.codroidhub.com/api/universities"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            if isinstance(json_data, list) and len(json_data) > 0:
                data = []
                for item in json_data[:25]:
                    raw_domain = item.get("domain", "N/A") or ", ".join(item.get("domains", []))
                    clickable_domain = f'<a href="http://{raw_domain}" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">{raw_domain}</a>'
                    data.append({
                        "University Name": item.get("name", "N/A"),
                        "Domain": clickable_domain
                    })
                return data
    except Exception as e:
        print(f"Live API Fetch Error (Universities): {e}")
    
    fallback_raw = [
        {"University Name": "Indian Institute of Technology Delhi", "Domain": "iitd.ac.in"},
        {"University Name": "Indian Institute of Science", "Domain": "iisc.ac.in"},
        {"University Name": "University of Delhi", "Domain": "du.ac.in"}
    ]
    
    data = []
    for item in fallback_raw:
        clickable_domain = f'<a href="http://{item["Domain"]}" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">{item["Domain"]}</a>'
        data.append({
            "University Name": item["University Name"],
            "Domain": clickable_domain
        })
    return data

def get_fakestore_data():
    url = "https://fakestoreapi.com/products"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            data = []
            for item in json_data[:25]:
                data.append({
                    "Product ID": item.get("id"),
                    "Title": item.get("title"),
                    "Price": f"${item.get('price')}",
                    "Category": item.get("category"),
                    "Rating": f"{item.get('rating', {}).get('rate', 0)} ({item.get('rating', {}).get('count', 0)} reviews)"
                })
            return data
    except Exception as e:
        print(f"Live API Fetch Error (FakeStore): {e}")
    return [{"Product ID": "1", "Title": "Fjallraven Backpack", "Price": "$109.95", "Category": "men's clothing", "Rating": "3.9 (120 reviews)"}]

def get_placeholder_data():
    url = "https://api.github.com/events"
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Accept": "application/vnd.github.v3+json"
        }
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            data = []
            for event in json_data[:25]:
                actor = event.get("actor", {})
                repo = event.get("repo", {})
                repo_name = repo.get("name", "Unknown-Repo")
                repo_link = f"https://github.com/{repo_name}"
                clickable_repo = f'<a href="{repo_link}" target="_blank" rel="noopener noreferrer" style="color: #505967; text-decoration: none; font-weight: 500;">{repo_name}</a>'
                
                data.append({
                    "Event ID": event.get("id", "N/A"),
                    "Developer Username": actor.get("login", "Anonymous"),
                    "Action Type": event.get("type", "PushEvent").replace("Event", " Action"),
                    "Target Repository": clickable_repo
                })
            return data
    except Exception as e:
        print(f"Live GitHub API Scrape Error: {e}")
        
    return [
        {"Event ID": "40219481", "Developer Username": "linus-torvalds", "Action Type": "Push Action", "Target Repository": '<a href="https://github.com/torvalds/linux" target="_blank" style="color: #38bdf8; text-decoration: none;">torvalds/linux</a>'}
    ]

def get_dummyjson_data():
    url = "https://dummyjson.com/products"
    try:
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            json_data = response.json()
            products_list = json_data.get("products", [])
            data = []
            for item in products_list[:25]:
                data.append({
                    "Item": item.get("title"),
                    "Price": f"${item.get('price')}",
                    "Stock Status": item.get("stock"),
                    "Brand": item.get("brand", "Generic"),
                    "Category": item.get("category")
                })
            return data
    except Exception as e:
        print(f"Live API Fetch Error (DummyJSON): {e}")
    return [{"Item": "Essence Mascara Lash Princess", "Price": "$9.99", "Stock Status": "5", "Brand": "Essence", "Category": "beauty"}]

# ==========================================
# LIVE API VIEWS
# ==========================================

@app.route('/scraping/api/universities/csv')
def view_universities_csv():
    df = pd.DataFrame(get_universities_data())
    table_html = df.to_html(classes='csv-data-table', index=False, escape=False)
    return render_template('view_csv.html', table_html=table_html, title='Codroid Hub Universities Catalog', download_key='api_uni', back_url='/scraping/api')

@app.route('/scraping/api/fakestore/csv')
def view_fakestore_csv():
    df = pd.DataFrame(get_fakestore_data())
    table_html = df.to_html(classes='csv-data-table', index=False, escape=False)
    return render_template('view_csv.html', table_html=table_html, title='FakeStore E-Commerce Dataset', download_key='api_fake', back_url='/scraping/api')

@app.route('/scraping/api/placeholder/csv')
def view_placeholder_csv():
    df = pd.DataFrame(get_placeholder_data())
    table_html = df.to_html(classes='csv-data-table', index=False, escape=False)
    return render_template('view_csv.html', table_html=table_html, title='Live GitHub Global Events Stream', download_key='api_place', back_url='/scraping/api')

@app.route('/scraping/api/dummyjson/csv')
def view_dummyjson_csv():
    df = pd.DataFrame(get_dummyjson_data())
    table_html = df.to_html(classes='csv-data-table', index=False, escape=False)
    return render_template('view_csv.html', table_html=table_html, title='DummyJSON Nested Store Grid', download_key='api_dummy', back_url='/scraping/api')

if __name__ == '__main__':
    app.run(debug=True)
