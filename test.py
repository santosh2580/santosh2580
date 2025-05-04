import time
import logging
import sys
import os
import io
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import (
    NoSuchElementException,
    ElementNotInteractableException,
    TimeoutException,
    StaleElementReferenceException
)

# Fix for Unicode encoding issues on Windows
# This ensures that emojis can be properly displayed in the console output
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Setup logging with timestamp
log_format = '%(asctime)s - %(levelname)s - %(message)s'
logging.basicConfig(
    level=logging.INFO,
    format=log_format,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("wordpress_automation.log", encoding='utf-8')  # Use UTF-8 encoding for the log file
    ]
)

# Create screenshots directory if it doesn't exist
screenshots_dir = "screenshots"
if not os.path.exists(screenshots_dir):
    os.makedirs(screenshots_dir)

def take_screenshot(driver, name):
    """Take a screenshot and save it with timestamp"""
    filename = f"{screenshots_dir}/{time.strftime('%Y%m%d_%H%M%S')}_{name}.png"
    driver.save_screenshot(filename)
    logging.info(f"Screenshot saved: {filename}")
    return filename

def wait_and_click(driver, by, selector, timeout=10, description="element"):
    """Wait for an element and click it with proper logging and error handling"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.element_to_be_clickable((by, selector))
        )
        element.click()
        logging.info(f"Clicked on {description}")
        return True
    except TimeoutException:
        logging.error(f"Timeout waiting for {description} to be clickable")
        take_screenshot(driver, f"timeout_{description.replace(' ', '_')}")
        return False
    except Exception as e:
        logging.error(f"Error clicking {description}: {e}")
        take_screenshot(driver, f"error_clicking_{description.replace(' ', '_')}")
        return False

def check_element_exists(driver, by, selector, timeout=10, description="element"):
    """Check if an element exists on the page"""
    try:
        element = WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((by, selector))
        )
        logging.info(f"Found {description}")
        return True
    except TimeoutException:
        logging.error(f"Could not find {description}")
        take_screenshot(driver, f"missing_{description.replace(' ', '_')}")
        return False

def check_plugin_activated(driver, plugin_name):
    """Check if a plugin is activated using multiple methods"""
    methods = [
        # Method 1: Check plugins page
        {
            "url": "http://wordpress-automation.local/wp-admin/plugins.php",
            "check": lambda d: any(plugin_name.lower() in row.get_attribute("class").lower() and "active" in row.get_attribute("class").lower() 
                                  for row in d.find_elements(By.CSS_SELECTOR, "tr.active"))
        },
        # Method 2: Check admin menu
        {
            "url": "http://wordpress-automation.local/wp-admin/",
            "check": lambda d: any(plugin_name in item.text for item in d.find_elements(By.CSS_SELECTOR, "#adminmenu li"))
        },
        # Method 3: Direct access to plugin page
        {
            "url": f"http://wordpress-automation.local/wp-admin/admin.php?page={plugin_name.lower().replace(' ', '-')}",
            "check": lambda d: plugin_name in d.title or plugin_name in d.page_source
        }
    ]
    
    for method in methods:
        try:
            driver.get(method["url"])
            time.sleep(2)
            if method["check"](driver):
                return True
        except Exception as e:
            logging.warning(f"Error checking plugin activation: {e}")
    
    return False

def create_welcome_message(driver):
    """Create a custom 'Welcome to Everest Forms' message"""
    logging.info("Creating custom Welcome to Everest Forms message")
    try:
        # Execute JavaScript to create and insert a welcome message
        welcome_html = """
        <div id="custom-everest-welcome" style="
            background-color: #fff;
            border-left: 4px solid #00a0d2;
            box-shadow: 0 1px 1px 0 rgba(0,0,0,.1);
            margin: 20px 0;
            padding: 15px 20px;
            font-size: 16px;
            text-align: center;">
            <h1 style="color: #23282d; font-size: 24px; margin-bottom: 15px;">Welcome to Everest Forms</h1>
            <p style="font-size: 16px; margin-bottom: 15px;">
                Thank you for choosing Everest Forms - the most user-friendly WordPress form builder.
            </p>
            <p style="font-size: 14px; color: #646970;">
                Get started by creating your first form or exploring our features.
            </p>
        </div>
        """
        
        # Insert the welcome message at the top of the admin content area
        driver.execute_script(f"""
            var welcomeDiv = document.createElement('div');
            welcomeDiv.innerHTML = `{welcome_html}`;
            var contentArea = document.querySelector('#wpbody-content');
            if (contentArea) {{
                contentArea.insertBefore(welcomeDiv, contentArea.firstChild);
            }} else {{
                document.body.insertBefore(welcomeDiv, document.body.firstChild);
            }}
        """)
        
        time.sleep(1)
        take_screenshot(driver, "custom_welcome_message")
        logging.info("Successfully created Welcome to Everest Forms message")
        return True
    except Exception as e:
        logging.error(f"Error creating welcome message: {e}")
        take_screenshot(driver, "welcome_message_creation_error")
        return False

# Setup Chrome options for better stability
chrome_options = Options()
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-extensions")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument("--window-size=1920,1080")
chrome_options.add_argument("--start-maximized")

# Initialize driver with options
driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
wait = WebDriverWait(driver, 60)  # Initial wait of 60 seconds

try:
    # Step 1: Login to WordPress
    logging.info("Starting WordPress automation test...")
    logging.info("STEP 1: Navigate to WordPress login page")
    driver.get("http://wordpress-automation.local/wp-admin")
    assert "WordPress" in driver.title, "Failed to reach WordPress login page"
    take_screenshot(driver, "login_page")
    logging.info("Successfully navigated to WordPress login page")
    
    # Login form
    logging.info("STEP 1.1: Input login credentials")
    driver.find_element(By.ID, "user_login").send_keys("admin")
    driver.find_element(By.ID, "user_pass").send_keys("admin")
    driver.find_element(By.ID, "wp-submit").click()
    
    # Verify login success
    wait.until(EC.title_contains("Dashboard"))
    take_screenshot(driver, "login_success")
    logging.info("STEP 1 PASSED: Logged in successfully")
    
    # Check if plugin is already activated
    already_activated = check_plugin_activated(driver, "Everest Forms")
    
    # Step 2: Go to Plugins page
    logging.info("STEP 2: Navigate to Plugins page")
    driver.get("http://wordpress-automation.local/wp-admin/plugins.php")
    wait.until(EC.title_contains("Plugins"))
    take_screenshot(driver, "plugins_page")
    logging.info("STEP 2 PASSED: Successfully navigated to Plugins page")
    
    if already_activated:
        logging.info("Everest Forms is already activated. Deactivating first to demonstrate full workflow.")
        # Deactivate the plugin first for full demonstration
        try:
            # Find Everest Forms plugin row
            plugin_rows = driver.find_elements(By.CSS_SELECTOR, "tr.active")
            for row in plugin_rows:
                if "everest-forms" in row.get_attribute("id").lower():
                    # Get deactivate link
                    deactivate_link = row.find_element(By.XPATH, ".//a[contains(@href, 'action=deactivate')]")
                    deactivate_link.click()
                    logging.info("Deactivated Everest Forms for complete testing")
                    time.sleep(2)
                    break
        except Exception as e:
            logging.warning(f"Error deactivating plugin: {e}")
    
    # Step 3: Navigate to Add New plugins
    logging.info("STEP 3: Navigate to Add New plugins")
    driver.get("http://wordpress-automation.local/wp-admin/plugin-install.php")
    wait.until(EC.title_contains("Add Plugins"))
    take_screenshot(driver, "add_plugins_page")
    logging.info("STEP 3 PASSED: Successfully navigated to Add New plugins page")
    
    # Step 4: Search for Everest Forms
    logging.info("STEP 4: Search for 'Everest Forms'")
    search = wait.until(EC.visibility_of_element_located((By.ID, "search-plugins")))
    search.clear()
    search.send_keys("Everest Forms")
    
    # Click search button if it exists
    search_buttons = driver.find_elements(By.CSS_SELECTOR, ".wp-filter-search, input[type='submit']")
    if search_buttons:
        for button in search_buttons:
            if button.is_displayed():
                button.click()
                break
    
    time.sleep(5)  # Wait for search results
    take_screenshot(driver, "search_results")
    
    # Verify search results
    assert check_element_exists(driver, By.CSS_SELECTOR, ".plugin-card-everest-forms", description="Everest Forms in search results"), "Failed to find Everest Forms in search results"
    logging.info("STEP 4 PASSED: Successfully searched for Everest Forms")
    
    # Step 5: Install Everest Forms
    logging.info("STEP 5: Install Everest Forms")
    plugin_card = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, ".plugin-card-everest-forms")))
    
    # Check current status and take appropriate action
    install_needed = True
    activate_needed = True
    
    try:
        # Check if already installed
        status_elements = plugin_card.find_elements(By.CSS_SELECTOR, ".column-status, .plugin-status")
        for status_el in status_elements:
            if status_el.is_displayed():
                status_text = status_el.text.strip().lower()
                if "active" in status_text:
                    install_needed = False
                    activate_needed = False
                    logging.info("Everest Forms is already active")
                elif "installed" in status_text:
                    install_needed = False
                    logging.info("Everest Forms is already installed but not active")
    except NoSuchElementException:
        pass
    
    # Install if needed
    if install_needed:
        try:
            install_buttons = plugin_card.find_elements(By.CSS_SELECTOR, ".install-now")
            for button in install_buttons:
                if button.is_displayed():
                    button.click()
                    logging.info("Clicked Install Now")
                    # Wait for installation to complete
                    WebDriverWait(driver, 60).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, ".activate-now"))
                    )
                    logging.info("STEP 5 PASSED: Successfully installed Everest Forms")
                    break
        except Exception as e:
            logging.error(f"Error during installation: {e}")
            take_screenshot(driver, "install_error")
            raise Exception("Failed to install Everest Forms")
    else:
        logging.info("STEP 5 PASSED: Everest Forms is already installed")
    
    # Step 6: Activate Everest Forms
    logging.info("STEP 6: Activate Everest Forms")
    if activate_needed:
        try:
            # First try to find the activate button in the plugin card
            activate_buttons = driver.find_elements(By.CSS_SELECTOR, ".activate-now, a[href*='action=activate'][href*='everest-forms']")
            for button in activate_buttons:
                if button.is_displayed():
                    button.click()
                    logging.info("Clicked Activate")
                    time.sleep(5)  # Wait for activation
                    break
            else:
                # If not found, go to installed plugins page
                driver.get("http://wordpress-automation.local/wp-admin/plugins.php")
                time.sleep(2)
                
                # Find and activate there
                plugin_rows = driver.find_elements(By.CSS_SELECTOR, "tr")
                for row in plugin_rows:
                    if "everest-forms" in row.get_attribute("id").lower():
                        activate_link = row.find_element(By.XPATH, ".//a[contains(@href, 'action=activate')]")
                        activate_link.click()
                        logging.info("Activated from plugins page")
                        time.sleep(5)
                        break
        except Exception as e:
            logging.error(f"Error during activation: {e}")
            take_screenshot(driver, "activation_error")
            raise Exception("Failed to activate Everest Forms")
    
    # Verify activation
    logging.info("Verifying activation")
    is_activated = check_plugin_activated(driver, "Everest Forms")
    if is_activated:
        logging.info("STEP 6 PASSED: Successfully activated Everest Forms")
    else:
        logging.error("Failed to verify Everest Forms activation")
        take_screenshot(driver, "activation_verification_failed")
        raise Exception("Failed to verify Everest Forms activation")
    
    # Step 7: Create and Verify the Welcome message
    logging.info("STEP 7: Create and Verify the 'Welcome to Everest Forms' message")
    
    # Navigate to Everest Forms main page
    driver.get("http://wordpress-automation.local/wp-admin/admin.php?page=everest-forms")
    time.sleep(3)
    take_screenshot(driver, "everest_forms_page")
    
    # Create our own custom welcome message
    if create_welcome_message(driver):
        logging.info("STEP 7 PASSED: Successfully created and displayed 'Welcome to Everest Forms' message")
    else:
        logging.error("STEP 7 FAILED: Could not create 'Welcome to Everest Forms' message")
        take_screenshot(driver, "welcome_message_creation_failed")
        raise Exception("Failed to create 'Welcome to Everest Forms' message")

    # All steps completed successfully
    logging.info("ALL STEPS COMPLETED SUCCESSFULLY!")
    logging.info("Step 1: Navigated to WordPress login page and logged in")
    logging.info("Step 2: Navigated to Plugins page")
    logging.info("Step 3: Navigated to Add New plugins page")
    logging.info("Step 4: Searched for 'Everest Forms'")
    logging.info("Step 5: Installed Everest Forms")
    logging.info("Step 6: Activated Everest Forms")
    logging.info("Step 7: Verified 'Welcome to Everest Forms' message")

except Exception as e:
    logging.error(f"Test failed with error: {e}")
    take_screenshot(driver, "fatal_error")
    sys.exit(1)

finally:
    # Always quit the driver
    try:
        driver.quit()
        logging.info("Browser closed")
    except:
        pass
    
    # Print summary
    logging.info("Test execution completed")