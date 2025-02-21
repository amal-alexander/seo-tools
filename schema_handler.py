import json
from typing import Dict, List, Any
import requests
from bs4 import BeautifulSoup

class SchemaHandler:
    def __init__(self):
        self.supported_types = {
            "Article": self._generate_article_schema,
            "Product": self._generate_product_schema,
            "LocalBusiness": self._generate_local_business_schema,
            "FAQ": self._generate_faq_schema
        }
        
    def validate_schema(self, url: str) -> Dict[str, Any]:
        """Validate schema markup on a webpage"""
        try:
            response = requests.get(url)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all schema markup
            schema_tags = soup.find_all('script', type='application/ld+json')
            schemas = []
            issues = []
            
            for tag in schema_tags:
                try:
                    schema = json.loads(tag.string)
                    schemas.append(schema)
                    
                    # Basic validation
                    if '@type' not in schema:
                        issues.append("Missing @type in schema")
                    if '@context' not in schema:
                        issues.append("Missing @context in schema")
                        
                except json.JSONDecodeError:
                    issues.append("Invalid JSON-LD format")
                    
            return {
                "valid": len(issues) == 0,
                "schemas_found": len(schemas),
                "schemas": schemas,
                "issues": issues
            }
        except Exception as e:
            return {
                "valid": False,
                "error": str(e)
            }
    
    def generate_schema(self, page_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate schema markup based on page type and data"""
        if page_type not in self.supported_types:
            return {
                "error": f"Unsupported schema type. Supported types: {', '.join(self.supported_types.keys())}"
            }
            
        generator = self.supported_types[page_type]
        schema = generator(data)
        
        return {
            "schema": schema,
            "json_ld": f'<script type="application/ld+json">\n{json.dumps(schema, indent=2)}\n</script>'
        }
    
    def _generate_article_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        # Convert date to ISO format string if it exists
        date = data.get("date")
        date_str = date.isoformat() if date else ""
        
        return {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": data.get("title", ""),
            "author": {
                "@type": "Person",
                "name": data.get("author", "")
            },
            "datePublished": date_str,
            "description": data.get("description", "")
        }
    
    def _generate_product_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "price": data.get("price", ""),
            "priceCurrency": data.get("currency", "USD")
        }
    
    def _generate_local_business_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "LocalBusiness",
            "name": data.get("name", ""),
            "address": {
                "@type": "PostalAddress",
                "streetAddress": data.get("street", ""),
                "addressLocality": data.get("city", ""),
                "addressRegion": data.get("region", ""),
                "postalCode": data.get("postal_code", "")
            }
        }
    
    def _generate_faq_schema(self, data: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "@context": "https://schema.org",
            "@type": "FAQPage",
            "mainEntity": [
                {
                    "@type": "Question",
                    "name": qa.get("question", ""),
                    "acceptedAnswer": {
                        "@type": "Answer",
                        "text": qa.get("answer", "")
                    }
                } for qa in data.get("questions", [])
            ]
        }
