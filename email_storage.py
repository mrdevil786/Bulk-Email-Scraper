import json
from pathlib import Path
import logging
from typing import List

EMAIL_OUTPUT_FILENAME = 'emails.json'
logger = logging.getLogger()

def save_emails_to_json(emails: List[str], filename: str = EMAIL_OUTPUT_FILENAME) -> None:
    email_output_path = Path(filename)
    logger.info(f"Saving {len(emails)} emails to {filename}.")
    
    if email_output_path.exists():
        try:
            with email_output_path.open('r') as f:
                existing_emails = json.load(f)
        except json.JSONDecodeError:
            existing_emails = []
    else:
        existing_emails = []
    
    all_emails = set(existing_emails + emails)
    try:
        with email_output_path.open('w') as f:
            json.dump(list(all_emails), f, indent=4)
        logger.info(f"Emails have been saved to {filename}.")
    except IOError as e:
        logger.error(f"Error saving emails to {filename}: {e}")
        exit(1)
