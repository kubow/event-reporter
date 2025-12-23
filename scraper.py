from bs4 import BeautifulSoup
from requests.adapters import HTTPAdapter
from requests import get, RequestException, Session
from urllib3.util import create_urllib3_context
from urllib3 import PoolManager
import subprocess
import ssl

class AddedCipherAdapter(HTTPAdapter):
  def init_poolmanager(self, connections, maxsize, block=False):
    ctx = create_urllib3_context(ciphers=":HIGH:!DH:!aNULL") ## More secure way here
    #ctx = create_urllib3_context()
    #ctx.set_ciphers("DEFAULT@SECLEVEL=1")           # ✅ Accepting all types of ciphers
    #ctx.check_hostname = False                      # ✅ Disable hostname checking
    #ctx.verify_mode = ssl.CERT_NONE                 # ✅ Fully disable verification
    # doing this instead of line #9
    self.poolmanager = PoolManager(
      num_pools=connections,
      maxsize=maxsize,
      block=block,
      ssl_context=ctx
    )

def fetch_webpage(url):
    """
    Fetches the content of a webpage.

    :param url: URL of the webpage to fetch
    :return: HTML content of the webpage
    """
    try:
        response = Session()
        response.mount("https://", AddedCipherAdapter())
        response.get(url)  # , verify=False
        return response.text
    except RequestException as e:
        print(f"Error fetching {url}: {e}")
        return fetch_with_curl(url)


def fetch_with_curl(url):
    try:
        result = subprocess.run(
            ["curl", "-k", url],
            capture_output=True, text=True, check=True
        )
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"curl failed: {e.stderr}")
        return None

def parse_html(html_content):
    """
    Parses HTML content using BeautifulSoup.

    :param html_content: HTML content to parse
    :return: BeautifulSoup object
    """
    return BeautifulSoup(html_content, 'html.parser')


def get_elements_by_tag(soup, tag_name):
    """
    Extracts elements by tag name.

    :param soup: BeautifulSoup object
    :param tag_name: Tag name to search for
    :return: List of elements with the specified tag name
    """
    return soup.find_all(tag_name)


def get_element_by_id(soup, element_id):
    """
    Extracts a single element by its ID.

    :param soup: BeautifulSoup object
    :param element_id: ID of the element to search for
    :return: Element with the specified ID or None if not found
    """
    return soup.find(id=element_id)


def get_elements_by_class(soup, class_name):
    """
    Extracts elements by class name.

    :param soup: BeautifulSoup object
    :param class_name: Class name to search for
    :return: List of elements with the specified class name
    """
    return soup.find_all(class_=class_name)


def get_elements_by_xpath_like(soup, xpath_like):
    """
    Extracts elements using a CSS selector equivalent to an XPath-like query.

    :param soup: BeautifulSoup object
    :param xpath_like: XPath-like query to search for
    :return: List of elements matching the query
    """
    # Convert XPath-like query to CSS selector
    css_selector = xpath_like.replace("//div[contains(@class, 'Test')]", "div.Test")
    return soup.select(css_selector)
    
def scrape_website(url):
    """
    Scrapes a website and returns the BeautifulSoup object.

    :param url: URL of the website to scrape
    :return: BeautifulSoup object or None if fetching fails
    """
    html_content = fetch_webpage(url)
    if html_content:
        return parse_html(html_content)
    return None
