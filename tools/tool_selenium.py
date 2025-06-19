"""
************************************************
    SELENIUM WEBSCRAPING TOOL FOR LANGGRAPH
************************************************
"""
from langchain_core.tools import tool

import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
import undetected_chromedriver as uc
from fake_useragent import UserAgent
import re

@tool("webscraping_tool")
def scrape_website(url, wait_time: int = 10):

    #ChromeOptions
    options = uc.ChromeOptions()
    options.add_argument('--user-agent=Mozilla/5.0 (iPhone; CPU iPhone OS 18_3_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.3.1 Mobile/15E148 Safari/604.1')

    #Stealth
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-blink-features=AutomationControlled')

    #Initializing
    driver = uc.Chrome(options=options)
    driver.get(url)

    # Wait for page to load
    WebDriverWait(driver, wait_time).until(
        EC.presence_of_element_located((By.TAG_NAME, "body"))
    )

    page_title = driver.title
    body_element = driver.find_element(By.TAG_NAME, "body")
    body_text = body_element.text
    cleaned_text = clean_text(body_text)

    result = {
            "title": page_title,
            "url": url,
            "content": cleaned_text,
            "status": "success"
        }
        
    return result

def clean_text(text):

    if not text:
        return "No text content found"

    # Remove excessive whitespace and newlines
    text = re.sub(r'\n\s*\n', '\n\n', text)  # Replace multiple newlines with double newline
    text = re.sub(r' +', ' ', text)  # Replace multiple spaces with single space
    text = text.strip()
    
    # Remove empty lines
    lines = [line.strip() for line in text.split('\n') if line.strip()]
    
    return '\n'.join(lines)

if __name__ == "__main__":
    test_url = "https://www.reddit.com/r/jdownloader/comments/q3xrgj/how_to_dark_mode_jdownloader_2/"
    result = scrape_website(test_url)
    print("SCRAPING RESULT:")
    print(result)
