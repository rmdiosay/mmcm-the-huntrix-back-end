from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from src.entities.schemas import PropertyResult, ScrapeRequest
from fastapi import HTTPException
import time


def scrape_facebook_marketplace(params: ScrapeRequest, email: str, password: str):
    options = webdriver.ChromeOptions()
    # Debug mode: comment this line to see the browser
    # options.add_argument("--headless=new")
    options.add_argument("--disable-blink-features=AutomationControlled")

    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()), options=options
    )
    wait = WebDriverWait(driver, 15)

    try:
        driver.get("https://www.facebook.com/login")
        wait.until(EC.presence_of_element_located((By.NAME, "email"))).send_keys(email)
        driver.find_element(By.NAME, "pass").send_keys(password)
        driver.find_element(By.NAME, "login").click()
        time.sleep(5)

        # Detect login issues
        current_url = driver.current_url
        if "login" in current_url:
            raise HTTPException(
                status_code=401,
                detail="Invalid credentials: email or password incorrect.",
            )
        if "checkpoint" in current_url:
            raise HTTPException(
                status_code=403,
                detail="Login blocked: checkpoint, captcha, or 2FA required.",
            )

        # Check Marketplace link
        # try:
        #     wait.until(
        #         EC.presence_of_element_located(
        #             (By.CSS_SELECTOR, "a[aria-label='Marketplace']")
        #         )
        #     )
        # except Exception:
        #     try:
        #         wait.until(
        #             EC.presence_of_element_located(
        #                 (By.XPATH, "//a[contains(@href, '/marketplace/')]")
        #             )
        #         )
        #     except Exception:
        #         raise HTTPException(
        #             status_code=404,
        #             detail="Marketplace not available for this account or region.",
        #         )

        # --- Go to marketplace search ---
        url = (
            f"https://www.facebook.com/marketplace/{params.location}/search?"
            f"query={params.query}&minPrice={params.min_price}&maxPrice={params.max_price}"
        )
        print("Navigating to:", url)
        time.sleep(15)
        driver.get(url)

        # wait for items to appear
        wait.until(
            EC.presence_of_all_elements_located(
                (By.CSS_SELECTOR, "a[href*='/marketplace/item/']")
            )
        )

        results = []
        listings = driver.find_elements(
            By.CSS_SELECTOR, "a[href*='/marketplace/item/']"
        )

        for listing in listings[:10]:  # limit results
            try:
                title_elem = listing.find_element(By.CSS_SELECTOR, "span[dir='auto']")
                price_elem = listing.find_element(By.CSS_SELECTOR, "span[dir='ltr']")

                title = title_elem.text.strip() if title_elem else "Untitled"
                price = price_elem.text.strip() if price_elem else "N/A"
                href = listing.get_attribute("href")

                results.append(
                    PropertyResult(
                        title=title,
                        price=price,
                        location=params.location or "Unknown",
                        url=href,
                    )
                )
            except Exception:
                continue  # skip broken listings

        return results

    finally:
        driver.quit()
