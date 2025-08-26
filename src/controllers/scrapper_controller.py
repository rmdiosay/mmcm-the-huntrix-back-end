from fastapi import APIRouter
from src.entities.schemas import ScrapeRequest, ScrapeResponse
from src.services.scrapper_services import scrape_facebook_marketplace
import os

router = APIRouter(prefix="/scrape", tags=["Scrapper"])

@router.post("/facebook", response_model=ScrapeResponse)
def scrape_facebook(request: ScrapeRequest):
    # use environment variables for credentials
    fb_email = os.getenv("FB_EMAIL")
    fb_password = os.getenv("FB_PASSWORD")
    results = scrape_facebook_marketplace(request, fb_email, fb_password)
    return {"results": results}