import pyautogui
import time

def record_screen(duration, output_folder):
    for i in range(duration):
        screenshot = pyautogui.screenshot()
        screenshot.save(f"{output_folder}/screenshot_{i}.png")
        time.sleep(1)
