import subprocess
import sys
import importlib
import requests
from bs4 import BeautifulSoup
import re
import json
import os
import time
import logging
import random
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import importlib.metadata

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger()

def install_package(package):
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])
        logger.info(f"Package {package} installed successfully.")
    except subprocess.CalledProcessError as e:
        logger.error(f"Error installing package {package}: {e}")
        sys.exit(1)

def is_package_installed(package):
    try:
        importlib.import_module(package)
        return True
    except ImportError:
        return False

def ensure_packages_installed(packages):
    installed_packages = {dist.metadata['Name'].lower() for dist in importlib.metadata.distributions()}

    for package in packages:
        if package.lower() not in installed_packages:
            logger.info(f"Package {package} not found. Installing...")
            install_package(package)

required_packages = ['requests', 'beautifulsoup4']
ensure_packages_installed(required_packages)

def load_credentials(filename='credentials.json'):
    try:
        with open(filename, 'r') as f:
            credentials = json.load(f)
        return credentials['api_key'], credentials['cx']
    except (FileNotFoundError, KeyError, json.JSONDecodeError) as e:
        logger.error(f"Error loading credentials: {e}")
        sys.exit(1)

def load_user_agents(filename='user_agents.json'):
    try:
        with open(filename, 'r') as f:
            user_agents = json.load(f)
        return user_agents
    except (FileNotFoundError, json.JSONDecodeError) as e:
        logger.error(f"Error loading user agents: {e}")
        sys.exit(1)

def create_session(user_agents):
    session = requests.Session()
    retries = Retry(total=3, backoff_factor=1, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    session.headers.update({'User-Agent': random.choice(user_agents)})
    return session

def google_search(query, api_key, cx, num_results=10, user_agents=None):
    search_results = []
    start_index = 1
    session = create_session(user_agents)

    while len(search_results) < num_results:
        url = f'https://www.googleapis.com/customsearch/v1?q={query}&key={api_key}&cx={cx}&start={start_index}'
        try:
            logger.info(f"Sending request to Google Search API (start={start_index})...")
            response = session.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"Error during Google Search API request: {e}")
            break
        
        if 'items' in data:
            search_results.extend(item['link'] for item in data['items'])
        
        if 'nextPage' not in data.get('queries', {}):
            break
        
        start_index += 10

    return search_results[:num_results]

def extract_emails(url, user_agents):
    session = create_session(user_agents)
    
    try:
        logger.info(f"Fetching URL: {url}")
        response = session.get(url, timeout=15)
        response.raise_for_status()
    except requests.Timeout:
        logger.warning(f"Timeout error while fetching {url}")
        return []
    except requests.RequestException as e:
        logger.warning(f"Error fetching URL {url}: {e}")
        return []
    
    try:
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        emails = re.findall(email_pattern, page_text)
        
        cleaned_emails = []
        for email in emails:
            email = re.sub(r'(Address|Building)$', '', email)
            cleaned_emails.append(email)
        
        return list(set(cleaned_emails))
    
    except Exception as e:
        logger.error(f"Error processing page {url}: {e}")
        return []

def save_emails_to_json(emails, filename='email.json'):
    if os.path.exists(filename):
        try:
            with open(filename, 'r') as f:
                existing_emails = json.load(f)
        except json.JSONDecodeError:
            existing_emails = []
    else:
        existing_emails = []
    
    all_emails = set(existing_emails + emails)
    
    try:
        with open(filename, 'w') as f:
            json.dump(list(all_emails), f, indent=4)
        logger.info(f"Emails have been saved to {filename}.")
    except IOError as e:
        logger.error(f"Error saving emails to {filename}: {e}")
        sys.exit(1)

def validate_input(query, num_results):
    if not query.strip():
        logger.error("Search query cannot be empty.")
        sys.exit(1)
    if num_results <= 0:
        logger.error("Number of results must be greater than zero.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        api_key, cx = load_credentials('credentials.json')
        user_agents = load_user_agents('user_agents.json')
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
    
    query = input("Enter your search query: ").strip()
    try:
        num_results = int(input("Enter the number of results you want to extract: ").strip())
    except ValueError:
        logger.error("Number of results must be a valid integer.")
        sys.exit(1)
    
    validate_input(query, num_results)
    
    search_results = google_search(query, api_key, cx, num_results=num_results, user_agents=user_agents)
    
    if not search_results:
        logger.info("No search results found.")
        sys.exit(0)
    
    all_emails = []
    for idx, url in enumerate(search_results):
        logger.info(f"Processing {url} ({idx+1}/{len(search_results)})")
        emails = extract_emails(url, user_agents)
        if emails:
            logger.info(f"Found {len(emails)} email(s) on {url}")
            all_emails.extend(emails)
        
        if all_emails:
            save_emails_to_json(all_emails)
            logger.info("Emails saved so far. Continuing...")

    if all_emails:
        logger.info(f"Total {len(all_emails)} email(s) found and saved.")
        save_emails_to_json(all_emails)
    else:
        logger.info("No emails found.")
