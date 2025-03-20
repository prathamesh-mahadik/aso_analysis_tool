from fastapi import FastAPI, HTTPException, Query
import requests
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel
import os

app = FastAPI()

# Load API key from environment variable (recommended for security)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)



# Initia
# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
    analysis_result = {}
    
    def get_text_or_default(soup_element, default="Not Available"):
        return soup_element.text.strip() if soup_element else default
    
    try:
        app_data['Name'] = get_text_or_default(soup.find('title'))
        app_data['Developer URL'] = soup.find('meta', attrs={'name': 'appstore:developer_url'}).get('content', 'Not Available') # type: ignore
        app_data['Bundle ID'] = soup.find('meta', attrs={'name': 'appstore:bundle_id'}).get('content', 'Not Available') # type: ignore
        app_data['Description'] = get_text_or_default(soup.find('div', class_='bARER'))
        rating_value = soup.find('div', class_='jILTFe')
        rating_value_text = rating_value.text.strip() if rating_value else 'Not Available'
        app_data['Rating'] = rating_value_text  #get_text_or_default(rating_value)
        # Extract the rating description from the aria-label attribute
        aria_label_div = soup.find('div', class_='I26one')
        if aria_label_div and 'aria-label' in aria_label_div.attrs: # type: ignore
            rating_description_text = aria_label_div['aria-label'] # type: ignore
        else:
            rating_description_text = 'Not Available'
        app_data['Rating Description'] = rating_description_text  # aria_label_div['aria-label'] if aria_label_div and 'aria-label' in aria_label_div.attrs else 'Not Available'
    
        app_data['Number of Reviews'] = get_text_or_default(soup.find('div', class_='g1rdde'))
        app_data['Number of Downloads'] = soup.find_all('div', class_='ClM7O')[1].text.strip() if len(soup.find_all('div', class_='ClM7O')) > 1 else 'Not Available'
        developer = soup.find('div', class_='Vbfug auoIOc')
        app_data['Developer'] = developer.find('span').text.strip() if developer and developer.find('span') else 'Not Available' # type: ignore
        app_data['Price'] = get_text_or_default(soup.find('span', class_='VfPp2b'), default='Free')
    except Exception as e:
        return {"error": f"Error extracting data: {str(e)}"}
    
    
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Act as an Google App Store Optimization Expert and help increase this apps ranking which is live in the play store."+
                 f"This data is an app's the google play store listing data: {app_data} . I want you to analyze this and do the following:"+
                 "1) figure out all the keywords, as a list of strings"+
                 "2) Give a list of more keywords suggestion that can help increase the ranking, as a list of string."+
                 "3) Give an ASO optimized title of upto 30 characters, as a string."+
                 "4) Give an ASO optimized short description of upto 80 characters, as a string."+
                 "5) Give an ASO optimized long description of upto 3000 characters, as a string."+
                 "6) By who much will the rank increase and an estimation of time that is need for the rank to increase, as a string."+
                 "7) List of sentences with keywords that can be given as reviews to the app, as list of strings."+
                 "You have to provide this data in a specific json format: { keywords:[], keyword_suggestions:[], title:"", short_description:"", long_description:"", rank_time_estimate:"",review_suggestions:[]}"+
                 "Rules you need to follow strictly is that you must only return this above given json format in response and nothing extra."}
            ]
        )  
        # return app_data
        analysis_result= {"app_details":app_data, "analysis": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return analysis_result   
    

@app.get("/scrape")
def scrape_playstore(url: str = Query(..., title="Google Play Store App URL")):
    """API endpoint to scrape app data from the Google Play Store."""
    return scrape_playstore_app_data(url)


    
class GPTRequest(BaseModel):
    prompt: str

@app.post("/generate1")
def generate_text1():
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "user", "content": ""}
            ]
        )  
        return {"response": completion.choices[0].message.content}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))