"""
Exchange Rate API Integration Module
Fetches real-time currency exchange rates from ExchangeRate-API.com
"""

import requests
from datetime import datetime
from typing import Optional, Dict


class ExchangeRateAPI:
    """
    Handles fetching and caching of exchange rates from ExchangeRate-API.com
    Free tier: 1,500 requests/month, no API key required
    """
    
    BASE_URL = "https://api.exchangerate-api.com/v4/latest"
    
    @staticmethod
    def fetch_rate(from_currency: str = "BDT", to_currency: str = "AUD") -> Optional[Dict]:
        """
        Fetch the exchange rate from from_currency to to_currency
        
        Args:
            from_currency: Source currency code (default: BDT)
            to_currency: Target currency code (default: AUD)
            
        Returns:
            Dictionary with rate, timestamp, and source info, or None if failed
        """
        try:
            # Fetch rates with BDT as base currency
            response = requests.get(f"{ExchangeRateAPI.BASE_URL}/{from_currency}", timeout=10)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract the rate for target currency
            if to_currency in data.get("rates", {}):
                rate = data["rates"][to_currency]
                
                return {
                    "rate": rate,
                    "from_currency": from_currency,
                    "to_currency": to_currency,
                    "timestamp": datetime.now().isoformat(),
                    "source": "ExchangeRate-API",
                    "success": True
                }
            else:
                return {
                    "success": False,
                    "error": f"Currency {to_currency} not found in rates"
                }
                
        except requests.exceptions.Timeout:
            return {
                "success": False,
                "error": "Request timed out. Please try again."
            }
        except requests.exceptions.RequestException as e:
            return {
                "success": False,
                "error": f"API request failed: {str(e)}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Unexpected error: {str(e)}"
            }
    
    @staticmethod
    def format_timestamp(iso_timestamp: str) -> str:
        """
        Format ISO timestamp to human-readable format
        
        Args:
            iso_timestamp: ISO format timestamp string
            
        Returns:
            Formatted date string
        """
        try:
            dt = datetime.fromisoformat(iso_timestamp)
            return dt.strftime("%B %d, %Y at %I:%M %p")
        except:
            return "Unknown"

