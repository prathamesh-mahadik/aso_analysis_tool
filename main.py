from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
import requests
from fastapi.middleware.cors import CORSMiddleware
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel
import os
import json

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
    model="gpt-4o",
    messages=[
        {
            "role": "user",
            "content": """Act as a Google App Store Optimization (ASO) expert. Analyze the given app data and provide an optimized response in **pure JSON format**.

            ### **App Data:**"""+
            
           f"{app_data}"+

           """ ### **Strict Output Requirements:**
            - The output **must** be **a valid JSON object** (no markdown, no extra text, no `\n` characters).
            - **Do not** use triple backticks (` ```json `) or any special formatting.
            - The JSON must contain the following fields:
              - `keywords`: List of target keywords in the app description (minimum 8-10 keywords).
              - `keyword_suggestions`: List of additional keyword suggestions (minimum 5-10 keywords)..
              - `title`: ASO-optimized relevant title (max 30 characters).
              - `short_description`: Optimized relevant short description (max 80 characters).
              - `long_description`: Optimized relevant long description (min 2500 characters and max 3000 characters).
              - `rank_time_estimate`: Estimated improvement timeframe.
              - `review_suggestions`: List of review sentence suggestions (at least 5).

            ### **JSON Format Example:**
            {
              "keywords": [],
              "keyword_suggestions": [],
              "title": "ASO-optimized title (max 30 characters)",
              "short_description": "Short Description text (max 80 characters)s",
              "long_description": "Long Description text (min 2500 characters and max 3000 characters)",
              "rank_time_estimate": "",
              "review_suggestions": [],
            }

            Strictly return the response **as a JSON object only**, without any additional formatting or text.
            """
                    }
                ],
                response_format={"type": "json_object"}  # ✅ Enforces pure JSON output
        )


        # return app_data
        # print(completion.choices[0].message.content)
        
        # Parse the JSON string into a Python dictionary
        new_response = json.loads(completion.choices[0].message.content)

        # Merge the two dictionaries
        combined_data = {}
        combined_data['app_data']=app_data
        combined_data['analysis_result']=new_response #completion.choices[0].message.content
        # Convert back to JSON format (for response)
        analysis_result = json.dumps(combined_data, indent=2)
        print(combined_data)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    return JSONResponse(content=combined_data)    
    

@app.get("/scrape")
def scrape_playstore(url: str = Query(..., title="Google Play Store App URL")):
    return scrape_playstore_app_data(url)


 