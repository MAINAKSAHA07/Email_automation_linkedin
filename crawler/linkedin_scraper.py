import time
import random
import os
import urllib.parse
import re
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from undetected_chromedriver import Chrome, ChromeOptions
from dotenv import load_dotenv
import json

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
        
        # Add user agent to appear more like a regular browser
        self.options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36')
        
        self.driver = None
        self.wait = None
        self.debug_mode = True  # Set to True to enable additional debugging

    def login(self):
        """Login to LinkedIn with enhanced error handling and debugging"""
        try:
            print("Initializing Chrome driver...")
            self.driver = Chrome(options=self.options)
            self.wait = WebDriverWait(self.driver, 30)  # Extended timeout
            
            print("Navigating to LinkedIn login page...")
            self.driver.get('https://www.linkedin.com/login')
            time.sleep(random.uniform(3, 5))
            
            # Take screenshot of login page
            if self.debug_mode:
                self.driver.save_screenshot('login_page.png')
                print(f"Current URL: {self.driver.current_url}")
            
            # Enter credentials with more human-like typing
            print("Entering credentials...")
            try:
                email_field = self.wait.until(EC.element_to_be_clickable((By.ID, 'username')))
                password_field = self.wait.until(EC.element_to_be_clickable((By.ID, 'password')))
            except TimeoutException:
                print("Could not find username/password fields. Checking alternative selectors...")
                try:
                    email_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="session_key"]')))
                    password_field = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input[name="session_password"]')))
                except TimeoutException:
                    print("Still cannot find login fields. Saving page source...")
                    with open('login_page_source.html', 'w', encoding='utf-8') as f:
                        f.write(self.driver.page_source)
                    self.driver.save_screenshot('login_fields_not_found.png')
                    return False
            
            # Clear fields first
            email_field.clear()
            password_field.clear()
            
            # Type like a human with variable speed
            for char in os.getenv('LINKEDIN_EMAIL'):
                email_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.25))
            
            # Slight pause between fields
            time.sleep(random.uniform(0.5, 1.5))
            
            for char in os.getenv('LINKEDIN_PASSWORD'):
                password_field.send_keys(char)
                time.sleep(random.uniform(0.05, 0.25))
            
            # Click login button
            print("Clicking login button...")
            try:
                login_button = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[type="submit"]')))
                # Add a small delay before clicking
                time.sleep(random.uniform(0.5, 1.5))
                login_button.click()
            except TimeoutException:
                print("Could not find login button. Trying to press Enter instead...")
                password_field.send_keys(Keys.RETURN)
            
            # Wait for login to complete with improved detection
            time.sleep(random.uniform(5, 8))
            
            # Take screenshot after login attempt
            if self.debug_mode:
                self.driver.save_screenshot('after_login_attempt.png')
                print(f"Current URL after login attempt: {self.driver.current_url}")
            
            # Check if login was successful with multiple indicators
            success_selectors = [
                '.global-nav',
                '.authentication-outlet',
                '.feed-identity-module',
                'input[placeholder="Search"]',
                '.search-global-typeahead'
            ]
            
            login_successful = False
            for selector in success_selectors:
                try:
                    self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
                    login_successful = True
                    print(f"Login confirmed with selector: {selector}")
                    break
                except TimeoutException:
                    continue
            
            if login_successful:
                print("Successfully logged in to LinkedIn")
                # Take a screenshot of the logged-in home page
                self.driver.save_screenshot('logged_in_home.png')
                return True
            else:
                print("Failed to confirm login to LinkedIn")
                self.driver.save_screenshot('login_failed.png')
                
                # Check for security verification
                if "checkpoint" in self.driver.current_url or "security-verification" in self.driver.current_url:
                    print("Security verification detected. Manual intervention required.")
                    
                # Save the page source for debugging
                with open('login_failed_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
                
                return False
                
        except Exception as e:
            print(f"Error during login: {str(e)}")
            if self.driver:
                self.driver.save_screenshot('login_error.png')
            return False

    def search_recruiters(self, job_title: str, location: str, max_results: int = 100) -> List[Dict]:
        """Search for recruiters based on job title and location with enhanced parsing"""
        try:
            if not self.driver:
                print("Starting new session...")
                if not self.login():
                    return []

            # Try direct navigation to search results
            self._perform_search(job_title, location)
            
            # Wait for page to fully load
            time.sleep(random.uniform(5, 8))
            
            # Debug the current state
            if self.debug_mode:
                print(f"Current URL after search: {self.driver.current_url}")
                self.driver.save_screenshot('search_results_initial.png')
                
                # Save page source for analysis
                with open('search_page_source.html', 'w', encoding='utf-8') as f:
                    f.write(self.driver.page_source)
            
            recruiters = []
            page = 1
            max_pages = 10  # Limit to 10 pages in case of issues

            while len(recruiters) < max_results and page <= max_pages:
                try:
                    print(f"Processing page {page}...")
                    
                    # Scroll slowly through the page to load all content
                    self._scroll_page()
                    
                    # Take screenshot after scrolling
                    if self.debug_mode:
                        self.driver.save_screenshot(f'search_results_page_{page}_scrolled.png')
                    
                    # Extract data using different methods
                    page_recruiters = self._extract_recruiters_from_page()
                    
                    if page_recruiters:
                        print(f"Found {len(page_recruiters)} recruiters on page {page}")
                        recruiters.extend(page_recruiters)
                        
                        # Print some examples for verification
                        for i, recruiter in enumerate(page_recruiters[:3]):
                            print(f"Example {i+1}: {recruiter['name']} - {recruiter['role']} at {recruiter['company']}")
                    else:
                        print(f"No recruiters found on page {page}. Checking alternative extraction methods...")
                        # Try alternative extraction as a fallback
                        alt_recruiters = self._extract_recruiters_alternative()
                        if alt_recruiters:
                            print(f"Found {len(alt_recruiters)} recruiters using alternative method")
                            recruiters.extend(alt_recruiters)
                        else:
                            print("No results with alternative method either, breaking search.")
                            break
                    
                    if len(recruiters) >= max_results:
                        print(f"Reached maximum results limit ({max_results})")
                        break
                    
                    # Try to navigate to next page
                    if not self._go_to_next_page():
                        print("Could not navigate to next page. Ending pagination.")
                        break
                    
                    page += 1
                    time.sleep(random.uniform(4, 7))  # Wait between page navigations
                
                except Exception as e:
                    print(f"Error processing page {page}: {str(e)}")
                    self.driver.save_screenshot(f'error_page_{page}.png')
                    break
            
            # Filter out duplicates and only keep recruiters
            unique_recruiters = self._filter_unique_recruiters(recruiters)
            print(f"Found {len(unique_recruiters)} unique recruiters in total.")
            
            # Save results to JSON file for reference
            with open('scraped_recruiters.json', 'w') as f:
                json.dump(unique_recruiters, f, indent=2)
                
            return unique_recruiters

        except Exception as e:
            print(f"Error during recruiter search: {str(e)}")
            if self.driver:
                self.driver.save_screenshot('search_error.png')
            return []
    
    def _perform_search(self, job_title: str, location: str):
        """Perform search using LinkedIn's search functionality"""
        try:
            # Try direct navigation first
            encoded_title = urllib.parse.quote(f"recruiter {job_title}")
            encoded_location = urllib.parse.quote(location)
            search_url = f"https://www.linkedin.com/search/results/people/?keywords={encoded_title}&location={encoded_location}&origin=GLOBAL_SEARCH_HEADER"
            
            print(f"Navigating to search URL: {search_url}")
            self.driver.get(search_url)
            time.sleep(random.uniform(4, 6))
            
            # If direct navigation doesn't work well, try using the search box
            if "keywords" not in self.driver.current_url:
                print("Direct URL navigation might not have worked, trying search box...")
                try:
                    # Find search box
                    search_box = self.wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'input.search-global-typeahead__input')))
                    search_box.clear()
                    
                    # Type search query
                    search_query = f"recruiter {job_title} {location}"
                    for char in search_query:
                        search_box.send_keys(char)
                        time.sleep(random.uniform(0.05, 0.15))
                    
                    # Submit search
                    time.sleep(random.uniform(0.5, 1))
                    search_box.send_keys(Keys.RETURN)
                    time.sleep(random.uniform(3, 5))
                    
                    # Click on People filter if available
                    try:
                        people_filter = self.wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(., 'People')]")))
                        people_filter.click()
                        time.sleep(random.uniform(2, 4))
                    except:
                        print("People filter not found or not needed")
                except:
                    print("Could not use search box, continuing with direct URL results")
        except Exception as e:
            print(f"Error during search: {str(e)}")
    
    def _scroll_page(self):
        """Scroll through the page gradually to load all content"""
        try:
            # Get initial page height
            last_height = self.driver.execute_script("return document.body.scrollHeight")
            
            # Scroll down in smaller increments
            for i in range(10):  # More granular scrolling
                # Scroll down in smaller steps
                scroll_amount = random.randint(300, 700)
                self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
                
                # Add random pauses between scrolls
                time.sleep(random.uniform(0.7, 1.5))
                
                # Sometimes jiggle the scroll slightly to seem more human
                if random.random() > 0.7:
                    self.driver.execute_script(f"window.scrollBy(0, {random.randint(-100, 100)});")
                    time.sleep(random.uniform(0.3, 0.7))
            
            # Final scroll to bottom
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(random.uniform(2, 3))
            
            # Check if we've scrolled all the way down
            new_height = self.driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print("Reached bottom of page")
            else:
                print("Page was extended during scrolling")
        
        except Exception as e:
            print(f"Error during page scrolling: {str(e)}")
    
    def _extract_recruiters_from_page(self):
        """Extract recruiter information using multiple approaches"""
        recruiters = []
        
        # Wait for the search results to load
        try:
            # First wait for the main container
            self.wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div.search-results-container')))
            # Then wait for the loading animation to disappear
            self.wait.until_not(EC.presence_of_element_located((By.CSS_SELECTOR, '.artdeco-loader')))
            # Give a moment for everything to settle
            time.sleep(2)
        except TimeoutException:
            print("Timeout waiting for search results to load")
            return []

        # Try several different selectors for the recruiter cards
        possible_card_selectors = [
            '.reusable-search__result-container',
            '.search-results-container .reusable-search__result-container',
            '.search-results-container .ember-view.reusable-search__result-container',
            '.scaffold-layout__list .reusable-search__result-container',
            '.search-results__list .ember-view'
        ]
        
        for selector in possible_card_selectors:
            try:
                # Wait for elements with a shorter timeout
                cards = WebDriverWait(self.driver, 5).until(
                    EC.presence_of_all_elements_located((By.CSS_SELECTOR, selector))
                )
                
                if cards:
                    print(f"Found {len(cards)} cards with selector: {selector}")
                    
                    # Process each card
                    for card in cards:
                        try:
                            # Print the HTML of the first few cards for debugging
                            if len(recruiters) < 3:
                                print(f"Card {len(recruiters) + 1} HTML: {card.get_attribute('outerHTML')[:200]}")
                            
                            recruiter_data = self._extract_data_from_card(card)
                            if recruiter_data:
                                recruiters.append(recruiter_data)
                        except Exception as e:
                            print(f"Error extracting data from card: {str(e)}")
                            continue
                    
                    # If we found any recruiters, break the loop
                    if recruiters:
                        break
            except Exception as e:
                print(f"Error with selector {selector}: {str(e)}")
                continue
        
        return recruiters
    
    def _extract_data_from_card(self, card):
        """Extract recruiter data from a single card element"""
        try:
            # Extract name
            name_selectors = [
                '.entity-result__title-text a span[aria-hidden="true"]',
                '.entity-result__title-text a span',
                '.app-aware-link span[aria-hidden="true"]',
                '.entity-result__title-line a span'
            ]
            
            name = None
            for selector in name_selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    name = element.text.strip()
                    if name:
                        break
                except:
                    continue
            
            if not name:
                return None
            
            # Extract role
            role_selectors = [
                '.entity-result__primary-subtitle',
                '.entity-result__summary.entity-result__primary-subtitle',
                '.primary-subtitle'
            ]
            
            role = None
            for selector in role_selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    role = element.text.strip()
                    if role:
                        break
                except:
                    continue
            
            if not role:
                role = "Unknown Role"
            
            # Extract company
            company_selectors = [
                '.entity-result__secondary-subtitle',
                '.entity-result__summary.entity-result__secondary-subtitle',
                '.secondary-subtitle'
            ]
            
            company = None
            for selector in company_selectors:
                try:
                    element = card.find_element(By.CSS_SELECTOR, selector)
                    company = element.text.strip()
                    if company:
                        break
                except:
                    continue
            
            if not company:
                company = "Unknown Company"
            
            # Extract profile URL
            profile_url = None
            try:
                link_element = card.find_element(By.CSS_SELECTOR, '.app-aware-link')
                profile_url = link_element.get_attribute('href')
                if profile_url:
                    # Clean up the URL
                    profile_url = profile_url.split('?')[0]
            except:
                pass
            
            if not profile_url:
                return None
            
            # Check if this is a recruiter
            recruiter_keywords = ['recruit', 'talent', 'hr', 'hiring', 'people', 'acquisition', 'sourcing']
            if any(keyword in role.lower() for keyword in recruiter_keywords):
                return {
                    'name': name,
                    'role': role,
                    'company': company,
                    'profile_url': profile_url,
                    'status': 'pending',
                    'created_at': time.time()
                }
            
            return None
            
        except Exception as e:
            print(f"Error extracting data from card: {str(e)}")
            return None
    
    def _extract_recruiters_alternative(self):
        """Alternative method to extract recruiters when primary method fails"""
        recruiters = []
        
        try:
            # Use JavaScript to extract data directly
            script = """
            const results = [];
            // Try to find all profile cards on the page
            const cards = document.querySelectorAll('li.reusable-search__result-container, div.entity-result, li.artdeco-list__item');
            
            cards.forEach(card => {
                try {
                    // Try multiple ways to get the name
                    let name = '';
                    const nameElements = card.querySelectorAll('span.entity-result__title-text a span, a.app-aware-link span, .entity-result__title-line a span');
                    for (let el of nameElements) {
                        if (el.textContent && el.textContent.trim()) {
                            name = el.textContent.trim();
                            break;
                        }
                    }
                    
                    // Try to get role
                    let role = '';
                    const roleElements = card.querySelectorAll('div.entity-result__primary-subtitle, p.entity-result__summary, p.subline-level-1');
                    for (let el of roleElements) {
                        if (el.textContent && el.textContent.trim()) {
                            role = el.textContent.trim();
                            break;
                        }
                    }
                    
                    // Try to get company
                    let company = '';
                    const companyElements = card.querySelectorAll('div.entity-result__secondary-subtitle, p.subline-level-2');
                    for (let el of companyElements) {
                        if (el.textContent && el.textContent.trim()) {
                            company = el.textContent.trim();
                            break;
                        }
                    }
                    
                    // Try to get profile URL
                    let profileUrl = '';
                    const links = card.querySelectorAll('a.app-aware-link');
                    for (let link of links) {
                        if (link.href && link.href.includes('/in/')) {
                            profileUrl = link.href.split('?')[0];
                            break;
                        }
                    }
                    
                    if (name && (role || company)) {
                        results.push({
                            name: name,
                            role: role || 'Unknown Role',
                            company: company || 'Unknown Company',
                            profileUrl: profileUrl || 'Unknown'
                        });
                    }
                } catch (e) {
                    console.error('Error processing card:', e);
                }
            });
            
            return results;
            """
            
            # Execute script and get results
            js_results = self.driver.execute_script(script)
            
            if js_results:
                print(f"JavaScript extraction found {len(js_results)} potential profiles")
                
                # Convert to our format and filter for recruiters
                for result in js_results:
                    recruiter_keywords = [
                        'recruit', 'talent', 'hr', 'hiring', 'people', 'acquisition', 
                        'sourcing', 'staffing', 'personnel', 'human resources'
                    ]
                    
                    role = result.get('role', '')
                    company = result.get('company', '')
                    
                    if any(keyword in (role + " " + company).lower() for keyword in recruiter_keywords):
                        recruiters.append({
                            'name': result.get('name', 'Unknown'),
                            'role': role if role else 'Unknown Role',
                            'company': company if company else 'Unknown Company',
                            'profile_url': result.get('profileUrl', 'Unknown'),
                            'status': 'pending',
                            'created_at': time.time()
                        })
        
        except Exception as e:
            print(f"Error during alternative extraction: {str(e)}")
        
        return recruiters
        
    def _go_to_next_page(self):
        """Navigate to the next page of search results"""
        try:
            # Try multiple selectors for the next button
            next_selectors = [
                'button.artdeco-pagination__button--next',
                'li.artdeco-pagination__indicator--number.active + li a',
                'a[aria-label="Next"]',
                'button[aria-label="Next"]'
            ]
            
            for selector in next_selectors:
                try:
                    next_buttons = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    for button in next_buttons:
                        if button.is_displayed() and button.is_enabled():
                            print(f"Found next button with selector: {selector}")
                            
                            # Scroll to button
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", button)
                            time.sleep(random.uniform(0.5, 1.5))
                            
                            # Click the button
                            button.click()
                            print("Clicked next page button")
                            
                            # Wait for page to load
                            time.sleep(random.uniform(3, 5))
                            
                            # Take screenshot after navigation
                            if self.debug_mode:
                                self.driver.save_screenshot('after_next_page_click.png')
                            
                            # Check if URL changed
                            if "page=" in self.driver.current_url:
                                print(f"Successfully navigated to next page: {self.driver.current_url}")
                                return True
                            else:
                                # Try to verify we're on a new page another way
                                return True
                except Exception as e:
                    print(f"Error with next button selector {selector}: {str(e)}")
            
            print("Could not find a working next button")
            return False
            
        except Exception as e:
            print(f"Error navigating to next page: {str(e)}")
            return False
    
    def _extract_element_text(self, parent_element, selectors):
        """Extract text using multiple possible selectors with improved reliability"""
        for selector in selectors:
            try:
                elements = parent_element.find_elements(By.CSS_SELECTOR, selector)
                for element in elements:
                    try:
                        # Try getting text attribute first
                        text = element.text.strip()
                        if text:
                            return text
                        
                        # If text attribute is empty, try getting attribute content
                        text = element.get_attribute('textContent').strip()
                        if text:
                            return text
                        
                        # Try innerHTML as last resort
                        text = element.get_attribute('innerHTML').strip()
                        if text and not text.startswith('<'):
                            return text
                    except:
                        continue
            except Exception:
                continue
        return ""
    
    def _filter_unique_recruiters(self, recruiters):
        """Filter out duplicate recruiters based on profile URL or name+company"""
        unique_recruiters = []
        seen_urls = set()
        seen_name_company = set()
        
        for recruiter in recruiters:
            profile_url = recruiter.get('profile_url', '').strip()
            name = recruiter.get('name', '').strip()
            company = recruiter.get('company', '').strip()
            
            # Create a unique identifier
            unique_id = f"{name}|{company}"
            
            # Skip if we've seen this URL or name+company before
            if (profile_url and profile_url != 'Unknown' and profile_url in seen_urls) or \
               (name and company and unique_id in seen_name_company):
                continue
            
            # Add to our unique sets
            if profile_url and profile_url != 'Unknown':
                seen_urls.add(profile_url)
            if name and company:
                seen_name_company.add(unique_id)
            
            unique_recruiters.append(recruiter)
        
        return unique_recruiters

    def close(self):
        """Close the browser"""
        if self.driver:
            print("Closing browser...")
            self.driver.quit() 

# Example usage
if __name__ == "__main__":
    scraper = LinkedInScraper()
    recruiters = scraper.search_recruiters(job_title="Data Analyst", location="United States")
    
    # Print results
    print("\nResults Summary:")
    print(f"Total recruiters found: {len(recruiters)}")
    for i, recruiter in enumerate(recruiters[:10], 1):  # Print first 10 as a sample
        print(f"{i}. {recruiter['name']} - {recruiter['role']} at {recruiter['company']}")
    
    # Save results to a file
    with open('linkedin_recruiters.json', 'w', encoding='utf-8') as f:
        json.dump(recruiters, f, indent=2)
    
    print(f"Saved {len(recruiters)} recruiters to linkedin_recruiters.json")
    
    scraper.close()