import unittest
from unittest.mock import MagicMock, patch, AsyncMock
import sys
import os

# Add project root to sys.path to resolve imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from brain.filters import ContentFilter
from ears.djinni_listener import DjinniListener
from ears.upwork_listener import UpworkListener
from config.settings import settings

class TestLeadMachine(unittest.IsolatedAsyncioTestCase):
    
    async def test_content_filter_logic(self):
        """Test that the filter correctly blocks Senior roles and accepts Junior."""
        
        # Test 1: Should REJECT Senior
        bad_text = "Looking for a Senior React Developer with 5+ years experience."
        self.assertFalse(ContentFilter.check(bad_text), "Filter should reject 'Senior'")

        # Test 2: Should REJECT Gambling/Crypto
        bad_crypto = "Junior Frontend for a new Crypto Casino project."
        self.assertFalse(ContentFilter.check(bad_crypto), "Filter should reject 'Crypto/Casino'")

        # Test 3: Should ACCEPT Junior React
        good_text = "We are looking for a Junior React Developer. Experience 1 year. Remote."
        self.assertTrue(ContentFilter.check(good_text), "Filter should accept 'Junior React'")

    @patch("httpx.AsyncClient")
    async def test_djinni_parsing_success(self, mock_client):
        """Test Djinni scraping logic with MOCKED HTML response."""
        
        # Mock HTML response from Djinni
        fake_html = """
        <li class="list-jobs__item">
            <div class="job-list-item__description">
                Looking for a Junior Python Developer. Django, FastAPI.
            </div>
            <a class="job-list-item__link" href="/jobs/111-junior-python-dev">
                Junior Python Developer
            </a>
        </li>
        """
        
        # Setup Mock
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = fake_html
        
        # Mock context manager
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.__aexit__.return_value = None
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        # Initialize Listener
        listener = DjinniListener()
        
        # We Mock ai_client and notifier to avoid real API calls
        with patch("ears.djinni_listener.ai_client") as mock_ai, \
             patch("ears.djinni_listener.notifier") as mock_notify:
            
            # Setup AI to return a high score
            mock_ai.analyze_vacancy = AsyncMock(return_value={"score": 8, "company": "TestCo"})
            mock_notify.send_vacancy_alert = AsyncMock()

            # Run scrape for one keyword
            await listener.scrape_keyword("Python")

            # ASSERTIONS
            # 1. Check if AI was called (means parsing worked)
            mock_ai.analyze_vacancy.assert_called()
            
            # 2. Check if text passed to AI contains correct info
            args, _ = mock_ai.analyze_vacancy.call_args
            self.assertIn("Junior Python Developer", args[0])
            
            # 3. Check if Notifier was called with correct link
            expected_link = "https://djinni.co/jobs/111-junior-python-dev"
            mock_notify.send_vacancy_alert.assert_called()
            call_args = mock_notify.send_vacancy_alert.call_args[0]
            self.assertEqual(call_args[1], expected_link)

    @patch("httpx.AsyncClient")
    async def test_upwork_cookie_expired(self, mock_client):
        """Test that Upwork listener detects login redirect (Cookie Expired)."""
        
        # Mock HTML that looks like a login page
        fake_html = "<html><head><title>Log In - Upwork</title></head><body>Please Log In</body></html>"
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.text = fake_html
        
        mock_client_instance = AsyncMock()
        mock_client_instance.__aenter__.return_value = mock_client_instance
        mock_client_instance.get.return_value = mock_response
        mock_client.return_value = mock_client_instance

        listener = UpworkListener()

        # We need to capture logs to verify the warning
        with self.assertLogs('hunter', level='ERROR') as cm:
            await listener.scrape_keyword("React")
            
            # Check if "Cookie EXPIRED" was logged
            self.assertTrue(any("Cookie EXPIRED" in log for log in cm.output), 
                            "Should log error about expired cookie")

    def test_settings_portfolio(self):
        """Verify that Portfolio URL is correctly set."""
        self.assertTrue(settings.PORTFOLIO_URL.startswith("http"), "PORTFOLIO_URL should be a valid link")
        self.assertIn("induktr", settings.PORTFOLIO_URL, "Portfolio URL should belong to Induktr")

if __name__ == '__main__':
    unittest.main()
