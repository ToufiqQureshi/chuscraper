"""
Contact information aggregator.

Combines all extraction methods:
- Emails
- Phones
- Social media links
- Website metadata
"""

from typing import Dict, Set, List, Optional
from .email import EmailExtractor
from .phone import PhoneExtractor
from .social import SocialExtractor


class ContactExtractor:
    """Aggregate all contact information from HTML."""
    
    @classmethod
    def extract_all(
        cls,
        html: str,
        extract_emails: bool = True,
        extract_phones: bool = True,
        extract_social: bool = True,
        phone_countries: Optional[List[str]] = None
    ) -> Dict:
        """
        Extract all contact information from HTML.
        
        Args:
            html: HTML content
            extract_emails: Extract email addresses
            extract_phones: Extract phone numbers
            extract_social: Extract social media links
            phone_countries: Countries for phone extraction
            
        Returns:
            Dict with all extracted contact info
        """
        result = {
            'emails': set(),
            'phones': set(),
            'social': {},
            'metadata': {}
        }
        
        if extract_emails:
            result['emails'] = EmailExtractor.extract(html)
        
        if extract_phones:
            if phone_countries is None:
                phone_countries = ['IN', 'US', 'UK']
            result['phones'] = PhoneExtractor.extract(html, countries=phone_countries)
        
        if extract_social:
            result['social'] = SocialExtractor.extract(html)
        
        # Extract metadata
        result['metadata'] = cls._extract_metadata(html)
        
        # Convert sets to lists for JSON serialization
        result['emails'] = list(result['emails'])
        result['phones'] = list(result['phones'])
        
        # Flatten social links
        social_flat = []
        for platform, links in result['social'].items():
            social_flat.extend(links)
        result['social_flat'] = social_flat
        
        return result
    
    @staticmethod
    def _extract_metadata(html: str) -> Dict:
        """Extract website metadata."""
        from bs4 import BeautifulSoup
        import re
        
        metadata = {
            'title': None,
            'description': None,
            'author': None,
            'keywords': []
        }
        
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # Title
            title = soup.find('title')
            if title:
                metadata['title'] = title.get_text().strip()
            
            # Meta description
            desc = soup.find('meta', attrs={'name': 'description'}) or \
                   soup.find('meta', attrs={'property': 'og:description'})
            if desc:
                metadata['description'] = desc.get('content', '').strip()
            
            # Author
            author = soup.find('meta', attrs={'name': 'author'})
            if author:
                metadata['author'] = author.get('content', '').strip()
            
            # Keywords
            keywords = soup.find('meta', attrs={'name': 'keywords'})
            if keywords:
                kw_content = keywords.get('content', '')
                metadata['keywords'] = [k.strip() for k in kw_content.split(',')]
            
        except:
            pass
        
        return metadata
    
    @classmethod
    def extract_to_dict(cls, html: str) -> Dict:
        """
        Extract all contact info formatted for easy access.
        
        Returns:
            Clean dict with all contact information
        """
        data = cls.extract_all(html)
        
        return {
            'contact': {
                'emails': data['emails'],
                'phones': data['phones'],
            },
            'social': data['social'],
            'metadata': data['metadata'],
            'stats': {
                'email_count': len(data['emails']),
                'phone_count': len(data['phones']),
                'social_count': len(data.get('social_flat', []))
            }
        }
    
    @classmethod
    def has_contact_info(cls, html: str) -> bool:
        """Quick check if page has any contact information."""
        # Quick regex checks (faster than full extraction)
        has_email = bool(EmailExtractor.EMAIL_PATTERN and \
                        len(EmailExtractor.extract(html[:5000])) > 0)
        
        if has_email:
            return True
        
        # Check for social keywords
        social_keywords = ['linkedin', 'twitter', 'facebook', 'instagram', '@']
        html_lower = html[:5000].lower()
        return any(kw in html_lower for kw in social_keywords)
