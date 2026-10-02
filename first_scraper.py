from playwright.sync_api import sync_playwright
import time
import random

def scrape_books():
    """
    Scrapes book data from books.toscrape.com
    This is a practice site designed for learning.
    """
    books = []
    
    with sync_playwright() as p:
        # Launch a visible browser (so you can watch what happens)
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        
        # Go to the practice site
        page.goto("http://books.toscrape.com/")
        
        # Wait for the page to fully load
        page.wait_for_load_state("networkidle")
        
        # Find all book containers on the page
        book_elements = page.query_selector_all("article.product_pod")
        
        print(f"Found {len(book_elements)} books on this page")
        
        for book in book_elements:
            # Extract the data from each book element
            title = book.query_selector("h3 a").get_attribute("title")
            price = book.query_selector(".price_color").inner_text()
            url = book.query_selector("h3 a").get_attribute("href")
            
            books.append({
                "title": title,
                "price": price,
                "url": url
            })
            
            print(f"  - {title}: {price}")
        
        # Close the browser
        browser.close()
    
    return books

if __name__ == "__main__":
    print("🚀 Starting scraper...")
    results = scrape_books()
    print(f"\n✅ Scraped {len(results)} books total")
