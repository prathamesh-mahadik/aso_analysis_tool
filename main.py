from fastapi import FastAPI, HTTPException # type: ignore
from pydantic import BaseModel, HttpUrl # type: ignore
import httpx
from bs4 import BeautifulSoup

app = FastAPI()

class CrawlRequest(BaseModel):
    url: HttpUrl

@app.post("/crawl")
async def crawl_url(request: CrawlRequest):
    try:
        # Fetch the URL content using httpx
        async with httpx.AsyncClient() as client:
            response = await client.get(request.url)

        # Raise an error if the status is not 200
        response.raise_for_status()

        # Parse the HTML content with BeautifulSoup
        soup = BeautifulSoup(response.text, "html.parser")

        # Extract all text content from the webpage
        extracted_text = soup.get_text(separator="\n", strip=True)

        return {"url": request.url, "content": extracted_text}

    except httpx.RequestError as e:
        raise HTTPException(status_code=400, detail=f"An error occurred while fetching the URL: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred: {str(e)}")
