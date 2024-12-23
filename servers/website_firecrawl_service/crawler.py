import os
import logging
from typing import List, Dict, Optional
from urllib.parse import urlparse
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from firecrawl import FirecrawlApp

from langsmith import traceable

from website_firecrawl_service.openai import Inference
from website_firecrawl_service.prompt import SYSTEM_CRAWLER_PROMPT, USER_CRAWLER_PROMPT

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

inference = Inference()

model_args = {
    "model": "gpt-4o-mini",
    "temperature": 0,
}

class CrawlerModel(BaseModel):
    target_urls: List[str] = Field(description="The domain URLs to be considered")
    justification: str = Field(description="The reason for selecting these target URLs")

class Page(BaseModel):
    metadata: Dict
    body: str

class FirecrawlClient:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        
        self.client = FirecrawlApp(api_key=os.getenv("FIRECRAWL_API_KEY"))

class WebsiteCrawler:
    def __init__(self):
        self._pages: List[Page] = []
        self.firecrawl = FirecrawlClient()

    def _normalize_url(self, url: str) -> str:
        """Normalize the URL and handle GitHub repositories specially"""
        if not url.startswith(('http://', 'https://')):
            if url.startswith(('http:/', 'https:/')):
                url = url.replace(':', '://')
            else:
                url = f'http://{url}'
        
        url_obj = urlparse(url)
        stem_url = url_obj.netloc

        # Special handling for GitHub URLs
        if 'github.com' in stem_url:
            path_segments = [seg for seg in url_obj.path.split('/') if seg]
            if len(path_segments) >= 2:
                owner, repo = path_segments[0:2]
                stem_url = f"{stem_url}/{owner}/{repo}"
        
        return stem_url
    

    @traceable(name="select_crawler_urls")
    async def _select_links(self, query: str, links: List[Dict]):  
        messages = [
            {"role": "system", "content": SYSTEM_CRAWLER_PROMPT.render()},
            {"role": "user", "content": USER_CRAWLER_PROMPT.render(query=query, links=links)}
        ]
        result = await inference.predict_with_parse_async(model_args, CrawlerModel, messages)
        return result.target_urls

    async def crawl(self, query: str, base_url: str, max_links: int = 100, llm_predict: bool = True) -> Optional[List[Page]]:
        """Fetch multiple pages using Firecrawl API and create Page objects"""
        try:
            logger.info(f"Searching for urls in {base_url}")
            
            self.base_url = self._normalize_url(base_url)

            # Map the URL to get a list of links
            map_result = self.firecrawl.client.map_url(
                self.base_url, 
                params={'limit': max_links}
            )
            
            if not map_result.get('success'):
                logger.error(f"Failed to map URL: {base_url}")
                return None
            
            # Select links based on relevance, given the user query
            links = await self._select_links(query, map_result['links']) if llm_predict else map_result['links']

            # Scrape the selected links
            for link in links[:]:
                try:
                    logger.info(f"Starting scrape for link: {link}")
                    
                    page = self.firecrawl.client.scrape_url(
                        link, 
                        params={
                            'formats': ['rawHtml'],
                        },
                    )       
                        
                    self._pages.append(Page(
                        body=page['rawHtml'],
                            metadata={
                                'url': page['metadata']['url'],
                                'title': page['metadata'].get('title', ''),
                                'description': page['metadata'].get('description', ''),
                                'language': page['metadata'].get('language', ''),
                            },
                        ))
                except Exception as e:
                    logger.error(f"Error scraping {link}: {str(e)}")
                    continue
                    
            return self._pages
            
        except Exception as e:
            logger.error(f"Error during crawl: {str(e)}")
            return None

