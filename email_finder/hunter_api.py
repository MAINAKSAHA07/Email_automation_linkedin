import os
import requests
from typing import Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class HunterAPI:
    def __init__(self):
        self.api_key = os.getenv('HUNTER_API_KEY')
        self.base_url = 'https://api.hunter.io/v2'
        self.headers = {
            'Authorization': f'Bearer {self.api_key}',
            'Content-Type': 'application/json'
        }

    def find_email(self, first_name: str, last_name: str, domain: str) -> Optional[Dict]:
        """Find email using Hunter.io API"""
        endpoint = f'{self.base_url}/email-finder'
        params = {
            'first_name': first_name,
            'last_name': last_name,
            'domain': domain
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get('data', {}).get('email'):
                return {
                    'email': data['data']['email'],
                    'score': data['data'].get('score', 0),
                    'sources': data['data'].get('sources', []),
                    'status': 'verified'
                }
            return None
            
        except requests.exceptions.RequestException as e:
            print(f"Error finding email: {e}")
            return None

    def verify_email(self, email: str) -> Dict:
        """Verify email using Hunter.io API"""
        endpoint = f'{self.base_url}/email-verifier'
        params = {'email': email}
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                'email': email,
                'status': data['data']['status'],
                'score': data['data'].get('score', 0),
                'result': data['data'].get('result', 'unknown')
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error verifying email: {e}")
            return {
                'email': email,
                'status': 'error',
                'score': 0,
                'result': 'error'
            }

    def get_domain_search(self, domain: str, limit: int = 100) -> Dict:
        """Get all emails for a domain"""
        endpoint = f'{self.base_url}/domain-search'
        params = {
            'domain': domain,
            'limit': limit
        }
        
        try:
            response = requests.get(endpoint, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            return {
                'domain': domain,
                'emails': data.get('data', {}).get('emails', []),
                'pattern': data.get('data', {}).get('pattern', ''),
                'organization': data.get('data', {}).get('organization', '')
            }
            
        except requests.exceptions.RequestException as e:
            print(f"Error getting domain search: {e}")
            return {
                'domain': domain,
                'emails': [],
                'pattern': '',
                'organization': ''
            } 