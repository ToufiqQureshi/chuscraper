"""
Email extraction and validation.

Extracts email addresses from HTML content with:
- Standard email patterns
- Obfuscated email detection
- Email validation
"""

import re
from typing import Set, List
from bs4 import BeautifulSoup


class EmailExtractor:
    """Extract and validate email addresses from HTML content."""
    
    # Comprehensive email regex (RFC 5322 simplified)
    EMAIL_PATTERN = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b'
    
    # Common email obfuscation patterns
    OBFUSCATED_PATTERNS = [
        (r'(\w+)\s*\[at\]\s*(\w+\.[\w.]+)', r'\1@\2'),
        (r'(\w+)\s*\(at\)\s*(\w+\.[\w.]+)', r'\1@\2'),
        (r'(\w+)\s*<at>\s*(\w+\.[\w.]+)', r'\1@\2'),
        (r'(\w+)\s*@\s*(\w+)\s*\.\s*(\w+)', r'\1@\2.\3'),
        (r'(\w+)\s*\[dot\]\s*(\w+)\s*@\s*(\w+\.[\w.]+)', r'\1.\2@\3'),
        (r'(\w+)@(\w+)\s*\[dot\]\s*([\w.]+)', r'\1@\2.\3'),
    ]
    
    # Common non-email patterns to exclude
    EXCLUDE_PATTERNS = [
        r'\.png$', r'\.jpg$', r'\.gif$', r'\.svg$',  # Images
        r'\.css$', r'\.js$',  # Scripts
        r'@2x\.',  # Retina images
    ]
    
    @classmethod
    def extract(cls, html: str, deobfuscate: bool = True) -> Set[str]:
        """
        Extract emails from HTML content.
        
        Args:
            html: HTML content as string
            deobfuscate: Whether to detect obfuscated emails
            
        Returns:
            Set of validated email addresses
        """
        emails = set()
        
        # Parse HTML to get text content
        try:
            soup = BeautifulSoup(html, 'html.parser')
            # Remove script and style elements
            for script in soup(['script', 'style']):
                script.decompose()
            text = soup.get_text()
        except:
            text = html
        
        # Standard extraction
        emails.update(re.findall(cls.EMAIL_PATTERN, text, re.IGNORECASE))
        
        # Extract from mailto links
        emails.update(cls._extract_from_mailto(html))
        
        # Deobfuscate common patterns
        if deobfuscate:
            for pattern, replacement in cls.OBFUSCATED_PATTERNS:
                deobfuscated = re.sub(pattern, replacement, text, flags=re.IGNORECASE)
                emails.update(re.findall(cls.EMAIL_PATTERN, deobfuscated))
        
        # Filter and validate
        valid_emails = set()
        for email in emails:
            email = email.lower().strip()
            if cls.validate(email) and not cls._should_exclude(email):
                valid_emails.add(email)
        
        return valid_emails
    
    @classmethod
    def _extract_from_mailto(cls, html: str) -> Set[str]:
        """Extract emails from mailto: links."""
        emails = set()
        mailto_pattern = r'mailto:([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})'
        emails.update(re.findall(mailto_pattern, html, re.IGNORECASE))
        return emails
    
    @classmethod
    def _should_exclude(cls, email: str) -> bool:
        """Check if email matches exclusion patterns."""
        for pattern in cls.EXCLUDE_PATTERNS:
            if re.search(pattern, email, re.IGNORECASE):
                return True
        return False
    
    @staticmethod
    def validate(email: str) -> bool:
        """
        Validate email format and structure.
        
        Args:
            email: Email address to validate
            
        Returns:
            True if email is valid
        """
        if not email or len(email) > 254:
            return False
        
        try:
            local, domain = email.rsplit('@', 1)
        except ValueError:
            return False
        
        # Local part validation
        if not local or len(local) > 64:
            return False
        
        # Domain validation
        if not domain or len(domain) > 253:
            return False
        
        # Check for valid TLD
        parts = domain.split('.')
        if len(parts) < 2:
            return False
        
        tld = parts[-1]
        if not (2 <= len(tld) <= 63 and tld.isalpha()):
            return False
        
        # Check for common invalid domains
        invalid_domains = ['example.com', 'test.com', 'localhost']
        if domain in invalid_domains:
            return False
        
        return True
    
    @staticmethod
    def normalize(email: str) -> str:
        """Normalize email address (lowercase, stripped)."""
        return email.lower().strip()
    
    @classmethod
    def extract_and_validate(cls, html: str) -> List[dict]:
        """
        Extract emails with validation details.
        
        Returns:
            List of dicts with email and validation info
        """
        emails = cls.extract(html)
        return [
            {
                'email': email,
                'normalized': cls.normalize(email),
                'valid': cls.validate(email)
            }
            for email in emails
        ]
