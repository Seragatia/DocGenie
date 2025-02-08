from selenium import webdriver
from selenium.webdriver.common.by import By
import time

def extract_video_url(website_url):
    driver = webdriver.Chrome()  # Ensure you have ChromeDriver installed
    driver.get(website_url)
    time.sleep(5)  # Wait for the page to load

    videos = driver.find_elements(By.TAG_NAME, "video")
    video_urls = [video.get_attribute("src") for video in videos]

    driver.quit()
    return video_urls
