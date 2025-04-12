import time
import random
import os
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from undetected_chromedriver import Chrome, ChromeOptions
from dotenv import load_dotenv

load_dotenv()

class LinkedInScraper:
    def __init__(self):
        self.options = ChromeOptions()
        self.options.add_argument('--headless')  # Run in headless mode
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.driver = None
        self.wait = None

    def login(self):
        """Login to LinkedIn"""
        self.driver = Chrome(options=self.options)
        self.wait = WebDriverWait(self.driver, 10)
        
        self.driver.get('https://www.linkedin.com/login')
        
        # Enter credentials
        email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
        password_field = self.driver.find_element(By.ID, 'password')
        
        email_field.send_keys(os.getenv('LINKEDIN_EMAIL'))
        password_field.send_keys(os.getenv('LINKEDIN_PASSWORD'))
        
        # Click login button
        login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
        login_button.click()
        
        # Wait for login to complete
        time.sleep(random.uniform(2, 4))

    def search_recruiters(self, job_title: str, location: str, max_results: int = 100) -> List[Dict]:
        """Search for recruiters based on job title and location"""
        if not self.driver:
            self.login()
        
        search_url = f"https://www.linkedin.com/search/results/people/?keywords={job_title}&location={location}&origin=FACETED_SEARCH"
        self.driver.get(search_url)
        
        recruiters = []
        while len(recruiters) < max_results:
            try:
                # Wait for search results to load
                self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, 'reusable-search__result-container')))
                
                # Get all recruiter cards
                recruiter_cards = self.driver.find_elements(By.CLASS_NAME, 'reusable-search__result-container')
                
                for card in recruiter_cards:
                    try:
                        name = card.find_element(By.CLASS_NAME, 'entity-result__title-text').text
                        role = card.find_element(By.CLASS_NAME, 'entity-result__primary-subtitle').text
                        company = card.find_element(By.CLASS_NAME, 'entity-result__secondary-subtitle').text
                        profile_url = card.find_element(By.CLASS_NAME, 'app-aware-link').get_attribute('href')
                        
                        recruiters.append({
                            'name': name,
                            'role': role,
                            'company': company,
                            'profile_url': profile_url,
                            'status': 'pending',
                            'created_at': time.time()
                        })
                        
                        if len(recruiters) >= max_results:
                            break
                            
                    except NoSuchElementException:
                        continue
                
                # Try to click next page if available
                try:
                    next_button = self.driver.find_element(By.CLASS_NAME, 'artdeco-pagination__button--next')
                    if 'artdeco-button--disabled' in next_button.get_attribute('class'):
                        break
                    next_button.click()
                    time.sleep(random.uniform(2, 4))
                except NoSuchElementException:
                    break
                    
            except TimeoutException:
                break
        
        return recruiters

    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit() 