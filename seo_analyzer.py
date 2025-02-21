import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
import trafilatura

class SEOAnalyzer:
    def __init__(self, url):
        self.url = url
        self.response = requests.get(url, headers={'User-Agent': 'SEOAnalyzer/1.0'})
        self.soup = BeautifulSoup(self.response.text, 'html.parser')
        
    def get_meta_info(self):
        """Extract meta information from the page"""
        meta_info = {
            "title": self.soup.title.string if self.soup.title else None,
            "meta_description": None,
            "meta_keywords": None,
            "canonical": None,
            "robots": None,
            "status_code": self.response.status_code
        }
        
        for meta in self.soup.find_all('meta'):
            if meta.get('name', '').lower() == 'description':
                meta_info['meta_description'] = meta.get('content', '')
            elif meta.get('name', '').lower() == 'keywords':
                meta_info['meta_keywords'] = meta.get('content', '')
            elif meta.get('name', '').lower() == 'robots':
                meta_info['robots'] = meta.get('content', '')
                
        canonical = self.soup.find('link', {'rel': 'canonical'})
        if canonical:
            meta_info['canonical'] = canonical.get('href', '')
            
        return meta_info
    
    def analyze_headers(self):
        """Analyze header tags (H1-H6)"""
        headers = []
        for i in range(1, 7):
            for header in self.soup.find_all(f'h{i}'):
                headers.append({
                    'type': f'H{i}',
                    'content': header.get_text().strip(),
                    'count': len(header.get_text().strip().split())
                })
        return headers
    
    def analyze_links(self):
        """Analyze links on the page"""
        links = []
        for link in self.soup.find_all('a'):
            href = link.get('href')
            if href:
                absolute_url = urljoin(self.url, href)
                links.append({
                    'text': link.get_text().strip(),
                    'url': absolute_url,
                    'internal': self.url in absolute_url
                })
        return links
    
    def get_main_content(self):
        """Get main content using trafilatura"""
        downloaded = trafilatura.fetch_url(self.url)
        text = trafilatura.extract(downloaded)
        return text if text else ""
