import time
import random
import os
import urllib.parse
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from undetected_chromedriver import Chrome, ChromeOptions
from dotenv import load_dotenv

load_dotenv()

class LinkedInScraper:
    def __init__(self):
        self.options = ChromeOptions()
        # self.options.add_argument('--headless')  # Disabled headless mode for better reliability
        self.options.add_argument('--no-sandbox')
        self.options.add_argument('--disable-dev-shm-usage')
        self.options.add_argument('--disable-blink-features=AutomationControlled')
        self.options.add_argument('--disable-notifications')
        self.options.add_argument('--window-size=1920,1080')
        self.options.add_argument('--start-maximized')
        self.driver = None
        self.wait = None

    def login(self):
        """Login to LinkedIn"""
        try:
            print("Initializing Chrome driver...")
            self.driver = Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 20)  # Increased timeout
            
            print("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(random.uniform(2, 4))
            
            # Enter credentials
            print("Entering credentials...")
            email_field = self.wait.until(EC.presence_of_element_located((By.ID, 'username')))
            password_field = self.driver.find_element(By.ID, 'password')
            
            # Type like a human
            for char in os.getenv('LINKEDIN_EMAIL'):
                email_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            for char in os.getenv('LINKEDIN_PASSWORD'):
                password_field.send_keys(char)
                time.sleep(random.uniform(0.1, 0.3))
            
            # Click login button
            print("Clicking login button...")
            login_button = self.driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]')
            login_button.click()
            
            # Wait for login to complete
            time.sleep(random.uniform(3, 5))
            
            # Check if login was successful
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '.global-nav, .authentication-outlet')))
                print("Successfully logged in to LinkedIn")
                return True
            except TimeoutException:
                print("Failed to log in to LinkedIn")
                self.driver.save_screenshot('login_failed.png')
                return False
                
        except Exception as e:
            print(f"Error during login: {str(e)}")
            if self.driver:
                self.driver.save_screenshot('login_error.png')
            return False

    def wait_for_results(self):
        """Wait for search results with multiple possible selectors"""
        selectors = [
            'div.search-results-container',
            'div.scaffold-layout__list',
            'ul.reusable-search__entity-result-list',
            'div.search-results-container ul',
            'div.scaffold-layout__main div.pb2'
        ]
        
        for selector in selectors:
            try:
                element = self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                print(f"Found results container with selector: {selector}")
                # Print the HTML of the found element for debugging
                print(f"Container HTML: {element.get_attribute('innerHTML')[:200]}...")
                return True
            except TimeoutException:
                continue
        
        print("Could not find results with any known selector")
        return False

    def get_element_text(self, element, selectors):
        """Safely get text from an element with multiple possible selectors"""
        for selector in selectors.split(', '):
            try:
                el = element.find_element(By.CSS_SELECTOR, selector)
                text = el.text.strip()
                if text:
                    return text
            except (NoSuchElementException, StaleElementReferenceException):
                continue
        return ""

    def search_recruiters(self, job_title: str, location: str, max_results: int = 100) -> List[Dict]:
        """Search for recruiters based on job title and location"""
        try:
            if not self.driver:
                print("Starting new session...")
                if not self.login():
                    return []
            
            # Encode search parameters
            encoded_title = urllib.parse.quote(f"recruiter {job_title}")
            encoded_location = urllib.parse.quote(location)
            
            # Construct search URL with filters for recruiters
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_title}&location={encoded_location}&origin=FACETED_SEARCH&sid=LR3"
            print(f"Navigating to search URL: {search_url}")
            self.driver.get(search_url)
            time.sleep(random.uniform(3, 5))  # Increased wait time
            
            # Wait for search results page to load completely
            try:
                self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.search-results-container')))
                print("Search results page loaded")
                
                # Print page title and URL for debugging
                print(f"Current URL: {self.driver.current_url}")
                print(f"Page title: {self.driver.title}")
                
            except TimeoutException:
                print("Timeout waiting for search results page")
                self.driver.save_screenshot('search_page_timeout.png')
            
            # Save page source for debugging
            with open('search_page.html', 'w', encoding='utf-8') as f:
                f.write(self.driver.page_source)
            
            recruiters = []
            page = 1
            
            while len(recruiters) < max_results:
                try:
                    print(f"Processing page {page}...")
                    if not self.wait_for_results():
                        self.driver.save_screenshot(f'no_results_page_{page}.png')
                        break
                    
                    # Scroll slowly to load all results
                    for _ in range(3):
                        self.driver.execute_script("window.scrollBy(0, 300);")
                        time.sleep(1)
                    
                    # Try different selectors for result containers
                    selectors = [
                        'li.reusable-search__result-container',
                        'li.ember-view.artdeco-list__item',
                        'div.entity-result__item',
                        'ul.reusable-search__entity-result-list > li',
                        'div.search-results-container li.ember-view'
                    ]
                    
                    print("Looking for result containers...")
                    recruiter_cards = []
                    for selector in selectors:
                        cards = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if cards:
                            print(f"Found {len(cards)} results with selector: {selector}")
                            # Print first card HTML for debugging
                            if cards:
                                print(f"First card HTML: {cards[0].get_attribute('innerHTML')[:200]}...")
                            recruiter_cards = cards
                            break
                    
                    if not recruiter_cards:
                        print("No results found with any selector")
                        # Try to find any visible elements for debugging
                        visible_elements = self.driver.find_elements(By.CSS_SELECTOR, 'div, li, ul')
                        print(f"Found {len(visible_elements)} visible elements")
                        if visible_elements:
                            print(f"First visible element: {visible_elements[0].get_attribute('outerHTML')[:200]}...")
                        self.driver.save_screenshot(f'no_cards_page_{page}.png')
                        break
                    
                    for card in recruiter_cards:
                        try:
                            # Get name with multiple possible selectors
                            name_selectors = [
                                'div.entity-result__title-text span[aria-hidden="true"]',
                                'div.entity-result__title-text a span',
                                'div.linked-area span.entity-result__title-text',
                                'div.entity-result__title-line a span',
                                'a.app-aware-link span.visually-hidden'
                            ]
                            
                            name = None
                            for selector in name_selectors:
                                try:
                                    name_element = card.find_element(By.CSS_SELECTOR, selector)
                                    name = name_element.text.strip()
                                    if name:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            if not name:
                                print("Could not find name, skipping...")
                                continue
                            
                            # Get role and company with multiple selectors
                            role_selectors = [
                                'div.entity-result__primary-subtitle',
                                'div.entity-result__summary.entity-result__primary-subtitle',
                                'div.linked-area div.entity-result__primary-subtitle',
                                'div.linked-area span.entity-result__primary-subtitle'
                            ]
                            
                            company_selectors = [
                                'div.entity-result__secondary-subtitle',
                                'div.entity-result__summary.entity-result__secondary-subtitle',
                                'div.linked-area div.entity-result__secondary-subtitle',
                                'div.linked-area span.entity-result__secondary-subtitle'
                            ]
                            
                            role = None
                            company = None
                            
                            for selector in role_selectors:
                                try:
                                    role_element = card.find_element(By.CSS_SELECTOR, selector)
                                    role = role_element.text.strip()
                                    if role:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            for selector in company_selectors:
                                try:
                                    company_element = card.find_element(By.CSS_SELECTOR, selector)
                                    company = company_element.text.strip()
                                    if company:
                                        break
                                except NoSuchElementException:
                                    continue
                            
                            if not role or not company:
                                print(f"Missing role or company for {name}, skipping...")
                                continue
                            
                            # Get profile URL
                            try:
                                profile_url = card.find_element(By.CSS_SELECTOR, 'a.app-aware-link').get_attribute('href')
                            except NoSuchElementException:
                                try:
                                    profile_url = card.find_element(By.CSS_SELECTOR, '.entity-result__title-text a').get_attribute('href')
                                except NoSuchElementException:
                                    print(f"Could not find profile URL for {name}")
                                    continue
                            
                            print(f"Processing: {name} - {role} at {company}")
                            
                            # Only include if they are actually recruiters
                            if any(keyword in role.lower() for keyword in ['recruit', 'talent', 'hr', 'hiring', 'people', 'acquisition', 'sourcing']):
                                recruiter_data = {
                                    'name': name,
                                    'role': role,
                                    'company': company,
                                    'profile_url': profile_url,
                                    'status': 'pending',
                                    'created_at': time.time()
                                }
                                recruiters.append(recruiter_data)
                                print(f"Added recruiter: {name} - {role} at {company}")
                            
                            if len(recruiters) >= max_results:
                                break
                                
                        except Exception as e:
                            print(f"Error processing card: {str(e)}")
                            continue
                    
                    if len(recruiters) >= max_results:
                        break
                    
                    # Try to click next page if available
                    try:
                        next_button = self.driver.find_element(By.CSS_SELECTOR, 'button.artdeco-pagination__button--next:not([disabled])')
                        if next_button.get_attribute('disabled') or 'disabled' in next_button.get_attribute('class'):
                            print("Next button is disabled")
                            break
                        print("Clicking next page...")
                        next_button.click()
                        page += 1
                        time.sleep(random.uniform(3, 5))
                    except NoSuchElementException:
                        print("No more pages available")
                        break
                        
                except TimeoutException:
                    print(f"Timeout waiting for results on page {page}")
                    self.driver.save_screenshot(f'timeout_page_{page}.png')
                    break
            
            print(f"Found {len(recruiters)} recruiters in total")
            return recruiters
            
        except Exception as e:
            print(f"Error during recruiter search: {str(e)}")
            if self.driver:
                self.driver.save_screenshot('search_error.png')
            return []

    def close(self):
        """Close the browser"""
        if self.driver:
            print("Closing browser...")
            self.driver.quit() 