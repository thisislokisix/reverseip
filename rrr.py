import requests
import re
import os
import time
from multiprocessing import Pool, Manager
from colorama import Fore, Style, init
from fake_useragent import UserAgent

init(autoreset=True)

ua = UserAgent()

def fetch_content(url):
    """Fetch the content of a URL with a random User-Agent."""
    headers = {
        'User-Agent': ua.random  # Generate a random User-Agent for each request
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.text
    except requests.exceptions.RequestException as e:
        print(f'{Fore.RED}Error fetching {url}: {e}{Style.RESET_ALL}')
        return None

def get_domains_from_ip(ip, output_file, lock):
    """Get all domains for a given IP by handling pagination."""
    domain_list = []
    page = 1

    while True:
        url = f'https://rapiddns.io/sameip/{ip}?page={page}'
        response = fetch_content(url)
        if not response:
            time.sleep(5)  # Wait before retrying
            continue

        results = re.findall(r'<tr>\s*<th[^>]*>\d+</th>\s*<td>([^<]+)</td>', response)
        
        num_results = len(results)

        if num_results == 0:
            break

        for domain in results:
            domain = domain.strip()
            if domain.startswith('www.'):
                domain = domain[4:]  # Remove 'www.' prefix
            if domain not in domain_list:
                domain_list.append(domain)
              
        page += 1
        time.sleep(25)  # DEFAULT 25 ITS SAFE

    with lock:
        with open(output_file, 'a+') as file:
            for domain in domain_list:
                file.write(f'{domain}\n')

    status = 'Failed' if len(domain_list) == 0 else len(domain_list)
    color = Fore.GREEN if len(domain_list) > 0 else Fore.RED
    print(f'{color}[#] Reversed {Fore.MAGENTA}{ip}{Style.RESET_ALL} {color}=>{Style.RESET_ALL} {Fore.YELLOW}{status}{Style.RESET_ALL} {color}domains [#]{Style.RESET_ALL}')

def main():
  
    input_file = input("Enter the name of the file containing IP addresses (e.g., list.txt): ").strip()
    
    if not os.path.exists(input_file):
        print(f'{Fore.RED}Error: The file "{input_file}" does not exist.{Style.RESET_ALL}')
        return
      
    with open(input_file, "r") as file:
        ips = [line.strip() for line in file if line.strip()]
    
    output_file = input("Enter the name of the output file to save results (e.g., results.txt): ").strip()
    
    if os.path.exists(output_file):
        open(output_file, 'w').close()
    
    manager = Manager()
    lock = manager.Lock()
  
    with Pool() as pool:
        # Map the function to the list of IPs
        pool.starmap(get_domains_from_ip, [(ip, output_file, lock) for ip in ips])

    print(f'{Fore.GREEN}Reverse IP lookup completed. Results saved to {output_file}.{Style.RESET_ALL}')

if __name__ == "__main__":
    main()
