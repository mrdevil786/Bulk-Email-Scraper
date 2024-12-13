import aiohttp
import asyncio
import random
from pyisemail import is_email
from bs4 import BeautifulSoup
import re
from typing import List
import logging

logger = logging.getLogger()

async def google_search(query: str, api_key: str, cx: str, num_results: int, user_agents: List[str]) -> List[str]:
    logger.info(f"Starting Google search for query: {query}")
    search_results: List[str] = []
    start_index = 1
    async with aiohttp.ClientSession() as session:
        while len(search_results) < num_results:
            url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}&start={start_index}'
            try:
                async with session.get(url, headers={'User-Agent': random.choice(user_agents)}, timeout=10) as response:
                    response.raise_for_status()
                    data = await response.json()
            except aiohttp.ClientError as e:
                logger.error(f"Error fetching search results: {e}")
                break
            if 'items' in data:
                search_results.extend(item['link'] for item in data['items'])
            if 'nextPage' not in data.get('queries', {}):
                break
            start_index += 10

    logger.info(f"Found {len(search_results)} search results for query: {query}")
    return search_results[:num_results]

async def extract_emails(url: str, user_agents: List[str]) -> List[str]:
    logger.info(f"Extracting emails from URL: {url}")
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers={'User-Agent': random.choice(user_agents)}, timeout=15) as response:
                response.raise_for_status()
                page_content = await response.text()
        except aiohttp.ClientError as e:
            logger.error(f"Error extracting emails from {url}: {e}")
            return []
        
        soup = BeautifulSoup(page_content, 'html.parser')
        page_text = soup.get_text()
        emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', page_text)
        valid_emails = [email for email in emails if is_email(email)]
        logger.info(f"Extracted {len(valid_emails)} valid emails from {url}.")
        return list(set(valid_emails))
