import subprocess
import sys
from typing import List

def install_package(package: str) -> None:
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def is_package_installed(package: str) -> bool:
    try:
        subprocess.check_output([sys.executable, "-m", "pip", "show", package])
        return True
    except subprocess.CalledProcessError:
        return False

required_packages: List[str] = ['aiohttp', 'pyisemail', 'beautifulsoup4']

for package in required_packages:
    if not is_package_installed(package):
        print(f"Installing {package}...")
        install_package(package)

from config import load_credentials, load_user_agents
from scraper import google_search, extract_emails
from email_storage import save_emails_to_json
from utils import validate_input
import asyncio

async def main() -> None:
    print("Starting program...")
    api_key, cx = load_credentials()
    user_agents = load_user_agents()

    query = input("Enter your search query: ").strip()
    print(f"Query entered: {query}")

    if not query:
        print("No query entered. Exiting.")
        exit(1)

    try:
        num_results = int(input("Enter the number of results you want to extract: ").strip())
    except ValueError:
        print("Number of results must be a valid integer.")
        exit(1)

    validate_input(query, num_results)

    search_results = await google_search(query, api_key, cx, num_results, user_agents)
    if not search_results:
        print("No search results found.")
        exit(0)

    all_emails = await asyncio.gather(
        *[extract_emails(url, user_agents) for url in search_results]
    )

    all_emails = [email for sublist in all_emails for email in sublist]

    if all_emails:
        print(f"Total {len(all_emails)} email(s) found and saved.")
        save_emails_to_json(all_emails)
    else:
        print("No emails found.")

if __name__ == "__main__":
    asyncio.run(main())
