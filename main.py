import requests
import random
import json
import sys
import logging
import time
import os
from concurrent.futures import ThreadPoolExecutor
from requests.exceptions import Timeout, ConnectionError, HTTPError
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(
    format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO, datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

OUTPUT_FILE = "Data_coupon.json"

SECRET_KEY = os.environ.get("SHEIN_SECRET_KEY", "3LFcKwBTXcsMzO5LaUbNYoyMSpt7M3RP5dW9ifWffzg")
GITHUB_TOKEN = "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"  # ✅ Your token
GITHUB_REPO = "Sheincpn/Shein"  # Change to your repo (example: "RishabhJain/SheinCoupons")
GITHUB_BRANCH = "main"

class SheinCliFetcher:
    # ... keep all your SheinCliFetcher class as-is ...
    # only change generate_indian_numbers() to valid prefixes ['9'] if needed
    def generate_indian_numbers(self, count):
        numbers = []
        valid_starters = ['9']  # only 9 prefix as you said
        for _ in range(count):
            first_digit = random.choice(valid_starters)
            remaining_digits = ''.join(random.choices('0123456789', k=9))
            number = first_digit + remaining_digits
            numbers.append(number)
        return numbers

# Save locally
def save_profile_data(formatted_data):
    try:
        data_to_save = formatted_data.copy()
        data_to_save["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
        with open(OUTPUT_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(data_to_save) + '\n')
        push_to_github()
    except Exception as e:
        logger.error(f"Failed to save profile: {e}")

# Push to GitHub using REST API
def push_to_github():
    try:
        with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
            content = f.read()

        url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{OUTPUT_FILE}"
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github+json"
        }

        # Check if file exists
        r = requests.get(url + f"?ref={GITHUB_BRANCH}", headers=headers)
        if r.status_code == 200:
            sha = r.json()["sha"]
        else:
            sha = None

        data = {
            "message": f"Update {OUTPUT_FILE} at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "content": content.encode("utf-8").decode("utf-8").encode("base64").decode("utf-8"),
            "branch": GITHUB_BRANCH
        }
        if sha:
            data["sha"] = sha

        response = requests.put(url, headers=headers, json=data, timeout=15)
        if response.status_code in [200, 201]:
            logger.info("✅ Data pushed to GitHub successfully.")
        else:
            logger.warning(f"❌ Failed to push to GitHub. Status: {response.status_code} - {response.text}")

    except Exception as e:
        logger.error(f"Error pushing to GitHub: {e}")

# --- Main CLI Automation ---
def main_cli_automation():
    fetcher = SheinCliFetcher()
    MAX_WORKERS = 12
    BATCH_SIZE = 1200
    total_checked = 0
    found_count = 0

    try:
        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            while True:
                numbers_to_test = fetcher.generate_indian_numbers(BATCH_SIZE)
                logger.info(f"--- Generated batch {BATCH_SIZE}")
                results = executor.map(fetcher.process_single_number, numbers_to_test)

                for result in results:
                    total_checked += 1
                    if result:
                        phone_number, profile_data = result
                        _, _, structured_data = fetcher.format_profile_response(profile_data, phone_number)
                        if structured_data:
                            found_count += 1
                            save_profile_data(structured_data)

                time.sleep(random.uniform(2.0, 3.0))

    except KeyboardInterrupt:
        print("🛑 User requested stop. Summary:")
        print(f"Total Numbers Checked: {total_checked}")
        print(f"Profiles Found: {found_count}")
    except Exception as e:
        logger.critical(f"Critical error: {e}")


if __name__ == "__main__":
    main_cli_automation()
