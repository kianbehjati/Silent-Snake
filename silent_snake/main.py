import requests
from bs4 import BeautifulSoup
from urllib.parse import parse_qs, urlparse, urljoin
import re
from typing import Any,List
import signal
from ssl import SSLCertVerificationError
from details import server, techs
import argparse
import asyncio

type URL = str
type Domain = str
type Link = str
UserAgents = {
    "1" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36", #pc
    "2" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Safari/537.36 Edg/140.0.0.0", #pc
    "3" : "Mozilla/5.0 (iPhone; CPU iPhone OS 18_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/18.5 Mobile/15E148 Safari/604.1", #Iphone
    "4" : "Mozilla/5.0 (Linux; Android 8.0.0; SM-G955U Build/R16NW) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36" #Android
}

def check_url(url) -> URL:
    '''
    Lower case url and remove any white space at the end
    '''
    if re.search(r"https?://",url):
        return url.lower().rstrip('/') 
    url = "https://" + url
    return url.lower().rstrip('/') 

def get_domain(url) -> Domain:
    '''
    returns scheme://netloc

    Example : https://github.com
    '''

    parsed_url = urlparse(url)
    domain = f'{parsed_url.scheme}://{parsed_url.netloc}'
    return domain


def is_page(url:URL, extra_patterns: list[str] = None) -> bool:
    '''
    check for pagination
    '''

    default_patterns = [
        r'page', r'p', r'pg', r'pagenumber',
        r'start', r'offset', r'limit'
    ]

    patterns = set(default_patterns + (extra_patterns or []))

    # Parse the query parameters of the URL
    parsed = urlparse(url)
    query_params = parse_qs(parsed.query)

    # Check query parameter names
    for param in query_params:
        for pattern in patterns:
            if re.search(pattern, param, re.IGNORECASE):
                return True

    # Also check fragments (e.g., #page=2)
    if parsed.fragment:
        for pattern in patterns:
            if re.search(pattern, parsed.fragment, re.IGNORECASE):
                return True

    return False

def shortify(str):
        try:
            return str[:25] + "..."
        except:
            return str + "..."
        
def scrape(url:URL, domain:Domain, media_li:List[Link]) -> tuple[dict[str, Any], list] | None:
    '''
    page_data contains 

    - Title

    - Meta Description 

    - URL, Status code
    
    links = All a tag links in page

    if there is an error return'll be None, []
    '''

    
    try:
        headers = {'User-Agent': UserAgents["1"]}
        response = requests.get(url, headers=headers)
        if 'text/html' not in response.headers.get('Content-Type', ''):
            print(f"Check Manualy: {url}")
            return None, []
    except KeyError:
        print("check UserAgent Dict !!!")
        return None, []
    
    ### handling cert & connection Errors
    except SSLCertVerificationError:
        print("Certificate problem \n use 'response = requests.get(url, headers=headers, verify=False)' (NOT RECOMMENDED)")
        return None, []
    except requests.exceptions.SSLError:
        print("Certificate problem \n use 'response = requests.get(url, headers=headers, verify=False)' (NOT RECOMMENDED)")
        return None, []
    except requests.exceptions.ConnectionError:
        print(f"Failed to Connect")
        return None, []


  
    
    soup = BeautifulSoup(response.text, 'html.parser')

    page_data = {'URL': url, "status": response.status_code}


    page_data.update({
        'Title': soup.title.string.strip() if soup.title.string else '',
        'META Description': soup.find('meta', {'name': 'description'})['content'].strip() if soup.find('meta', {'name': 'description'}) else ''
    })

    links = []

    # Note that some links will be revealed if you preform a certain action for example loggin in as Admin will reveal Admin Dash link 

    for a in soup.find_all('a', href=True):
        link = check_url(urljoin(url, a['href']))
        if (get_domain(link) == domain and '#' not in link):
            links.append(link)

    for media in soup.find_all(src=True):
        link = check_url(urljoin(url, media['src']))
        if (get_domain(link) == domain and not re.search(r"(.svg|.js|.gif|#)",link)): #js and svg files are excluded
            media_li.append(link)

    return page_data, links

async def main():   
    ### arg input handling ###
    parser = argparse.ArgumentParser(description="Silent Snake - A fast and reliable web scraper for gathering server and technology details along with almost all of inside links.",epilog="Example usage: python silent_snake/main.py -u example.com -o n ")
    parser.add_argument('-u', '--url', type=str, help='Target URL to scrape (http/https is optional, default = https)')
    parser.add_argument('-o', '--output', type=str, choices=['Y', 'n', 'y'], default='Y', help='Do you want extra data output? (Y/n)')
    args = parser.parse_args()
    if args.url:
        input_url = args.url
        output = args.output.lower()
    
    ### Interactive input handling ###
    else:
        input_url = input("Enter the URL(http/https is optional , default = https): ")
        output = input("do you want extra data output?(Y/n) ").lower()

    if input_url == "":
            print("???")
            exit(0)
    start_url = check_url(input_url)

    media = []
  
    
    def media_output(media=media,output=output):
        """
        Print discovered media links
        """
        if output == "" or output == "y":
            if len(media) > 0:
                print("Also found: ")
                for m in media:
                    print(m)


    # Handle graceful exit on Ctrl+C
    def exit_gracefully(signum, frame):
        media_output()
        print("\nExiting gracefully...")


        # Perform collective tasks here if needed
        exit(0)
    signal.signal(signal.SIGINT, exit_gracefully)

    

    
    

    ### Get and print details about the server and technologies used ###
    server_obj = server.Server(host=get_domain(start_url).replace("https://","").replace("http://",""))
    ui_frameworks_obj = techs.UiFrameworks()
    
    await asyncio.gather(server_obj.fetch_details(), ui_frameworks_obj.detect(url=start_url))

    print(server_obj)
    print(ui_frameworks_obj)

    domain = get_domain(start_url)
    visited = []
    to_visit = {start_url}
    all_headers = set(['URL', 'Title', 'META Description', 'Status code'])

    
    while len(to_visit) > 0:

        current_url = to_visit.pop()
        visited.append(current_url)

        if is_page(current_url):
            continue

        page_data, links = scrape(current_url, domain, media)
        if page_data:
            all_headers.update(page_data.keys())
            
            if output == "" or output == "y":
                print(f"{current_url}, {shortify(page_data['Title'])}, {shortify(page_data['META Description'])}")
            
                
            for link in links:
                if link not in visited:
                    to_visit.add(link)
    print(f"found : {len(visited)} urls in {domain}")
    print("No more Urls")

    if output == "" or output == "y":
        media_output()
    


if __name__ == "__main__":
    asyncio.run(main())
