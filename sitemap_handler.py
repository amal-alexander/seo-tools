import xml.etree.ElementTree as ET
from datetime import datetime
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

class SitemapHandler:
    def __init__(self):
        self.urls = []
        
    def validate_sitemap(self, sitemap_url):
        """Validate an existing sitemap"""
        try:
            response = requests.get(sitemap_url)
            if response.status_code != 200:
                return {
                    "valid": False,
                    "error": f"Failed to fetch sitemap: Status code {response.status_code}"
                }
                
            root = ET.fromstring(response.content)
            urls = []
            issues = []
            
            # Extract URLs and validate each
            for url in root.findall(".//{http://www.sitemaps.org/schemas/sitemap/0.9}loc"):
                url_str = url.text
                urls.append(url_str)
                
                # Check if URL is accessible
                try:
                    url_response = requests.head(url_str, allow_redirects=True)
                    if url_response.status_code != 200:
                        issues.append({
                            "url": url_str,
                            "issue": f"URL returned status code {url_response.status_code}"
                        })
                except Exception as e:
                    issues.append({
                        "url": url_str,
                        "issue": f"Failed to access URL: {str(e)}"
                    })
            
            return {
                "valid": len(issues) == 0,
                "total_urls": len(urls),
                "issues": issues,
                "urls": urls
            }
        except ET.ParseError:
            return {
                "valid": False,
                "error": "Invalid XML format"
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def generate_sitemap(self, base_url, max_urls=500):
        """Generate a sitemap for a website"""
        self.urls = []
        visited = set()
        
        def crawl(url):
            if len(self.urls) >= max_urls or url in visited:
                return
                
            visited.add(url)
            try:
                response = requests.get(url)
                if response.status_code == 200:
                    self.urls.append({
                        "loc": url,
                        "lastmod": datetime.now().strftime("%Y-%m-%d"),
                        "priority": "0.8" if url == base_url else "0.5"
                    })
                    
                    soup = BeautifulSoup(response.text, 'html.parser')
                    for link in soup.find_all('a'):
                        href = link.get('href')
                        if href:
                            absolute_url = urljoin(base_url, href)
                            if (absolute_url.startswith(base_url) and 
                                absolute_url not in visited and 
                                not any(exclude in absolute_url for exclude in ['.pdf', '.jpg', '#'])):
                                crawl(absolute_url)
            except Exception:
                pass
                
        crawl(base_url)
        return self._generate_xml()
    
    def _generate_xml(self):
        """Generate XML sitemap from collected URLs"""
        root = ET.Element("urlset")
        root.set("xmlns", "http://www.sitemaps.org/schemas/sitemap/0.9")
        
        for url_data in self.urls:
            url_element = ET.SubElement(root, "url")
            for key, value in url_data.items():
                element = ET.SubElement(url_element, key)
                element.text = value
                
        return ET.tostring(root, encoding='unicode', method='xml')
