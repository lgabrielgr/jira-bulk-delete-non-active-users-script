import os
import json
import unittest
from unittest.mock import patch, MagicMock

from jira_user_manager import JiraUserManager

class TestJiraUserManager(unittest.TestCase):
    def setUp(self):
        os.environ['JIRA_DOMAIN'] = 'example'
        os.environ.pop('JIRA_EMAIL', None)
        os.environ.pop('JIRA_API_TOKEN', None)

    @patch('jira_user_manager.getpass.getpass', return_value='token123')
    @patch('builtins.input')
    def test_setup_credentials_uses_inputs(self, mock_input, mock_getpass):
        mock_input.side_effect = ["user@example.com"]
        mgr = JiraUserManager()
        mgr.setup_credentials()
        self.assertEqual(mgr.email, 'user@example.com')
        self.assertEqual(mgr.api_token, 'token123')
        self.assertTrue(mgr.base_url.endswith('.atlassian.net'))
        self.assertIsNotNone(mgr.session.auth)

    def test_fetch_non_active_users_filters_correctly(self):
        mgr = JiraUserManager()
        mgr.email = 'user@example.com'
        mgr.api_token = 'token123'
        mgr.domain = 'example'
        mgr.base_url = f"https://{mgr.domain}.atlassian.net"
        mgr.session = MagicMock()

        users_page_1 = [
            {'accountId': '1', 'displayName': 'Active User', 'emailAddress': 'a@ex.com', 'active': True, 'accountType': 'atlassian'},
            {'accountId': '2', 'displayName': 'Inactive User', 'emailAddress': 'i@ex.com', 'active': False, 'accountType': 'atlassian'},
            {'accountId': '3', 'displayName': 'Former User', 'emailAddress': 'f@ex.com', 'active': False, 'accountType': 'former'},
        ]
        users_page_2 = []

        def get_side_effect(url, params=None):
            class Resp:
                def __init__(self, data):
                    self.status_code = 200
                    self._data = data
                def json(self):
                    return self._data
            if params and params.get('startAt') == 0:
                return Resp(users_page_1)
            else:
                return Resp(users_page_2)

        mgr.session.get.side_effect = get_side_effect
        non_active = mgr.fetch_non_active_users()
        self.assertEqual(len(non_active), 1)
        self.assertEqual(non_active[0]['accountId'], '2')

    def test_delete_user_success_and_failure(self):
        mgr = JiraUserManager()
        mgr.base_url = 'https://example.atlassian.net'
        mgr.session = MagicMock()

        class Resp204:
            status_code = 204
            text = ''
        class Resp400:
            status_code = 400
            text = 'bad request'

        mgr.session.delete.side_effect = [Resp204(), Resp400()]

        ok = mgr.delete_user('acc-1', 'User One')
        fail = mgr.delete_user('acc-2', 'User Two')
        self.assertTrue(ok)
        self.assertFalse(fail)

    def test_save_users_to_file(self):
        mgr = JiraUserManager()
        users = [
            {'accountId': '1', 'displayName': 'U1'},
            {'accountId': '2', 'displayName': 'U2'},
        ]
        fname = 'non_active_users.json'
        try:
            mgr.save_users_to_file(users, fname)
            with open(fname, 'r') as f:
                data = json.load(f)
            self.assertEqual(len(data), 2)
        finally:
            if os.path.exists(fname):
                os.remove(fname)

if __name__ == '__main__':
    unittest.main()
