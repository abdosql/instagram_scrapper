import instaloader
import os
import time
from typing import List, Dict
import undetected_chromedriver as uc
import json
import csv
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import random

class InstagramScraper:
    def __init__(self):
        self.L = instaloader.Instaloader()
        self.driver = None
        self.login_username = None  # Add login_username property
        
    def get_cookies_from_browser(self, username: str) -> bool:
        """Get cookies from browser after manual login"""
        try:
            print("\nNo saved session found. Launching Chrome for Instagram login...")
            
            # Initialize undetected Chrome driver
            options = uc.ChromeOptions()
            options.add_argument("--start-maximized")
            self.driver = uc.Chrome(options=options)
            
            # Open Instagram login page
            self.driver.get('https://www.instagram.com/accounts/login/')
            print("\nPlease:")
            print("1. Log in to your account in the Chrome window")
            print("2. Complete the 2FA process if prompted")
            print("3. Press Enter here after you've successfully logged in...")
            input()
            
            # Get cookies
            cookies = self.driver.get_cookies()
            
            # Save cookies to file
            session_file = f"{username}_session.json"
            with open(session_file, 'w') as f:
                json.dump(cookies, f)
            
            print(f"Session saved for future use in {session_file}")
            
            # Load cookies into instaloader session
            self.load_session_from_cookies(username, session_file)
            return True
            
        except Exception as e:
            print(f"Error during browser automation: {e}")
            return False
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None
    
    def load_session_from_cookies(self, username: str, session_file: str) -> bool:
        """Load session from saved cookies"""
        try:
            with open(session_file, 'r') as f:
                cookies = json.load(f)
                
            # Convert cookies to instaloader format
            session_cookies = {}
            for cookie in cookies:
                session_cookies[cookie['name']] = cookie['value']
                
            # Set cookies in instaloader session
            self.L.context._session.cookies.update(session_cookies)
            return True
        except Exception as e:
            print(f"Error loading session: {e}")
            return False
    
    def apply_cookies_to_browser(self, session_file: str):
        """Apply saved cookies to browser session"""
        with open(session_file, 'r') as f:
            cookies = json.load(f)
        
        # First go to Instagram domain to set cookies
        self.driver.get('https://www.instagram.com')
        time.sleep(2)
        
        # Add cookies to browser
        for cookie in cookies:
            try:
                self.driver.add_cookie(cookie)
            except Exception as e:
                print(f"Error adding cookie: {e}")
                continue
        
        # Refresh page to apply cookies
        self.driver.refresh()
        time.sleep(3)
        
    def login(self, username: str) -> bool:
        """Login to Instagram account"""
        try:
            # Check for existing session
            session_file = f"{username}_session.json"
            
            if os.path.exists(session_file):
                print("Found existing session, attempting to load...")
                if self.load_session_from_cookies(username, session_file):
                    print("Session loaded successfully!")
                    return True
                else:
                    print("Failed to load session, need to login again...")
                    return self.get_cookies_from_browser(username)
            else:
                return self.get_cookies_from_browser(username)
                
        except Exception as e:
            print(f"Error during login: {e}")
            return False
    
    def scroll_to_bottom(self, dialog):
        """Automatically scroll the following dialog with random delays"""
        print("\nAutomatically scrolling through the following list...")
        
        # Wait for the modal to fully load
        time.sleep(2)
        
        # Initialize variables for tracking progress
        last_count = 0
        no_change_count = 0
        scroll_position = 0
        scroll_increment = 1000
        max_no_change_attempts = 5  # Number of attempts before concluding we've reached the end
        
        while True:
            # Get current loaded elements directly from the dialog
            elements = dialog.find_elements(By.CSS_SELECTOR, "a[role='link']")
            current_count = len(elements)
            print(f"\rCurrently loaded followers: {current_count}", end="", flush=True)
            
            if current_count == last_count:
                no_change_count += 1
                if no_change_count >= max_no_change_attempts:
                    print(f"\nNo new followers found after {max_no_change_attempts} attempts. Reached the end!")
                    break
                    
                # Try different scrolling techniques before giving up
                try:
                    # Method 1: Scroll to last element
                    if elements:
                        last_element = elements[-1]
                        self.driver.execute_script("arguments[0].scrollIntoView(true);", last_element)
                        time.sleep(1)
                    
                    # Method 2: Large jump scroll
                    scroll_position += scroll_increment * 2
                    self.driver.execute_script(
                        f"arguments[0].scrollTop = {scroll_position};", 
                        dialog
                    )
                    time.sleep(1)
                    
                    # Method 3: Random scroll position
                    random_scroll = random.randint(int(scroll_position * 0.8), int(scroll_position * 1.2))
                    self.driver.execute_script(
                        f"arguments[0].scrollTop = {random_scroll};", 
                        dialog
                    )
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"\nScroll error: {e}")
            else:
                # Reset counter if we found new followers
                no_change_count = 0
                print(f"\nFound {current_count - last_count} new followers!")
                
            # Normal scroll
            try:
                scroll_position += scroll_increment
                self.driver.execute_script(
                    f"arguments[0].scrollTop = {scroll_position};", 
                    dialog
                )
                
                # Random delay between scrolls
                time.sleep(random.uniform(0.5, 1))
                
                # Occasionally take a longer break
                if random.random() < 0.1:  # 10% chance
                    print("\nTaking a short break...")
                    time.sleep(random.uniform(1, 2))
                
            except Exception as e:
                print(f"\nError during scroll: {e}")
                continue
            
            # Update last count
            last_count = current_count
        
        # Final count
        final_elements = dialog.find_elements(By.CSS_SELECTOR, "a[role='link']")
        print(f"\nScrolling complete. Total followers loaded: {len(final_elements)}")

    def get_following_data(self, username: str, is_first_load: bool = False) -> List[Dict]:
        """Get following data including username and bio"""
        try:
            # Initialize Chrome if not already initialized
            if not self.driver:
                options = uc.ChromeOptions()
                options.add_argument("--start-maximized")
                self.driver = uc.Chrome(options=options)
                
                # Apply saved cookies to browser
                session_file = f"{self.login_username}_session.json"  # Use login username for session
                if os.path.exists(session_file):
                    print("Applying saved session to browser...")
                    self.apply_cookies_to_browser(session_file)
            
            # If this is first load, just verify login
            if is_first_load:
                print("Verifying login...")
                self.driver.get('https://www.instagram.com/')
                time.sleep(3)
                return []
            
            # Create timestamp for this scraping session
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            usernames_file = f"usernames_{timestamp}.txt"
            output_file = f"following_data_{timestamp}.csv"
            
            # Load target profile page
            print("Loading profile page...")
            self.driver.get(f'https://www.instagram.com/{username}/')
            time.sleep(random.uniform(2, 3))
            
            # Click the Following button
            print("Looking for Following button...")
            following_button = WebDriverWait(self.driver, 10).until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href$='/following/']"))
            )
            following_button.click()
            time.sleep(1)
            
            # Wait for the modal dialog
            print("Waiting for following modal to load...")
            dialog = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div[role='dialog']"))
            )
            print("Found modal with selector: div[role='dialog']")
            
            # Scroll the modal
            self.scroll_to_bottom(dialog)
            
            # Get all following elements
            following_elements = dialog.find_elements(By.CSS_SELECTOR, "a[role='link']")
            
            # Process and save usernames first
            usernames_to_scrape = []
            print("\nCollecting usernames...")
            
            for element in following_elements:
                try:
                    href = element.get_attribute('href')
                    if href and '/instagram.com/' not in href:
                        username = href.split('/')[-2]
                        if username and username not in usernames_to_scrape:
                            usernames_to_scrape.append(username)
                            print(f"Found username: {username}")
                except Exception as e:
                    continue
            
            print(f"\nFound {len(usernames_to_scrape)} usernames to scrape")
            
            # Save usernames to file
            with open(usernames_file, 'w', encoding='utf-8') as f:
                for username in usernames_to_scrape:
                    f.write(f"{username}\n")
            print(f"Usernames saved to: {usernames_file}")
            
            # Continue with bio scraping automatically
            print("\nStarting bio scraping...")
            
            # Open CSV file for writing bios
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['username', 'bio'])
                writer.writeheader()
                
                # Process each username for bio
                for username in usernames_to_scrape:
                    try:
                        print(f"\nVisiting profile of {username}...")
                        self.driver.get(f'https://www.instagram.com/{username}/')
                        time.sleep(random.uniform(1, 2))
                        
                        # Try to find bio with the exact selector
                        try:
                            bio_element = WebDriverWait(self.driver, 3).until(
                                EC.presence_of_element_located((By.CSS_SELECTOR, "span._ap3a._aaco._aacu._aacx._aad7._aade"))
                            )
                            bio = bio_element.text.strip()
                        except:
                            bio = ""
                        
                        # Write to CSV
                        writer.writerow({
                            'username': username,
                            'bio': bio
                        })
                        print(f"Scraped data for: {username}")
                        
                        # Random delay
                        time.sleep(random.uniform(1, 2))
                            
                    except Exception as e:
                        print(f"Error scraping account {username}: {e}")
                        continue
            
            print(f"\nData collection completed! Check {output_file} for results.")
            return []
            
        except Exception as e:
            print(f"Error getting following data: {e}")
            return []
        finally:
            if self.driver:
                self.driver.quit()
                self.driver = None

def main():
    scraper = InstagramScraper()
    
    # Get login credentials
    login_username = input("Enter your Instagram username to login: ")
    scraper.login_username = login_username  # Store login username
    
    # Login using session
    if scraper.login(login_username):
        # First verify login by loading Instagram
        scraper.get_following_data("", is_first_load=True)
        
        # Now ask for target account
        target_username = input("Enter the username of the account you want to scrape followers from: ")
        # Get following data
        scraper.get_following_data(target_username)

if __name__ == "__main__":
    main() 