import asyncio
import random
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright
from faker import Faker
import nest_asyncio

nest_asyncio.apply()

# Flag to indicate whether the script is running
running = True

# Semaphore to limit concurrent browser launches
MAX_CONCURRENT_BROWSERS = 30
semaphore = asyncio.Semaphore(MAX_CONCURRENT_BROWSERS)

# Faker instance for generating names
faker = Faker('en_IN')

# Hardcoded password
HARDCODED_PASSWORD = "Fly@1234"

# Verify password function
def verify_password(password):
    return password == HARDCODED_PASSWORD

# Generate a unique user name
def generate_unique_user():
    return f"{faker.first_name()} {faker.last_name()}"

async def start(wait_time, meetingcode, passcode, browser):
    global running

    async with semaphore:
        try:
            # Generate unique user name
            user = generate_unique_user()
            print(f"{user} attempting to join with Chromium.")

            # Create a new context and page
            context = await browser.new_context()
            page = await context.new_page()

            try:
                await page.goto(f'http://app.zoom.us/wc/join/{meetingcode}', timeout=200000)

                # Simulate user media
                for _ in range(5):
                    await page.evaluate('() => { navigator.mediaDevices.getUserMedia({ audio: true, video: true }); }')

                # Accept cookies if prompt appears
                try:
                    await page.click('//button[@id="onetrust-accept-btn-handler"]', timeout=5000)
                except Exception:
                    pass

                # Accept agreement if prompt appears
                try:
                    await page.click('//button[@id="wc_agree1"]', timeout=5000)
                except Exception:
                    pass

                # Fill meeting details
                await page.wait_for_selector('input[type="text"]', timeout=200000)
                await page.fill('input[type="text"]', user)

                password_field_exists = await page.query_selector('input[type="password"]')
                if password_field_exists:
                    await page.fill('input[type="password"]', passcode)

                join_button = await page.wait_for_selector('button.preview-join-button', timeout=200000)
                await join_button.click()

                # Attempt to join audio
                retry_count = 5
                while retry_count > 0:
                    try:
                        await page.wait_for_selector('button.join-audio-by-voip__join-btn', timeout=300000)
                        query = 'button[class*="join-audio-by-voip__join-btn"]'
                        mic_button_locator = await page.query_selector(query)
                        await asyncio.sleep(2)
                        await mic_button_locator.evaluate_handle('node => node.click()')
                        print(f"{user} successfully joined audio.")
                        break
                    except Exception as e:
                        print(f"Attempt {5 - retry_count + 1}: {user} failed to join audio. Retrying...", e)
                        retry_count -= 1
                        await asyncio.sleep(2)

                if retry_count == 0:
                    print(f"{user} failed to join audio after multiple attempts.")

                # Stay in the meeting
                print(f"{user} will remain in the meeting for {wait_time} seconds ...")
                while running and wait_time > 0:
                    await asyncio.sleep(1)
                    wait_time -= 1
                print(f"{user} has left the meeting.")
            finally:
                await page.close()
                await context.close()

        except Exception as e:
            print(f"An error occurred for {user}: {e}")

async def main():
    global running

    # Configuration
    password = "Fly@1234"
    number = 30
    meetingcode = "82770760919"
    passcode = "468111"
    wait_time = 7200  # Fixed wait time

    if not verify_password(password):
        print("Wrong password. GET LOST.")
        return

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                    '--use-fake-ui-for-media-stream',
                    '--use-fake-device-for-media-stream'
                ]
            )

            tasks = []
            for _ in range(number):
                tasks.append(start(wait_time, meetingcode, passcode, browser))

            try:
                await asyncio.gather(*tasks, return_exceptions=True)
            except KeyboardInterrupt:
                running = False
                await asyncio.gather(*tasks, return_exceptions=True)
            finally:
                await browser.close()

    except KeyboardInterrupt:
        running = False
        print("Script interrupted by user.")

if __name__ == "__main__":
    asyncio.run(main())
