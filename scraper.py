import requests
from bs4 import BeautifulSoup
import os
import time
import re
from urllib.parse import urljoin

SKIP_ARTICLES = set(['https://www.bu.edu/tech/support/research/whats-happening/updates/'])

class BUResearchScraper:
    def __init__(self, base_url, output_dir="scraped_content"):
        self.base_url = base_url
        self.output_dir = output_dir
        self.visited_urls = SKIP_ARTICLES
        
        # Create output directory if it doesn't exist
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
    def clean_filename(self, filename):
        """Create a valid filename from a string."""
        # Replace invalid characters with underscores
        filename = re.sub(r'[\\/*?:"<>|]', "_", filename)
        # Limit filename length
        return filename[:100] if len(filename) > 100 else filename
    
    def get_soup(self, url):
        """Get BeautifulSoup object from URL."""
        try:
            response = requests.get(url)
            response.raise_for_status()
            return BeautifulSoup(response.text, 'html.parser')
        except requests.exceptions.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
    
    def extract_article_content(self, article_url):
        """Extract content from an article page."""
        print(f"Extracting content from: {article_url}")
        soup = self.get_soup(article_url)
        if not soup:
            return None
        
        # Find the title - usually in an h1 element in the page-title div
        title_elem = soup.find('div', class_='page-title')
        if title_elem and title_elem.find('h1', class_='title'):
            title = title_elem.find('h1', class_='title').text.strip()
        else:
            # Fallback to any h1
            title_elem = soup.find('h1')
            title = title_elem.text.strip() if title_elem else "Untitled Article"
        
        # Find the main content - based on the provided example
        content_div = soup.find('div', class_='entry')
        
        if not content_div:
            # Fallback options
            content_div = soup.find('section', {'role': 'main'})
        
        if not content_div:
            content_div = soup.find('div', class_='content')
            
        if not content_div:
            print(f"Could not find content in {article_url}")
            return None
        
        # Convert content to markdown
        markdown_content = f"# {title}\n\n"
        
        # Process content elements
        for element in content_div.find_all(['p', 'h2', 'h3', 'h4', 'ul', 'ol', 'pre', 'code']):
            # Skip empty elements
            if not element.text.strip():
                continue
                
            if element.name == 'h2':
                markdown_content += f"\n## {element.text.strip()}\n\n"
            elif element.name == 'h3':
                markdown_content += f"\n### {element.text.strip()}\n\n"
            elif element.name == 'h4':
                markdown_content += f"\n#### {element.text.strip()}\n\n"
            elif element.name == 'p':
                # Skip elements that are just anchors or contain only images
                if element.find('a', {'name': True}) and len(element.text.strip()) == 0:
                    continue
                
                markdown_content += f"{element.text.strip()}\n\n"
            elif element.name == 'ul' or element.name == 'ol':
                # Instead of getting the whole list text, process each list item
                for li in element.find_all('li', recursive=False):
                    prefix = "* " if element.name == 'ul' else "1. "
                    
                    # Handle nested lists
                    if li.find(['ul', 'ol']):
                        try:
                            markdown_content += f"{prefix}{li.contents[0].strip() if li.contents else ''}\n"
                            
                            for nested_list in li.find_all(['ul', 'ol'], recursive=False):
                                for nested_li in nested_list.find_all('li'):
                                    nested_prefix = "  * " if nested_list.name == 'ul' else "  1. " # doesnt properly handle ol right
                                    markdown_content += f"{nested_prefix}{nested_li.text.strip()}\n"
                        except:
                            pass
                    else:
                        markdown_content += f"{prefix}{li.text.strip()}\n"
                        
                markdown_content += "\n"
            elif element.name == 'pre' or element.name == 'code':
                # Extract code blocks - common in tech documentation
                code_text = element.text.strip()
                if code_text:
                    markdown_content += f"```\n{code_text}\n```\n\n"
        
        return {
            'title': title,
            'content': markdown_content,
            'url': article_url
        }
    
    def save_article(self, article_data):
        """Save article to a markdown file."""
        if not article_data:
            return
        
        filename = self.clean_filename(article_data['title'])
        filepath = os.path.join(self.output_dir, f"{filename}.md")
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(article_data['content'])
            f.write(f"\n\nSource: {article_data['url']}")
        
        print(f"Saved: {filepath}")
    
    def extract_links_from_support_rows(self, soup):
        """Extract links from div elements with class 'clearfix support-row'."""
        links = []
        support_rows = soup.find_all('div', class_='clearfix support-row')
        
        for row in support_rows:
            link_elements = row.find_all('a')
            for link in link_elements:
                href = link.get('href')
                if href:
                    full_url = urljoin(self.base_url, href)
                    links.append(full_url)
        
        return links
    
    def scrape_recursively(self, url, depth=1, max_depth=10):
        """Recursively scrape articles and their linked pages."""
        if depth > max_depth or url in self.visited_urls:
            return
        
        self.visited_urls.add(url)
        print(f"Visiting: {url} (depth {depth})")
        
        soup = self.get_soup(url)
        if not soup:
            return
        
        # Check if this is an article page
        if soup.find('div', class_='page-title') or soup.find('div', class_='entry'):
            article_data = self.extract_article_content(url)
            if article_data:
                self.save_article(article_data)
        
        # Find links to follow
        links_to_follow = []
        
        # Check for support rows
        if soup.find('div', class_='clearfix support-row'):
            links_to_follow.extend(self.extract_links_from_support_rows(soup))
        
        # Follow links
        for link in links_to_follow:
            if link not in self.visited_urls:
                # Sleep briefly to avoid overwhelming the server
                time.sleep(0.1)
                self.scrape_recursively(link, depth + 1, max_depth)
    
    def extract_table_of_contents(self, soup):
        """Extract table of contents links if available."""
        toc_links = []
        
        # Look for a table of contents-like section
        # In the example, it's in a div with <strong>Sections</strong> followed by a list
        sections_div = None
        for div in soup.find_all('div'):
            if div.find('strong') and div.find('strong').text.strip() == 'Sections':
                sections_div = div
                break
        
        if sections_div:
            for a in sections_div.find_all('a'):
                href = a.get('href')
                if href:
                    # Handle both absolute and relative URLs
                    if not href.startswith('http'):
                        # Handle anchor links
                        base_url = self.base_url
                        if '#' in href and 'http' not in href:
                            base_url = soup.url if hasattr(soup, 'url') else self.base_url
                        full_url = urljoin(base_url, href)
                    else:
                        full_url = href
                    toc_links.append(full_url)
        
        return toc_links
    
    def process_code_blocks(self, soup):
        """Extract code blocks with proper formatting."""
        code_blocks = []
        
        # Find all pre and code elements
        for pre in soup.find_all('pre'):
            code = pre.find('code')
            if code:
                code_text = code.text.strip()
                language = ''
                if 'class' in code.attrs:
                    for cls in code['class']:
                        if cls.startswith('language-') or cls == 'code-block':
                            language = cls.replace('language-', '')
                            break
                
                code_blocks.append({
                    'language': language,
                    'code': code_text
                })
            else:
                code_blocks.append({
                    'language': '',
                    'code': pre.text.strip()
                })
        
        return code_blocks
    
    def start_scraping(self):
        """Start scraping from the base URL."""
        print(f"Starting to scrape from {self.base_url}")
        self.scrape_recursively(self.base_url)
        print(f"Scraping complete. Content saved to {self.output_dir}/")


# Usage
if __name__ == "__main__":
    base_url = "https://www.bu.edu/tech/support/research/"
    scraper = BUResearchScraper(base_url)
    # scraper.start_scraping()


    # scraper = BUResearchScraper("https://www.bu.edu/tech/support/research/")
    # # article_data = scraper.extract_article_content("https://www.bu.edu/tech/support/research/software-and-programming/common-languages/python/python-ml/tensorflow/")
    article_data = scraper.extract_article_content("https://www.bu.edu/tech/support/research/system-usage/running-jobs/batch-script-examples/")
    scraper.save_article(article_data)
    