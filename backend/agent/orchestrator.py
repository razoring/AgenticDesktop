import asyncio
import json
import re
from typing import Dict, Any, List, Callable
from .llm import LLMClient
from .memory import MemoryStore
from .scheduler import TaskScheduler
from ..tools.browser_tool import BrowserTool
from ..tools.desktop_tool import DesktopTool
from ..tools.search_tool import SearchTool

SYSTEM_PROMPT = """You are Agentic Desktop, an autonomous AI assistant powered by Vision-Language capabilities.
You have access to the user's computer via Set-of-Mark screenshots.

AVAILABLE TOOLS:
1. CLICK <MarkID> - Click on a numbered UI element on the screen.
2. TYPE <MarkID> "text" - Type text into a numbered UI element.
3. SEARCH "query" - Search the web using DuckDuckGo.
4. REMEMBER "fact" - Save a fact to long-term ChromaDB memory.
5. SCHEDULE "datetime_iso" "prompt" - Schedule a future task.
6. SPAWN "sub-task" - Spawn a concurrent background sub-agent for a task.
7. BROWSE "url" - Navigate the browser to a specific URL.
8. ASK_USER "question" - Pause execution and ask the user a question or for authorization (Human-in-the-Loop).
9. DONE "message" - Conclude the task and report back.

RULES:
- You will receive a screenshot with red grids or blue/red boxes with numbers. These are MarkIDs.
- Output ONLY ONE tool call per turn.
- The output format must be EXACTLY: TOOL_NAME arguments
- Use ASK_USER if you are unsure or need human authorization for sensitive actions.
- Use SPAWN if you need to do something in parallel.
"""

class MasterOrchestrator:
    def __init__(self, consoleCallback: Callable):
        self.consoleCallback = consoleCallback
        self.memory = MemoryStore()
        self.scheduler = TaskScheduler()
        self.llm = LLMClient()
        
        self.browserTool = BrowserTool()
        self.desktopTool = DesktopTool()
        self.searchTool = SearchTool()
        
        self.activeTasks = {}
        self.chatHistory = []

    def setLLMConfig(self, provider: str, modelName: str, apiKey: str = None, privateMode: bool = False):
        self.llm = LLMClient(provider=provider, modelName=modelName, apiKey=apiKey, privateMode=privateMode)

    def start(self):
        self.scheduler.start()

    async def _emit(self, type_: str, content: str, **kwargs):
        payload = {"type": type_, "content": content}
        payload.update(kwargs)
        await self.consoleCallback(payload)

    async def handleUserMessage(self, message: str, mode: str, tabContext: str = None):
        #retrieve semantic memory
        memories = self.memory.searchMemories(message, topK=3)
        memContext = "\n".join([m["content"] for m in memories]) if memories else "No relevant past memory."

        prompt = f"User Request: {message}\nMode: {mode}\nMemory Context: {memContext}\n"
        if tabContext:
            prompt += f"Tab Context: {tabContext}\n"

        self.chatHistory.append({"role": "user", "content": prompt})

        taskId = f"task_{asyncio.get_event_loop().time()}"
        self.activeTasks[taskId] = True
        
        if mode == "autonomous":
            await self._emit("agent_response", "Spawned autonomous background task. I will notify you when it's done.")
            asyncio.create_task(self._executionLoop(taskId))
        else:
            await self._executionLoop(taskId)

    async def _executionLoop(self, taskId: str):
        iteration = 0
        while self.activeTasks.get(taskId) and iteration < 15:
            iteration += 1
            
            #1. Observe (Screenshot)
            b64_image = None
            if self.browserTool.page:
                b64_image = await self.browserTool.getScreenshot()
            if not b64_image:
                b64_image = self.desktopTool.getScreenshotWithGrid()

            #2. Orient & Decide
            obsMsg = {"role": "user", "content": "Current screen state attached. What is your next action?"}
            ctx = self.chatHistory.copy()
            ctx.append(obsMsg)

            await self._emit("status", "Analyzing Screen...")
            #invoke VL model
            response = self.llm.query(messages=ctx, systemPrompt=SYSTEM_PROMPT, base64Images=[b64_image] if b64_image else None)
            self.chatHistory.append({"role": "assistant", "content": response})

            #3. Act (Parse Tool Calls)
            actionMatched = False
            
            if response.startswith("DONE"):
                msg = response.replace("DONE", "").strip()
                await self._emit("agent_response", msg)
                self.activeTasks[taskId] = False
                break
                
            elif response.startswith("ASK_USER"):
                msg = response.replace("ASK_USER", "").strip()
                await self._emit("user_callback", msg, question=msg, taskId=taskId)
                self.activeTasks[taskId] = "paused"
                break
                
            elif response.startswith("CLICK"):
                mark = re.search(r"CLICK\s+(\d+)", response)
                if mark:
                    markId = int(mark.group(1))
                    await self._emit("status", f"Clicking {markId}...")
                    if self.browserTool.page:
                        await self.browserTool.clickElement(markId)
                    actionMatched = True
            
            elif response.startswith("TYPE"):
                match = re.search(r"TYPE\s+(\d+)\s+\"(.*)\"", response)
                if match:
                    markId = int(match.group(1))
                    text = match.group(2)
                    await self._emit("status", f"Typing in {markId}...")
                    if self.browserTool.page:
                        await self.browserTool.typeText(markId, text)
                    actionMatched = True
                    
            elif response.startswith("SEARCH"):
                match = re.search(r"SEARCH\s+\"(.*)\"", response)
                if match:
                    query = match.group(1)
                    await self._emit("status", f"Searching DDG for {query}...")
                    res = self.searchTool.search(query)
                    self.chatHistory.append({"role": "user", "content": f"Search Results: {json.dumps(res)}"})
                    actionMatched = True
                    
            elif response.startswith("REMEMBER"):
                match = re.search(r"REMEMBER\s+\"(.*)\"", response)
                if match:
                    fact = match.group(1)
                    self.memory.addMemory(fact)
                    await self._emit("status", "Saved to memory.")
                    self.chatHistory.append({"role": "user", "content": "Memory saved."})
                    actionMatched = True
                    
            elif response.startswith("BROWSE"):
                match = re.search(r"BROWSE\s+\"(.*)\"", response)
                if match:
                    url = match.group(1)
                    await self._emit("status", f"Navigating to {url}...")
                    await self.browserTool.navigate(url)
                    self.chatHistory.append({"role": "user", "content": f"Navigated to {url}"})
                    actionMatched = True
                    
            elif response.startswith("SPAWN"):
                match = re.search(r"SPAWN\s+\"(.*)\"", response)
                if match:
                    subTask = match.group(1)
                    await self._emit("agent_response", f"Spawning sub-agent for: {subTask}")
                    asyncio.create_task(self.handleUserMessage(subTask, "autonomous"))
                    self.chatHistory.append({"role": "user", "content": f"Spawned sub-task {subTask}"})
                    actionMatched = True
                    
            if not actionMatched and not response.startswith("DONE"):
                self.chatHistory.append({"role": "user", "content": "You didn't output a valid TOOL command. Please use one of the specified commands."})

            await asyncio.sleep(1)
            
        if self.activeTasks.get(taskId) == True:
            del self.activeTasks[taskId]

    async def resumeTask(self, taskId: str, userInput: str):
        if self.activeTasks.get(taskId) == "paused":
            self.activeTasks[taskId] = True
            self.chatHistory.append({"role": "user", "content": f"User replied to ASK_USER: {userInput}"})
            await self._executionLoop(taskId)

    async def shutdown(self):
        await self.browserTool.close()
