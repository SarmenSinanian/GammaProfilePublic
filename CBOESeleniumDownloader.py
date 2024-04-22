from selenium.webdriver.chrome.service import Service
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.action_chains import ActionChains
import time
import csv
import datetime
import os

download_directory = r'I:/Users/Sarmen/PycharmProjects/HelloWorld1/2022_Programming/backAtIt'
output_directory = 'I:/Users/Sarmen/PycharmProjects/HelloWorld1/2022_Programming/backAtIt/output/'

# Configure Chrome options
chrome_options = Options()
chrome_options.add_experimental_option('prefs', {
    "download.default_directory" : r"I:\Users\Sarmen\PycharmProjects\HelloWorld1\2022_Programming\backAtIt\\",
    'download.prompt_for_download': False,
    'download.directory_upgrade': True,
    'safebrowsing.enabled': True
})

# Function to download data
def download_data(symbol):
#    service = Service('C:\\Users\\Administrator\\Desktop\\Scripts\\chromedriver.exe')
    service = Service('I:\\Users\\Sarmen\\PycharmProjects\\HelloWorld1\\2022_Programming\\backAtIt\\GammaProfile\\chromedriver.exe')
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.get('https://www.cboe.com/delayed_quotes/spx/quote_table')

    text_box = driver.find_element(By.ID, 'textInput_1')
    text_box.clear()
    text_box.send_keys(symbol)
    text_box.send_keys(Keys.ENTER)

    time.sleep(5)  # Adjust the sleep duration based on the file size and download speed

    text_box = driver.find_element(By.ID, 'select_5')
    text_box.clear()
    text_box.send_keys('All')
    text_box.send_keys(Keys.ENTER)

    text_box = driver.find_element(By.ID, 'select_7')
    text_box.clear()
    text_box.send_keys('All')
    text_box.send_keys(Keys.ENTER)

    button = driver.find_element(By.XPATH, '//*[@id="root"]/div/div/div[2]/div[2]/div[2]/div[2]/div[5]/div/button/span')
    button.click()

    # Wait for the download to complete (assuming it takes a few seconds)
    time.sleep(10)  # Adjust the sleep duration based on the file size and download speed
    body_element = driver.find_element(By.TAG_NAME, 'body')
    body_element.send_keys(Keys.END)

    for _ in range(8):
        body_element.send_keys(Keys.ARROW_UP)

    # Simulate clicking on the body
    actions = ActionChains(driver)
    actions.move_to_element(body_element).click().perform()

    # Find all div elements with the specified class name
    div_elements = driver.find_elements(By.XPATH, '//*[@id="root"]/div/div/div[2]/div[2]/div[3]/div')

    # Find the index of the last div element
    last_div_index = len(div_elements)

    # Construct the XPath expression using the last div index
    link_xpath = '//*[@id="root"]/div/div/div[2]/div[2]/div[3]/div[{}]/a'.format(last_div_index)

    # Find the link element using the dynamic XPath expression
    link = driver.find_element(By.XPATH, link_xpath)
    link.click()

    time.sleep(2)  # Adjust the sleep duration based on the file size and download speed

    # Close the WebDriver
    driver.quit()

# Function to rename files
def rename_files(folder_path, file_pattern, output_directory):
    # Get the list of files in the folder
    files = []
    for file_name in os.listdir(folder_path):
        if file_pattern in file_name:
            files.append(os.path.join(folder_path, file_name))

    # Process each file
    for file_path in files:
        # Split the file path
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        base_name_parts = base_name.split('_')

        # Get the word to replace "data" in the filename template
        word = base_name_parts[0]

        # Read the CSV file
        with open(file_path, 'r') as file:
            reader = csv.reader(file)

            # Skip the first two rows to reach the third row
            for _ in range(2):
                next(reader)

            # Get the content of the third cell in column A
            row = next(reader)
            cell_content = row[0]  # Assuming column A is the first column (index 0)

        # Extract the date string from the cell content
        date_string_start = 'Date: '
        date_start_index = cell_content.find(date_string_start) + len(date_string_start)
        date_string = cell_content[date_start_index:]

        # Extract the date part from the date string
        date_parts = date_string.split(' ')[0:3]  # Extract the first three parts: Month, Day, Year
        formatted_date_string = ' '.join(date_parts)

        # Parse the date string into a datetime object
        date_value = datetime.datetime.strptime(formatted_date_string, '%B %d, %Y')

        # Extract year, month, and day from the date value
        year = date_value.year
        month = str(date_value.month).zfill(2)
        day = date_value.day

        # Generate the file name using the template and dynamic values
        filename_template = "{word}_{year}_{month}_{day}.csv"
        new_filename = filename_template.format(word=word, year=year, month=month, day=day)

        # Check if the new file name already exists in the output folder
        file_index = 1
        while os.path.exists(os.path.join(output_directory, new_filename)):
            # Append a numerical value between parentheses to account for duplicates
            new_filename = "{word}_{year}_{month}_{day} ({index}).csv".format(
                word=word, year=year, month=month, day=day, index=file_index
            )
            file_index += 1

        # Rename the file
        old_filepath = file_path
        new_filepath = os.path.join(output_directory, new_filename)
        os.rename(old_filepath, new_filepath)

        # Output the new file name
        print(f"File renamed to: {new_filename}")

# Download data for 'SPX'
download_data('SPX')

# Rename files
rename_files(download_directory, 'quotedata', output_directory)

# Download data for 'NVDA'
#download_data('NVDA')

# Rename files
#rename_files(download_directory, 'quotedata', output_directory)

# Download data for 'TTD'
#download_data('AMD')

# Rename files
#rename_files(download_directory, 'quotedata', output_directory)
