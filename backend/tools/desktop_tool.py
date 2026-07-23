import mss
import pyautogui
import base64
from io import BytesIO
from PIL import Image, ImageDraw

class DesktopTool:
    def __init__(self):
        pyautogui.FAILSAFE = False

    def getScreenshotWithGrid(self, gridSize=100) -> str:
        #capture primary monitor
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            sct_img = sct.grab(monitor)
            img = Image.frombytes("RGB", sct_img.size, sct_img.bgra, "raw", "BGRX")

        draw = ImageDraw.Draw(img)
        width, height = img.size

        #draw red grid lines for visual reference
        for x in range(0, width, gridSize):
            draw.line([(x, 0), (x, height)], fill=(255, 0, 0, 128), width=1)
        for y in range(0, height, gridSize):
            draw.line([(0, y), (width, y)], fill=(255, 0, 0, 128), width=1)

        #draw cell coordinate labels (e.g. "2,3") in blue boxes
        for x in range(0, width, gridSize):
            for y in range(0, height, gridSize):
                label = f"{x//gridSize},{y//gridSize}"
                draw.rectangle([x, y, x+30, y+15], fill="blue")
                draw.text((x+2, y+2), label, fill="white")

        buffered = BytesIO()
        img.save(buffered, format="JPEG", quality=60)
        return base64.b64encode(buffered.getvalue()).decode("utf-8")

    def clickCoordinate(self, gridX: int, gridY: int, gridSize: int = 100, offsetX: int = 50, offsetY: int = 50) -> bool:
        #calculate raw screen coords from grid references
        screenX = (gridX * gridSize) + offsetX
        screenY = (gridY * gridSize) + offsetY
        try:
            pyautogui.click(x=screenX, y=screenY)
            return True
        except:
            return False

    def typeText(self, text: str) -> bool:
        try:
            pyautogui.write(text, interval=0.01)
            return True
        except:
            return False

    def pressKey(self, key: str) -> bool:
        try:
            pyautogui.press(key)
            return True
        except:
            return False
