import base64
import os
import asyncio
from playwright.async_api import async_playwright
from playwright_stealth import stealth

class BrowserTool:
    def __init__(self, userDataDir: str = None):
        #default to user's actual chrome profile to bypass anti-bot
        self.userDataDir = userDataDir or os.path.join(os.environ.get("LOCALAPPDATA", ""), "Google", "Chrome", "User Data")
        self.browser = None
        self.context = None
        self.page = None
        self.playwright = None

    async def initBrowser(self, headless=False):
        if self.playwright is None:
            self.playwright = await async_playwright().start()
            
            try:
                self.context = await self.playwright.chromium.launch_persistent_context(
                    user_data_dir=self.userDataDir,
                    headless=headless,
                    channel="chrome",
                    args=["--disable-blink-features=AutomationControlled"]
                )
                self.page = await self.context.new_page()
                await stealth(self.page)
            except Exception as e:
                print(f"[BrowserTool] Fallback to ephemeral profile: {e}")
                self.browser = await self.playwright.chromium.launch(headless=headless, channel="chrome")
                self.context = await self.browser.new_context()
                self.page = await self.context.new_page()
                await stealth(self.page)

    async def navigate(self, url: str) -> None:
        if not self.page:
            await self.initBrowser()
        await self.page.goto(url, wait_until="networkidle")

    async def getScreenshot(self) -> str:
        if not self.page:
            return ""
        
        await self._injectSetOfMarkFallback()
        screenshot_bytes = await self.page.screenshot(type="jpeg", quality=60)
        return base64.b64encode(screenshot_bytes).decode("utf-8")

    async def _injectSetOfMarkFallback(self):
        js = """
        () => {
            if (document.querySelector('.agent-som-mark')) return;
            const elements = document.querySelectorAll('a, button, input, textarea, select, [role="button"]');
            let id = 1;
            elements.forEach(el => {
                const rect = el.getBoundingClientRect();
                if (rect.width > 5 && rect.height > 5 && rect.top >= 0 && rect.left >= 0 && rect.top <= window.innerHeight) {
                    const tag = document.createElement('div');
                    tag.className = 'agent-som-mark';
                    tag.innerText = id;
                    tag.style.position = 'fixed';
                    tag.style.top = `${rect.top}px`;
                    tag.style.left = `${rect.left}px`;
                    tag.style.backgroundColor = 'blue';
                    tag.style.color = 'white';
                    tag.style.padding = '2px';
                    tag.style.fontSize = '12px';
                    tag.style.zIndex = '999999';
                    document.body.appendChild(tag);
                    
                    const box = document.createElement('div');
                    box.className = 'agent-som-mark';
                    box.style.position = 'fixed';
                    box.style.top = `${rect.top}px`;
                    box.style.left = `${rect.left}px`;
                    box.style.width = `${rect.width}px`;
                    box.style.height = `${rect.height}px`;
                    box.style.border = '2px solid blue';
                    box.style.zIndex = '999998';
                    box.style.pointerEvents = 'none';
                    document.body.appendChild(box);
                    id++;
                }
            });
        }
        """
        try:
            await self.page.evaluate(js)
        except:
            pass

    async def clickElement(self, markId: int) -> bool:
        js = f"""
        () => {{
            const tags = document.querySelectorAll('div.agent-som-mark');
            for (let t of tags) {{
                if (t.innerText == '{markId}' && t.style.backgroundColor) {{
                    const x = parseInt(t.style.left);
                    const y = parseInt(t.style.top);
                    const el = document.elementFromPoint(x + 5, y + 5);
                    if (el) {{ el.click(); return true; }}
                }}
            }}
            return false;
        }}
        """
        try:
            return await self.page.evaluate(js)
        except:
            return False

    async def typeText(self, markId: int, text: str) -> bool:
        js = f"""
        () => {{
            const tags = document.querySelectorAll('div.agent-som-mark');
            for (let t of tags) {{
                if (t.innerText == '{markId}' && t.style.backgroundColor) {{
                    const x = parseInt(t.style.left);
                    const y = parseInt(t.style.top);
                    const el = document.elementFromPoint(x + 5, y + 5);
                    if (el) {{
                        el.focus();
                        el.value = '{text}';
                        el.dispatchEvent(new Event('input', {{ bubbles: true }}));
                        el.dispatchEvent(new Event('change', {{ bubbles: true }}));
                        return true;
                    }}
                }}
            }}
            return false;
        }}
        """
        try:
            return await self.page.evaluate(js)
        except:
            return False

    async def close(self):
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
