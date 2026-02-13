"""
Phone number extraction and normalization.

Supports multiple country formats:
- India (IN)
- United States (US)
- United Kingdom (UK)
- Generic international format
"""

import re
from typing import Set, List, Dict


class PhoneExtractor:
    """Extract and normalize phone numbers from HTML content."""
    
    # Country-specific patterns
    PATTERNS = {
        'IN': [
            r'(\+91|0)?[\s-]?[6-9]\d{9}',  # Indian mobile
            r'(\+91|0)?[\s-]?\d{2,4}[\s-]?\d{6,8}',  # Indian landline
        ],
        'US': [
            r'(\+1|1)?[\s-]?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}',  # US format
            r'\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # Simple US
        ],
        'UK': [
            r'(\+44|0)?[\s-]?[1-9]\d{9,10}',  # UK format
            r'(\+44|0)?[\s-]?\d{4}[\s-]?\d{6}',  # UK landline
        ],
        'GENERIC': [
            r'\+?\d{10,15}',  # Generic international
        ]
    }
    
    @classmethod
    def extract(cls, html: str, countries: List[str] = None) -> Set[str]:
        """
        Extract phone numbers from HTML.
        
        Args:
            html: HTML content as string
            countries: List of country codes to extract (default: ['IN', 'US', 'UK'])
            
        Returns:
            Set of normalized phone numbers
        """
        if countries is None:
            countries = ['IN', 'US', 'UK']
        
        phones = set()
        
        # Remove HTML tags for cleaner extraction
        try:
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(html, 'html.parser')
            text = soup.get_text()
        except:
            text = html
        
        # Extract by country patterns
        for country in countries:
            patterns = cls.PATTERNS.get(country, cls.PATTERNS['GENERIC'])
            for pattern in patterns:
                matches = re.findall(pattern, text)
                phones.update(matches)
        
        # Also check tel: links
        phones.update(cls._extract_from_tel_links(html))
        
        # Normalize all phones
        normalized = set()
        for phone in phones:
            cleaned = cls.normalize(phone)
            if cls.validate(cleaned):
                normalized.add(cleaned)
        
        return normalized
    
    @classmethod
    def _extract_from_tel_links(cls, html: str) -> Set[str]:
        """Extract from tel: links."""
        tel_pattern = r'tel:([+\d\s\-\(\)]+)'
        return set(re.findall(tel_pattern, html, re.IGNORECASE))
    
    @staticmethod
    def normalize(phone: str) -> str:
        """
        Normalize phone number (remove formatting, keep digits and +).
        
        Args:
            phone: Raw phone number
            
        Returns:
            Normalized phone (digits and + only)
        """
        # Keep only digits and plus sign
        normalized = re.sub(r'[^\d+]', '', str(phone))
        
        # Ensure plus is at start if present
        if '+' in normalized:
            normalized = '+' + normalized.replace('+', '')
        
        return normalized
    
    @staticmethod
    def validate(phone: str) -> bool:
        """
        Validate phone number.
        
        Args:
            phone: Normalized phone number
            
        Returns:
            True if valid
        """
        # Remove plus for length check
        digits_only = phone.replace('+', '')
        
        # Valid phone: 10-15 digits
        if not (10 <= len(digits_only) <= 15):
            return False
        
        # Should be all digits (after +)
        if not digits_only.isdigit():
            return False
        
        return True
    
    @classmethod
    def extract_by_country(cls, html: str) -> Dict[str, Set[str]]:
        """
        Extract phones grouped by country.
        
        Returns:
            Dict mapping country code to phone numbers
        """
        results = {}
        
        for country in ['IN', 'US', 'UK']:
            phones = cls.extract(html, countries=[country])
            if phones:
                results[country] = phones
        
        return results
    
    @classmethod
    def format_phone(cls, phone: str, country: str = 'IN') -> str:
        """
        Format phone number for display.
        
        Args:
            phone: Normalized phone
            country: Country code for formatting
            
        Returns:
            Formatted phone string
        """
        digits = phone.replace('+', '')
        
        if country == 'IN':
            if len(digits) == 10:
                return f'+91 {digits[:5]} {digits[5:]}'
            elif len(digits) == 12 and digits.startswith('91'):
                return f'+{digits[:2]} {digits[2:7]} {digits[7:]}'
        
        elif country == 'US':
            if len(digits) == 10:
                return f'+1 ({digits[:3]}) {digits[3:6]}-{digits[6:]}'
            elif len(digits) == 11 and digits.startswith('1'):
                return f'+{digits[0]} ({digits[1:4]}) {digits[4:7]}-{digits[7:]}'
        
        # Default: return normalized
        return phone
