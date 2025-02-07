from fastapi import FastAPI, Query
import requests
from bs4 import BeautifulSoup

app = FastAPI()

def scrape_playstore_app_data(url: str):
    """Scrapes data from a Google Play Store app URL."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    response = requests.get(url, headers=headers)
    if response.status_code != 200:
        return {"error": f"Failed to retrieve data for URL: {url}"}
    
    soup = BeautifulSoup(response.content, 'html.parser')
    app_data = {}
    
    def get_text_or_default(soup_element, default="Not Available"):
        return soup_element.text.strip() if soup_element else default
    
    try:
        app_data['Name'] = get_text_or_default(soup.find('title'))
        app_data['Developer URL'] = soup.find('meta', attrs={'name': 'appstore:developer_url'}).get('content', 'Not Available')
        app_data['Bundle ID'] = soup.find('meta', attrs={'name': 'appstore:bundle_id'}).get('content', 'Not Available')
        app_data['Description'] = get_text_or_default(soup.find('div', class_='bARER'))
        
        rating_value = soup.find('div', class_='jILTFe')
        app_data['Rating'] = get_text_or_default(rating_value)
        
        aria_label_div = soup.find('div', class_='I26one')
        app_data['Rating Description'] = aria_label_div['aria-label'] if aria_label_div and 'aria-label' in aria_label_div.attrs else 'Not Available'
        
        app_data['Number of Reviews'] = get_text_or_default(soup.find('div', class_='g1rdde'))
        app_data['Number of Downloads'] = soup.find_all('div', class_='ClM7O')[1].text.strip() if len(soup.find_all('div', class_='ClM7O')) > 1 else 'Not Available'
        
        developer = soup.find('div', class_='Vbfug auoIOc')
        app_data['Developer'] = developer.find('span').text.strip() if developer and developer.find('span') else 'Not Available'
        
        app_data['Price'] = get_text_or_default(soup.find('span', class_='VfPp2b'), default='Free')
    except Exception as e:
        return {"error": f"Error extracting data: {str(e)}"}
    
    return app_data

@app.get("/scrape")
def scrape_playstore(url: str = Query(..., title="Google Play Store App URL")):
    """API endpoint to scrape app data from the Google Play Store."""
    return scrape_playstore_app_data(url)
