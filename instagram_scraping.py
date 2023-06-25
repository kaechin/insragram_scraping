# Ref. https://proxyway.com/guides/how-to-scrape-instagram
# video: https://www.youtube.com/watch?v=SNyQu_FXkqs
# proxy provider: https://proxy2.webshare.io/proxy/list

from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from pprint import pprint
import json
from selenium_stealth import stealth
import csv
import pytesseract
import time

# Define the proxy server to be used
# This cording part is to use "Webshare" proxcy
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

# # This cording part is to use "Bright Data" proxcy
# def prepare_browser():
#     # Set up Chrome options
#     chrome_options = webdriver.ChromeOptions()

#     # Configure the Bright Data proxy
#     proxy = "http://USERNAME:PASSWORD@HOST"
#     chrome_options.add_argument(f'--proxy-server={proxy}')

#     # Other Chrome options
#     chrome_options.add_argument("start-maximized")
#     chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
#     chrome_options.add_experimental_option('useAutomationExtension', False)
    
#     # Start the Chrome driver
#     driver = webdriver.Chrome('PATH OF CHROMEDRIVER')
#     driver.get("https://www.instagram.com/")

#     # Configure stealth options for Selenium
#     # It is for helping to increase the success rate of scraping
#     stealth(driver,
#             user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.53 Safari/537.36',
#             languages=["en-US", "en"],
#             vendor="Google Inc.",
#             platform="Win32",
#             webgl_vendor="Intel Inc.",
#             renderer="Intel Iris OpenGL Engine",
#             fix_hairline=False,
#             run_on_insecure_origins=False
#     )
#     return driver

# Function to parse the scraped user data from Instagram
def parse_data(username, user_data, start_date, end_date):
    post_data = []
    total_likes = 0
    total_comments = 0
    total_interactions = 0
    profile_picture_url = user_data['profile_pic_url']

    edges = user_data['edge_owner_to_timeline_media']['edges']
    for edge in edges:
        captions = []
        post_urls = []
        post_type = []
        post_created_date = None
        post_created_time = None

        # Check if there is a caption for the post
        if len(edge['node']['edge_media_to_caption']['edges']) > 0:
            if edge['node']['edge_media_to_caption']['edges'][0]['node']['text']:
                captions.append(edge['node']['edge_media_to_caption']['edges'][0]['node']['text'])
        post_url = f"https://instagram.com/p/{edge['node']['shortcode']}"
        post_urls.append(post_url)

        # Check the type of the post
        if edge['node']['is_video']:
            post_type.append('Video')
        else:
            post_type.append('Photo')

        created_timestamp = edge['node']['taken_at_timestamp']
        created_datetime = datetime.fromtimestamp(created_timestamp)
        post_created_date = created_datetime.date()
        post_created_time = created_datetime.time()

        # Filter data within the specified date range
        if start_date <= post_created_date <= end_date:
            total_likes += edge['node']['edge_liked_by']['count']
            total_comments += edge['node']['edge_media_to_comment']['count']
            hide_like_and_view_counts = edge['node'].get('hide_like_and_view_counts', False)
            total_interactions = total_likes + total_comments

            # Append the parsed data to the post_data list
            post_data.append({
                'UserName': username,
                'Name': user_data['full_name'],
                'Category': user_data['category_name'],
                'Followers': user_data['edge_followed_by']['count'],
                'Following': user_data['edge_follow']['count'],
                'Post Created Date': post_created_date,
                'Post Created Time': post_created_time,
                'Number of Post': user_data['edge_owner_to_timeline_media']['count'],
                'Total Likes': total_likes,
                'Total Comments': total_comments,
                'Total Interactions': total_interactions,
                'Posts': captions,
                'Post URLs': post_urls[0] if post_urls else '',
                'Type': post_type[0] if post_type else '',
                'Link': f"https://instagram.com/{username}",
                'Like and view counts disabled': hide_like_and_view_counts,
                'Profile Picture URL': profile_picture_url
            })
    return post_data

# Function scrape, which uses Selenium to retrieve user data from Instagram
def scrape(username,start_date, end_date):

    # Construct the URL for the user's Instagram profile
    url = f'https://instagram.com/{username}/?__a=1&__d=dis'

    # Prepare the browser for scraping
    chrome = prepare_browser()

    # Load the URL in the browser
    chrome.get(url)
    print(f"Attempting: {chrome.current_url}")

    # Check if the page redirects to the login page
    if "login" in chrome.current_url:
        print("Failed/ redir to login")
        chrome.quit()
        return None
    else:
        print("Success")
        # Extract the response body (HTML content) from the page
        resp_body = chrome.find_element(By.TAG_NAME, "body").text

        # Parse the response body as JSON
        data_json = json.loads(resp_body)
        print("Answer" + resp_body)

        # Extract the user data from the JSON response
        user_data = data_json.get('graphql', {}).get('user')

        # Check if user data is present in the JSON
        if not user_data:
            print("User data not found in JSON.")
            chrome.quit()
            return None
        
        # Get the total number of posts for the user
        num_posts = user_data['edge_owner_to_timeline_media']['count']

        # Parse the scraped user data within the specified date range
        parsed_data = parse_data(username, user_data, start_date, end_date)
        
        # Close the browser
        chrome.quit()

        # Add a delay of a few seconds before making the next request
        time.sleep(3)

        return parsed_data

def main():
    # Define the "output" dictionary
    output = {}

    usernames = input("Enter the usernames you want to retrieve data for (separated by commas): ").split(",")


    start_date_input = input("Enter the start date in YYYY-MM-DD format: ")
    end_date_input = input("Enter the end date in YYYY-MM-DD format: ")

    start_date = datetime.strptime(start_date_input, "%Y-%m-%d").date()
    end_date = datetime.strptime(end_date_input, "%Y-%m-%d").date()


    # Open a CSV file in write mode
    with open('instagram.csv', 'w', newline='', encoding='utf-8') as csvfile:
        fieldnames = ['UserName', 'Name', 'Category', 'Followers', 'Following', 'Post Created Date',  'Post Created Time', 'Number of Post', 'Total Likes', 'Total Comments', 'Total Interactions', 'Posts', 'Post URLs', 'Type', 'Link', 'Like and view counts disabled', 'Profile Picture URL']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header row
        writer.writeheader()

       # This code snippet is responsible for iterating over each username, scraping the user data, writing the parsed data to the CSV file, 
       # storing the parsed data in the output dictionary, and adding a delay before the next request.
        for username in usernames:
            post_data = scrape(username, start_date, end_date)
            if post_data:
                for data in post_data:
                    writer.writerow(data)
                output[username] = post_data
                time.sleep(3)

    pprint(output)

if __name__ == '__main__':
    main()
