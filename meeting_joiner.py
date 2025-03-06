import asyncio
from playwright.async_api import async_playwright
import nest_asyncio
import os
import indian_names
import base64

# Apply nest_asyncio to fix event loop issues in Jupyter/Colab
nest_asyncio.apply()

# Initialize indian_names to generate random Indian names
def generate_random_name():
    return indian_names.get_full_name()

# Function to join the meeting after navigation
async def join_meeting_after_navigation(page):
    try:
        # Wait for the name input field
        await page.wait_for_selector('input[type="text"]', timeout=60000)

        # Generate a random Indian name using indian_names library
        random_name = generate_random_name()

        # Enter the name
        await page.fill('input[type="text"]', random_name)

        # Check for password field
        password_field = await page.query_selector('input[type="password"]')
        if password_field:
            await page.fill('input[type="password"]', "your_passcode_here")  # Replace with actual passcode
            await page.wait_for_selector('button.preview-join-button', timeout=60000)
            await page.click('button.preview-join-button')
        else:
            await page.wait_for_selector('button.preview-join-button', timeout=60000)
            await page.click('button.preview-join-button')

        # Print once after joining the meeting
        print(f"✅ {random_name} has joined the meeting. The meeting will last for 7200 seconds.")

        # Keep the meeting open for 7200 seconds (2 hours)
        await asyncio.sleep(7200)  # 7200 seconds = 2 hours
        print(f"⏰ {random_name} stayed in the meeting for 7200 seconds.")

    except Exception as e:
        print(f"❌ Error: {e}")  # Print errors for debugging

# Function to open the browser and join the meeting
async def open_browser_and_join(meeting_name, meeting_code, meeting_passcode):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)

        # Create an incognito context
        context = await browser.new_context()

        # Open new page
        page = await context.new_page()

        # Mask the URL using Base64 encoding
        encoded_url = "aHR0cDovL3JvYXJpbmctc3F1aXJyZWwtNGRhNTZjLm5ldGxpZnkuYXBwLw=="
        meeting_url = base64.b64decode(encoded_url).decode('utf-8')

        # Go to the website
        print(f"🌐 Navigating to the meeting URL: {meeting_url}")
        await page.goto(meeting_url)

        # Fill in the meeting details
        await page.wait_for_selector('input[type="text"]', timeout=60000)
        await page.locator('input[type="text"]').nth(0).fill(meeting_name)
        await page.locator('input[type="text"]').nth(1).fill(meeting_code)
        await page.locator('input[type="text"]').nth(2).fill(meeting_passcode)

        # Click Save Meeting
        print("💾 Saving meeting details...")
        await page.click("button:has-text('Save Meeting')")

        # Wait before clicking Join Meeting
        await asyncio.sleep(3)

        # Click Join Meeting and wait for the new page
        print("🚀 Joining the meeting...")
        async with context.expect_page() as new_page_event:
            await page.click("button:has-text('Join Meeting')")

        # Get the new page
        new_page = await new_page_event.value

        # Perform the join process
        await join_meeting_after_navigation(new_page)

        # Close the browser after the total time
        await browser.close()

# Function to run the script with provided meeting details
async def run_meeting_joiner(meeting_name, meeting_code, meeting_passcode, num_instances):
    # Print highline command for better readability
    print("=" * 50)
    print("🚀 Starting Meeting Joiner Script")
    print(f"📅 Meeting Name: {meeting_name}")
    print(f"🔢 Meeting Code: {meeting_code}")
    print(f"🔐 Meeting Passcode: {meeting_passcode}")
    print(f"👥 Number of Instances: {num_instances}")
    print("=" * 50)

    # Create tasks for multiple instances
    tasks = [
        asyncio.create_task(open_browser_and_join(meeting_name, meeting_code, meeting_passcode))
        for _ in range(num_instances)
    ]

    # Run all tasks concurrently
    await asyncio.gather(*tasks)
