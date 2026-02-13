"""
Export lead data to various formats.

Supports:
- CSV export
- JSON export
- Deduplication
- Data cleaning
"""

import csv
import json
from typing import List, Dict, Set
from pathlib import Path


class LeadExporter:
    """Export lead data to CSV, JSON, and other formats."""
    
    @staticmethod
    def to_csv(leads: List[Dict], filename: str, flat_format: bool = True) -> None:
        """
        Export leads to CSV file.
        
        Args:
            leads: List of lead dicts from scraper
            filename: Output CSV file path
            flat_format: Flatten nested data (recommended)
        """
        if not leads:
            return
        
        # Flatten leads for CSV
        flattened = []
        for lead in leads:
            if not lead.get('success'):
                continue
            
            data = lead.get('data', {})
            if not data:
                continue
            
            # Create flat row
            row = {
                'url': lead['url'],
                'scraped_at': lead['scraped_at'],
            }
            
            # Add emails (comma-separated)
            emails = data.get('emails', [])
            row['emails'] = ', '.join(emails) if emails else ''
            row['email_count'] = len(emails)
            
            # Add phones (comma-separated)
            phones = data.get('phones', [])
            row['phones'] = ', '.join(phones) if phones else ''
            row['phone_count'] = len(phones)
            
            # Add social media
            social = data.get('social', {})
            for platform, links in social.items():
                row[f'social_{platform}'] = ', '.join(links) if links else ''
            
            # Add metadata
            metadata = data.get('metadata', {})
            row['title'] = metadata.get('title', '')
            row['description'] = metadata.get('description', '')
            row['author'] = metadata.get('author', '')
            
            flattened.append(row)
        
        if not flattened:
            return
        
        # Write CSV
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=flattened[0].keys())
            writer.writeheader()
            writer.writerows(flattened)
    
    @staticmethod
    def to_json(leads: List[Dict], filename: str, pretty: bool = True) -> None:
        """
        Export leads to JSON file.
        
        Args:
            leads: List of lead dicts
            filename: Output JSON file path
            pretty: Pretty-print JSON
        """
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, 'w', encoding='utf-8') as f:
            if pretty:
                json.dump(leads, f, indent=2, ensure_ascii=False)
            else:
                json.dump(leads, f, ensure_ascii=False)
    
    @staticmethod
    def deduplicate_emails(leads: List[Dict]) -> List[Dict]:
        """
        Remove duplicate emails across all leads.
        
        Args:
            leads: List of lead dicts
            
        Returns:
            Deduplicated leads
        """
        seen_emails: Set[str] = set()
        deduplicated = []
        
        for lead in leads:
            if not lead.get('success') or not lead.get('data'):
                deduplicated.append(lead)
                continue
            
            # Filter emails
            emails = lead['data'].get('emails', [])
            unique_emails = []
            for email in emails:
                if email not in seen_emails:
                    unique_emails.append(email)
                    seen_emails.add(email)
            
            # Update lead
            lead['data']['emails'] = unique_emails
            deduplicated.append(lead)
        
        return deduplicated
    
    @staticmethod
    def merge_leads(leads: List[Dict]) -> Dict[str, Dict]:
        """
        Merge leads by URL (combine data from same URL).
        
        Returns:
            Dict mapping URL to merged lead data
        """
        merged = {}
        
        for lead in leads:
            if not lead.get('success') or not lead.get('data'):
                continue
            
            url = lead['url']
            
            if url not in merged:
                merged[url] = {
                    'url': url,
                    'emails': set(),
                    'phones': set(),
                    'social': {},
                    'metadata': lead['data'].get('metadata', {})
                }
            
            # Merge emails
            merged[url]['emails'].update(lead['data'].get('emails', []))
            
            # Merge phones
            merged[url]['phones'].update(lead['data'].get('phones', []))
            
            # Merge social
            social = lead['data'].get('social', {})
            for platform, links in social.items():
                if platform not in merged[url]['social']:
                    merged[url]['social'][platform] = set()
                merged[url]['social'][platform].update(links)
        
        # Convert sets to lists
        for url in merged:
            merged[url]['emails'] = list(merged[url]['emails'])
            merged[url]['phones'] = list(merged[url]['phones'])
            for platform in merged[url]['social']:
                merged[url]['social'][platform] = list(merged[url]['social'][platform])
        
        return merged
    
    @staticmethod
    def filter_by_criteria(leads: List[Dict], min_emails: int = 0, min_phones: int = 0) -> List[Dict]:
        """
        Filter leads by criteria.
        
        Args:
            leads: List of leads
            min_emails: Minimum emails required
            min_phones: Minimum phones required
            
        Returns:
            Filtered leads
        """
        filtered = []
        
        for lead in leads:
            if not lead.get('success') or not lead.get('data'):
                continue
            
            email_count = len(lead['data'].get('emails', []))
            phone_count = len(lead['data'].get('phones', []))
            
            if email_count >= min_emails and phone_count >= min_phones:
                filtered.append(lead)
        
        return filtered
