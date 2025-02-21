import pandas as pd
import io
import re
from urllib.parse import urlparse

def export_to_csv(data):
    """Convert analysis data to CSV format"""
    output = io.StringIO()
    
    # Export meta information
    meta_df = pd.DataFrame([data['meta']])
    meta_df.to_csv(output, index=False)
    output.write("\n\nHeader Analysis\n")
    
    # Export headers
    headers_df = pd.DataFrame(data['headers'])
    headers_df.to_csv(output, index=False)
    output.write("\n\nLinks Analysis\n")
    
    # Export links
    links_df = pd.DataFrame(data['links'])
    links_df.to_csv(output, index=False)
    
    return output.getvalue()

def validate_url(url):
    """Validate URL format"""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc]) and result.scheme in ['http', 'https']
    except:
        return False
