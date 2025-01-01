from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import logging

class RobethoodScraper:
    def __init__(self):
        self.setup_driver()
        self.logger = logging.getLogger(__name__)

    def setup_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)

    def get_ads(self):
        try:
            self.driver.get("https://www.robethood.com")
            time.sleep(5)  # Wait for page to load
            
            # Get page source and parse with BeautifulSoup
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            # Extract ads (adjust selectors based on actual website structure)
            ads = []
            ad_elements = soup.find_all('div', class_='ad-container')  # Adjust class name
            
            for ad in ad_elements:
                ad_data = {
                    'id': ad.get('data-ad-id', ''),
                    'title': ad.find('h2', class_='ad-title').text.strip(),
                    'description': ad.find('p', class_='ad-description').text.strip(),
                    'image_url': ad.find('img', class_='ad-image')['src']
                }
                ads.append(ad_data)
            
            return {'status': 'success', 'ads': ads}
            
        except Exception as e:
            self.logger.error(f"Error scraping ads: {str(e)}")
            return {'status': 'error', 'message': str(e)}
        
    def close(self):
        self.driver.quit()
