# from faker import Faker

# fake = Faker()

# for i in range(10):
#     random_name = fake.name()
#     print(random_name)
import time
import threading
import pandas as pd
import requests
from GPMLoginAPI import GPMLoginAPI
from selenium.webdriver.chrome import service
from selenium.webdriver.chrome.options import Options
from UndetectChromeDriver import UndetectChromeDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from screeninfo import get_monitors

api = GPMLoginAPI('http://127.0.0.1:19995')

initial_run_iteration = 1  # Initial run iteration
number_of_profiles = int(input('Nhập số luồng chạy profile : '))

# Read the Excel file
df = pd.read_excel('E:\Downloads\GPMLoginApiV2-main\python\mail.xlsx')

# Get screen resolution dynamically
monitor = get_monitors()[0]  # Assuming a single monitor setup; adjust if multiple monitors are used
screen_width = monitor.width
screen_height = monitor.height
columns = 4
rows = 3
window_width = screen_width // columns
window_height = screen_height // rows

def create_profile(profile_number):
    profile_name = f"addcard{profile_number}"
    proxy = 'p.webshare.io:80:romauto1234-rotate:romauto1234'

    print(f'CREATE PROFILE {profile_name}------------------')
    createdResult = api.Create(profile_name, proxy)
    createdProfileId = None
    if createdResult is not None:
        status = bool(createdResult['status'])
        if status:
            createdProfileId = str(createdResult['profile_id'])
    print(f"Created profile ID {profile_name}: {createdProfileId}")

    return createdProfileId

def position_window(driver, x, y, width, height):
    driver.set_window_position(x, y)
    driver.set_window_size(width, height)

def run_profile(profile_number):
    createdProfileId = create_profile(profile_number)
    if createdProfileId:
        print(f'START PROFILE addcard{profile_number}------------------')
        startedResult = api.Start(createdProfileId)
        if startedResult is not None:
            status = bool(startedResult['status'])
            if status:
                seleniumRemoteDebugAddress = str(startedResult["selenium_remote_debug_address"])
                gpmDriverPath = str(startedResult["selenium_driver_location"])

                try:
                    # Init selenium
                    options = Options()
                    options.debugger_address = seleniumRemoteDebugAddress
                    myService = service.Service(gpmDriverPath)
                    driver = UndetectChromeDriver(service=myService, options=options)
                    driver.GetByGpm("https://www.amazon.com/ap/signin?openid.pape.max_auth_age=0&openid.return_to=https%3A%2F%2Fkdp.amazon.com%2Fbookshelf&openid.identity=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&openid.assoc_handle=amzn_dtp&openid.mode=checkid_setup&language=en_US&openid.claimed_id=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0%2Fidentifier_select&pageId=kdp-ap&openid.ns=http%3A%2F%2Fspecs.openid.net%2Fauth%2F2.0")

                    # Calculate the window position based on profile_number
                    col = (profile_number - 1) % columns
                    row = (profile_number - 1) // columns
                    x = col * window_width
                    y = row * window_height

                    # Position the window
                    position_window(driver, x, y, window_width, window_height)

                    retries = 5
                    for attempt in range(retries):
                        try:
                            # Wait for the email input element to be present
                            wait = WebDriverWait(driver, 10)
                            email_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="ap_email"]')))
                            break
                        except Exception as e:
                            if attempt < retries - 1:
                                print(f"Retry {attempt + 1} - Email input not found, reloading...")
                                driver.refresh()
                                time.sleep(3)
                            else:
                                raise e

                    email = df.iloc[profile_number - 1]['email']
                    password = df.iloc[profile_number - 1]['password']
                    code_2fa = df.iloc[profile_number - 1]['2fa']
                    driver.execute_script("arguments[0].value = arguments[1];", email_input, email)
                    time.sleep(2)
                    # Wait for the password input element to be present
                    password_input = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="ap_password"]')))
                    driver.execute_script("arguments[0].value = arguments[1];", password_input, password)
                    time.sleep(2)
                    # Wait for the sign-in submit button to be present
                    sign_in_button = wait.until(EC.presence_of_element_located((By.XPATH, '//input[@id="signInSubmit"]')))
                    driver.execute_script("arguments[0].click();", sign_in_button)
                    
                    time.sleep(30)

                except Exception as e:
                    print(f"Error in thread addcard{profile_number}: {e}")
                finally:
                    try:
                        driver.close()
                        driver.quit()
                    except Exception as e:
                        print(f"Error closing driver in thread addcard{profile_number}: {e}")

        print(f'CLOSE PROFILE addcard{profile_number}------------------')
    print('DELETE PROFILE ------------------')
    api.Delete(createdProfileId)
    print(f"Deleted: {createdProfileId}")

def run_profiles_indefinitely():
    iteration = initial_run_iteration
    while True:
        threads = []
        profile_numbers = list(range((iteration - 1) * number_of_profiles + 1, iteration * number_of_profiles + 1))
        for profile_number in profile_numbers:
            t = threading.Thread(target=run_profile, args=(profile_number,))
            threads.append(t)
            t.start()

        # Wait for all threads to complete
        for t in threads:
            t.join()

        print('Đang tạo luồng mới ...')
        iteration += 1

if __name__ == "__main__":
    try:
        run_profiles_indefinitely()
    except KeyboardInterrupt:
        print('Process interrupted by user. Exiting...')