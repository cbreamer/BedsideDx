import requests
from bs4 import BeautifulSoup

# Function to scrape a website for relevant information
def scrape_website(url):
    try:
        response = requests.get(url)
        response.raise_for_status()  # Check if the request was successful
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract relevant content (this depends on the structure of the website)
        content = soup.find_all('p')  # Just an example; adjust based on your needs
        extracted_text = " ".join([p.get_text() for p in content])
        return extracted_text
    except Exception as e:
        print(f"Error scraping website: {e}")
        return ""

# Scraping content from a publicly available website
website_url = "https://stanfordmedicine25.stanford.edu/the25/aorticregurgitation.html"  # Replace with the desired URL
scraped_data = scrape_website(website_url)
#print(scraped_data)
