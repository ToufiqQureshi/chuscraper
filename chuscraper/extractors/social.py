"""
Social media link extraction.

Extracts profiles from:
- LinkedIn
- Twitter/X
- Facebook  
- Instagram
- GitHub
- YouTube
- And more...
"""

import re
from typing import Set, Dict, List
from urllib.parse import urlparse


class SocialExtractor:
    """Extract social media links from HTML content."""
    
    # Social media platforms and their patterns
    PLATFORMS = {
        'linkedin': [
            r'linkedin\.com/(in|company)/[\w-]+',
            r'linkedin\.com/profile/view\?id=[\w-]+',
        ],
        'twitter': [
            r'twitter\.com/[\w]+',
            r'x\.com/[\w]+',
        ],
        'facebook': [
            r'facebook\.com/[\w.]+',
            r'fb\.com/[\w.]+',
        ],
        'instagram': [
            r'instagram\.com/[\w.]+',
        ],
        'github': [
            r'github\.com/[\w-]+',
        ],
        'youtube': [
            r'youtube\.com/(c|channel|user)/[\w-]+',
            r'youtube\.com/@[\w-]+',
        ],
        'tiktok': [
            r'tiktok\.com/@[\w.]+',
        ],
        'reddit': [
            r'reddit\.com/(r|u|user)/[\w-]+',
        ],
        'pinterest': [
            r'pinterest\.com/[\w-]+',
        ],
        'telegram': [
            r't\.me/[\w]+',
            r'telegram\.me/[\w]+',
        ],
        'discord': [
            r'discord\.gg/[\w-]+',
            r'discord\.com/invite/[\w-]+',
        ],
        'whatsapp': [
            r'wa\.me/[\d]+',
            r'whatsapp\.com/.*',
        ],
    }
    
    @classmethod
    def extract(cls, html: str) -> Dict[str, Set[str]]:
        """
        Extract social media links grouped by platform.
        
        Args:
            html: HTML content
            
        Returns:
            Dict mapping platform name to set of URLs
        """
        results = {}
        
        # Extract all links from HTML
        all_links = cls._extract_all_links(html)
        
        # Match against platform patterns
        for platform, patterns in cls.PLATFORMS.items():
            matches = set()
            for link in all_links:
                for pattern in patterns:
                    if re.search(pattern, link, re.IGNORECASE):
                        # Normalize URL
                        normalized = cls._normalize_url(link)
                        matches.add(normalized)
                        break
            
            if matches:
                results[platform] = matches
        
        return results
    
    @classmethod
    def extract_flat(cls, html: str) -> Set[str]:
        """
        Extract all social media links as a flat set.
        
        Args:
            html: HTML content
            
        Returns:
            Set of all social media URLs
        """
        all_social = set()
        grouped = cls.extract(html)
        
        for platform_links in grouped.values():
            all_social.update(platform_links)
        
        return all_social
    
    @classmethod
    def _extract_all_links(cls, html: str) -> Set[str]:
        """Extract all HTTP(S) links from HTML."""
        # Pattern for URLs
        url_pattern = r'https?://[^\s<>"{}|\\^`\[\]]+'
        links = set(re.findall(url_pattern, html, re.IGNORECASE))
        
        # Also extract from href attributes
        href_pattern = r'href=["\']([^"\']+)["\']'
        links.update(re.findall(href_pattern, html, re.IGNORECASE))
        
        return links
    
    @staticmethod
    def _normalize_url(url: str) -> str:
        """Normalize URL (remove trailing slashes, fragments)."""
        # Remove URL parameters and fragments for social links
        url = url.split('?')[0].split('#')[0]
        
        # Remove trailing slash
        url = url.rstrip('/')
        
        # Ensure https
        if url.startswith('http://'):
            url = 'https://' + url[7:]
        
        return url
    
    @classmethod
    def extract_usernames(cls, html: str) -> Dict[str, Set[str]]:
        """
        Extract just usernames from social links.
        
        Returns:
            Dict mapping platform to usernames
        """
        grouped = cls.extract(html)
        usernames = {}
        
        for platform, links in grouped.items():
            usernames[platform] = set()
            for link in links:
                username = cls._extract_username(link, platform)
                if username:
                    usernames[platform].add(username)
        
        return usernames
    
    @staticmethod
    def _extract_username(url: str, platform: str) -> str:
        """Extract username from social media URL."""
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        
        if platform == 'linkedin':
            # linkedin.com/in/username or linkedin.com/company/name
            parts = path.split('/')
            if len(parts) >= 2:
                return parts[1]
        
        elif platform in ['twitter', 'instagram', 'github', 'pinterest']:
            # Direct username after domain
            parts = path.split('/')
            if parts:
                return parts[0].lstrip('@')
        
        elif platform == 'youtube':
            # youtube.com/@username or /c/channel
            if '@' in path:
                return path.split('@')[1].split('/')[0]
            parts = path.split('/')
            if len(parts) >= 2:
                return parts[1]
        
        elif platform in ['telegram', 'tiktok']:
            return path.lstrip('@')
        
        return path
