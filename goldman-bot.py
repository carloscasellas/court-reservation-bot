from playwright.async_api import async_playwright, Playwright
import asyncio
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

ROOT_URL = os.getenv("ROOT_URL")
EMAIL = os.getenv("EMAIL")
PASSWORD = os.getenv("PASSWORD")

current_date = datetime.now()
future_day = (current_date + timedelta(days=8)).strftime("%d").lstrip("0")
future_date = (current_date + timedelta(days=8)).strftime("%m/%d/%Y")
time_list = ['7:00', '7:30', '8:00', '8:30', '9:00']

async def click_button(selector: str, page: 'playwright.async_api.Page'):
    await page.wait_for_load_state('load'),
    await page.wait_for_selector(selector, state='visible'),
    await asyncio.gather(
        page.eval_on_selector(selector, 'el => el.removeAttribute("target")'),
        page.click(selector)
    )

async def main():
    async with async_playwright() as playwright:
        chromium = playwright.chromium
        browser = await chromium.launch(headless=False, args=[
            "--disable-blink-features=AutomationControlled",
            "--no-sandbox",
            "--disable-dev-shm-usage"
        ])
        context = await browser.new_context(
            record_video_dir="videos/",
            record_video_size={"width": 1280, "height": 720},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",   
        )
        page = await context.new_page()        
        await page.goto(ROOT_URL)
        await click_button('a:has-text("Reserve a Court & Register for Classes")', page)
        await click_button('a:has-text("LOG IN")', page)
        await log_in(page)
        await click_button('a:has-text("BOOK A COURT")', page)
        await page.wait_for_load_state('load')
        reserved = await reserve_court(page)
        if reserved:
            print('Reserved a court!')
        else:
            print('Failed to reserve a court.')
        await context.close()
        await browser.close()
    
async def log_in(page: 'playwright.async_api.Page'):
    button = 'button:has(span:has-text("Continue"))'
    await page.locator('input[name="email"]').fill(EMAIL)
    await page.locator('input[name="password"]').fill(PASSWORD)
    await page.eval_on_selector(button, 'el => el.removeAttribute("target")')
    await page.click(button)
    await page.wait_for_load_state('load')
    
async def fill_out_res_form(page: 'playwright.async_api.Page'):
    await page.click('span[aria-labelledby="Duration_label"]')
    await asyncio.sleep(3)
    duration_options = await page.query_selector_all('li:has(span:has-text("1 hour & 30 minutes"))')
    if duration_options:
        await duration_options[-1].click()
    await page.click('label:has-text("Check to agree to above disclosure")')
    await page.wait_for_selector('label:has-text("$18.00")', state='visible')
    await page.click('button[onclick="submitCreateReservationForm()"]')
    await asyncio.sleep(1.5)
    if await page.is_visible('div:has-text("Sorry, no available courts for the time requested.")'):
        await click_button('button:has-text("OK")', page)
        await click_button('button:has-text("Close")', page)
        print('No court available.')
        return False
    return True
    
async def attempt_court_res(time: str, endTime: str, page: 'playwright.async_api.Page'):
    try:
        # Use JavaScript evaluation to find elements by partial data-href match
        script = f"""
        () => {{
            const links = Array.from(document.querySelectorAll('a[data-href]'));
            const linkHrefs = links.map(link => link.getAttribute('data-href'));
            return linkHrefs.find(link => 
                link.includes('{time}') &&
                link.includes('{endTime}') &&
                link.includes('PM')
            );
            
            return {{
                linkHrefs,
                matching_link
            }}
        
        }}
        """
        element = await page.evaluate(script)
        
        if element:
            # Find the element again using a function to click it
            await page.evaluate(f"""
            () => {{
                const links = Array.from(document.querySelectorAll('a[data-href]'));
                const link = links.find(link => 
                    link.getAttribute('data-href').includes('{time}') && 
                    link.getAttribute('data-href').includes('{endTime}') &&
                    link.getAttribute('data-href').includes('PM')
                );
                if (link) link.click();
            }}
            """)
            
            print(f"Found and clicked time slot: {time} PM")
            await page.wait_for_load_state('load')
            return await fill_out_res_form(page)
        else:
            print(f"Time slot {time} PM not available")
            return False
            
    except Exception as e:
        print(f"Error when attempting to reserve court at {time} PM: {str(e)}")
        return False
        

async def reserve_court(page: 'playwright.async_api.Page'):
    await page.click('a.k-nav-current')
    selector = f'td:has(a:has-text("{future_day}"))'
    await page.wait_for_selector(selector, state='visible')
    await page.click(selector)
    
    await asyncio.sleep(1.5)
    
    for index in range(len(time_list) - 1):
        res = await attempt_court_res(time_list[index], time_list[index + 1], page)
        if res:
            return True
        await asyncio.sleep(1)
    return False

if __name__ == '__main__':
    asyncio.run(main())