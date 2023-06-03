# Ref. https://proxyway.com/guides/how-to-scrape-instagram
# video: https://www.youtube.com/watch?v=SNyQu_FXkqs
# proxy provider: https://proxy2.webshare.io/proxy/list

from selenium import webdriver
from selenium.webdriver.common.by import By
from pprint import pprint
import json
from selenium_stealth import stealth
import csv

# Define the proxy server to be used
proxy = "http://USERNAME:PASSWORD@proxy_server:PORTNUMBER"
proxy = "server:port"
output = {}

#Funtion to prepare the browser fot scraping
def prepare_browser():

    # Set up Chrome options
    chrome_options = webdriver.ChromeOptions()
    proxy = "server:port"
    chrome_options.add_argument(f'--proxy-server={proxy}')
    chrome_options.add_argument("start-maximized")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    # Start the Chrome driver
    driver = webdriver.Chrome('PATH OF CHROMEDRIVER')
    driver.get("https://www.instagram.com/")

    # Configure stealth options for Selenium
    # It is for helping to increase the success rate of scraping
    stealth(driver,
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36',
            languages=["en-US", "en"],
            vendor="Google Inc.",
            platform="Win32",
            webgl_vendor="Intel Inc.",
            renderer="Intel Iris OpenGL Engine",
            fix_hairline=False,
            run_on_insecure_origins=False,
            )
    return driver

# Function to parse the scraped user data
def parse_data(username, user_data):
    captions = []
    post_urls = []
    if len(user_data['edge_owner_to_timeline_media']['edges']) > 0:
        latest_node = user_data['edge_owner_to_timeline_media']['edges'][0]
        if len(latest_node['node']['edge_media_to_caption']['edges']) > 0:
            if latest_node['node']['edge_media_to_caption']['edges'][0]['node']['text']:
                captions.append(latest_node['node']['edge_media_to_caption']['edges'][0]['node']['text'])
        post_url = f"https://instagram.com/p/{latest_node['node']['shortcode']}"
        print(f"Post URL: {post_url}")
        post_urls.append(post_url)

    user_output = {
        'UserName': username,
        'Name': user_data['full_name'],
        'Category': user_data['category_name'],
        'Followers': user_data['edge_followed_by']['count'],
        'Following': user_data['edge_follow']['count'],
        'Number of Post': user_data['edge_owner_to_timeline_media']['count'],
        'Posts': captions,
        #'Post URLs': post_urls,
        # Change the data type from list to string
        'Post URLs': post_urls[0] if post_urls else '',
        'Link': f"https://instagram.com/{username}",
    }
    print(f"user_output: {user_output}")
    return user_output

# Function to scrape user data from
def scrape(username):
    url = f'https://instagram.com/{username}/?__a=1&__d=dis'
    chrome = prepare_browser()
    chrome.get(url)
    print(f"Attempting: {chrome.current_url}")
    if "login" in chrome.current_url:
        print("Failed/ redir to login")
        chrome.quit()
        return None
    else:
        print("Success")
        resp_body = chrome.find_element(By.TAG_NAME, "body").text
        data_json = json.loads(resp_body)
        user_data = data_json['graphql']['user']
        num_posts = user_data['edge_owner_to_timeline_media']['count']
        parsed_data = parse_data(username, user_data)
        chrome.quit()
        return parsed_data

def main():
    # Open a CSV file in write mode
    with open('instagram.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['UserName', 'Name', 'Category', 'Followers', 'Following', 'Number of Post', 'Posts', 'Post URLs', 'Link']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

        # It is possible to add more users, but to do test easily, I added just 2 users
        usernames = ["tibber", "posteninnovasjonshub"]

        for username in usernames:
            user_data = scrape(username)
            if user_data:
                # It is possible to change following way to change the data type from list to string
                # user_data['Post URLs'] = '\n'.join(user_data['Post URLs'])
                writer.writerow(user_data)
                output[username] = user_data

if __name__ == '__main__':
    main()
    pprint(output)