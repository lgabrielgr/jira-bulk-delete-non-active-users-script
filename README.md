# JIRA Non-Active User Management Script

This script helps JIRA administrators manage non-active (suspended or inactive) users by fetching them in bulk and providing options to review and delete them.

## Features

- Connects to JIRA Cloud using email and API token
- Fetches all users and filters non-active ones
- Saves non-active users to a JSON file for review
- Opens the file automatically for manual review
- Provides confirmation prompts before deletion
- Batch deletion of selected users
- Progress tracking and error handling

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Configure your JIRA domain in `.env`:
   ```
   JIRA_DOMAIN=your-jira-domain      # Required
   JIRA_EMAIL=your-email@domain.com  # Optional
   JIRA_API_TOKEN=your-api-token     # Optional
   ```

3. Run the script:
   ```bash
   python jira_user_manager.py
   ```

## Usage

The script will prompt you for:
- JIRA email (if not in .env)
- JIRA API token (if not in .env)

Then provides a menu with options to:
1. Fetch and save non-active users
2. Review the saved users file
3. Delete users from the saved file
4. Exit

## Safety Features

- Multiple confirmation prompts before deletion
- Detailed user list preview before deletion
- Error handling and status reporting
- Non-destructive file operations
- Connection testing before operations

## JIRA API Token

To create an API token:
1. Go to https://id.atlassian.com/manage-profile/security/api-tokens
2. Click "Create API token"
3. Give it a name and copy the token

## File Output

Non-active users are saved to `non_active_users.json` with fields:
- accountId
- displayName
- emailAddress
- active status
- accountType
- and other user metadata

## Testing

Run unit tests:



## Disclaimer

This script was tested against Atlassian Jira Cloud REST API v3 as of 2025-12-26.
