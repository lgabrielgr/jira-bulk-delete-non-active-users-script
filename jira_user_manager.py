#!/usr/bin/env python3
"""
JIRA Non-Active User Management Script
Fetches, reviews, and deletes suspended or inactive users in JIRA.
"""

import os
import sys
import json
import requests
import subprocess
from typing import List, Dict, Any
from dotenv import load_dotenv
import getpass

class JiraUserManager:
    def __init__(self):
        load_dotenv()
        self.domain = os.getenv('JIRA_DOMAIN')
        self.email = None
        self.api_token = None
        self.base_url = None
        self.session = requests.Session()
        
    def setup_credentials(self):
        """Get credentials from user input"""
        print("JIRA User Management Tool")
        print("=" * 40)
        
        # Get email
        stored_email = os.getenv('JIRA_EMAIL')
        if stored_email:
            use_stored = input(f"Use stored email ({stored_email})? [Y/n]: ").strip().lower()
            if use_stored in ('', 'y', 'yes'):
                self.email = stored_email
        
        if not self.email:
            self.email = input("Enter your JIRA email: ").strip()
        
        # Get API token
        stored_token = os.getenv('JIRA_API_TOKEN')
        if stored_token:
            use_stored = input("Use stored API token? [Y/n]: ").strip().lower()
            if use_stored in ('', 'y', 'yes'):
                self.api_token = stored_token
        
        if not self.api_token:
            self.api_token = getpass.getpass("Enter your JIRA API token: ")
        
        # Setup base URL and session
        self.base_url = f"https://{self.domain}.atlassian.net"
        self.session.auth = (self.email, self.api_token)
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        })
        
        print(f"Connecting to: {self.base_url}")
    
    def test_connection(self) -> bool:
        """Test JIRA connection"""
        try:
            response = self.session.get(f"{self.base_url}/rest/api/3/myself")
            if response.status_code == 200:
                user_info = response.json()
                print(f"✓ Connected successfully as: {user_info.get('displayName', self.email)}")
                return True
            else:
                print(f"✗ Connection failed: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            print(f"✗ Connection error: {e}")
            return False
    
    def fetch_non_active_users(self) -> List[Dict[str, Any]]:
        """Fetch only inactive users from JIRA (excluding deleted users)"""
        non_active_users = []
        
        print("Fetching inactive users from JIRA...")
        
        try:
            start_at = 0
            max_results = 50
            
            while True:
                # Use the correct API endpoint to get all users (active, inactive, deleted)
                response = self.session.get(
                    f"{self.base_url}/rest/api/3/users",
                    params={
                        'startAt': start_at,
                        'maxResults': max_results
                    }
                )
                
                if response.status_code != 200:
                    print(f"Error fetching users: {response.status_code} - {response.text}")
                    break
                
                users = response.json()
                if not users:
                    break
                
                # Filter to only include inactive users (not deleted)
                for user in users:
                    # Check if user is inactive but not deleted
                    # accountType 'former' indicates deleted users, so we exclude those
                    is_inactive = (
                        not user.get('active', True) and 
                        user.get('accountType') != 'former'
                    )
                    
                    if is_inactive:
                        non_active_users.append({
                            'accountId': user.get('accountId'),
                            'displayName': user.get('displayName'),
                            'emailAddress': user.get('emailAddress'),
                            'active': user.get('active'),
                            'accountType': user.get('accountType'),
                        })
                
                start_at += max_results
                print(f"Processed {start_at} users, found {len(non_active_users)} inactive users so far...")
                
                # Break if we got fewer results than requested (end of data)
                if len(users) < max_results:
                    break
                
        except requests.exceptions.RequestException as e:
            print(f"Error fetching users: {e}")
        
        print(f"Found {len(non_active_users)} inactive users (excluding deleted accounts)")
        return non_active_users
    
    def save_users_to_file(self, users: List[Dict[str, Any]], filename: str = 'non_active_users.json'):
        """Save users to JSON file"""
        with open(filename, 'w') as f:
            json.dump(users, f, indent=2)
        print(f"✓ Saved {len(users)} non-active users to {filename}")
    
    def open_file_for_review(self, filename: str):
        """Open the JSON file for review"""
        try:
            if sys.platform == "darwin":  # macOS
                subprocess.run(['open -a TextEdit', filename])
            elif sys.platform == "linux":  # Linux
                subprocess.run(['xdg-open', filename])
            elif sys.platform == "win32":  # Windows
                subprocess.run(['start', filename], shell=True)
            else:
                print(f"Please manually review the file: {filename}")
        except Exception as e:
            print(f"Could not automatically open file: {e}")
            print(f"Please manually review the file: {filename}")
    
    def delete_user(self, account_id: str, display_name: str) -> bool:
        """Delete a single user"""
        try:
            response = self.session.delete(
                f"{self.base_url}/rest/api/3/user",
                params={'accountId': account_id}
            )

            if response.status_code == 204:
                print(f"✓ Deleted: {display_name}")
                return True
            else:
                print(f"✗ Failed to delete {display_name}: {response.status_code} - {response.text}")
                return False

        except requests.exceptions.RequestException as e:
            print(f"✗ Error deleting {display_name}: {e}")
            return False
    
    def delete_users_from_file(self, filename: str = 'non_active_users.json'):
        """Delete users from the JSON file"""
        try:
            with open(filename, 'r') as f:
                users = json.load(f)
        except FileNotFoundError:
            print(f"File {filename} not found!")
            return
        
        print(f"\nFound {len(users)} users to delete.")
        print("\nUsers to be deleted:")
        print("-" * 60)
        
        for i, user in enumerate(users[:10], 1):  # Show first 10
            print(f"{i:2d}. {user.get('displayName', 'Unknown')} ({user.get('emailAddress', 'No email')})")
        
        if len(users) > 10:
            print(f"... and {len(users) - 10} more users")
        
        print("\n⚠️  WARNING: This will permanently delete all these users from JIRA!")
        print("This action cannot be undone.")
        
        confirm = input("\nType 'DELETE' to confirm deletion: ").strip()
        
        if confirm != 'DELETE':
            print("Deletion cancelled.")
            return
        
        # Final confirmation
        final_confirm = input(f"Are you absolutely sure you want to delete {len(users)} users? [y/N]: ").strip().lower()
        if final_confirm != 'y':
            print("Deletion cancelled.")
            return
        
        # Proceed with deletion
        print("\nStarting deletion process...")
        successful_deletions = 0
        failed_deletions = 0
        
        for user in users:
            account_id = user.get('accountId')
            display_name = user.get('displayName', 'Unknown')
            
            if not account_id:
                print(f"✗ Skipping {display_name}: No account ID")
                failed_deletions += 1
                continue
            
            if self.delete_user(account_id, display_name):
                successful_deletions += 1
            else:
                failed_deletions += 1
        
        print(f"\nDeletion Summary:")
        print(f"✓ Successfully deleted: {successful_deletions}")
        print(f"✗ Failed to delete: {failed_deletions}")
        print(f"Total processed: {len(users)}")

def main():
    manager = JiraUserManager()
    
    # Setup credentials
    manager.setup_credentials()
    
    # Test connection
    if not manager.test_connection():
        print("Please check your credentials and try again.")
        return
    
    # Menu
    while True:
        print("\n" + "=" * 50)
        print("JIRA User Management Options:")
        print("1. Fetch non-active users")
        print("2. Review saved users file")
        print("3. Delete users from saved file")
        print("4. Exit")
        print("=" * 50)
        
        choice = input("Select an option (1-4): ").strip()
        
        if choice == '1':
            # Remove existing file if it exists
            filename = 'non_active_users.json'
            if os.path.exists(filename):
                try:
                    os.remove(filename)
                    print(f"✓ Removed existing {filename}")
                except Exception as e:
                    print(f"Warning: Could not remove existing file: {e}")
            
            # Fetch only non-active users
            non_active_users = manager.fetch_non_active_users()
            
            if non_active_users:
                # Save to file
                manager.save_users_to_file(non_active_users)
                
                # Offer to open file for review
                open_file = input("Open file for review? [Y/n]: ").strip().lower()
                if open_file in ('', 'y', 'yes'):
                    manager.open_file_for_review('non_active_users.json')
            else:
                print("No non-active users found.")
        
        elif choice == '2':
            manager.open_file_for_review('non_active_users.json')
            
        elif choice == '3':
            manager.delete_users_from_file()
            
        elif choice == '4':
            print("Goodbye!")
            break
            
        else:
            print("Invalid choice. Please try again.")

if __name__ == "__main__":
    main()
