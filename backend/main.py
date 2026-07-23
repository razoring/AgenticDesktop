import os
import json
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from backend.agent.orchestrator import MasterOrchestrator
from pydantic import BaseModel

app = FastAPI()

consolePath = os.path.join(os.path.dirname(__file__), "..", "Web")
app.mount("/console", StaticFiles(directory=consolePath, html=True), name="console")

active_console_ws = None
extension_ws = None

async def sendToConsole(payload: dict):
    if active_console_ws:
        try:
            await active_console_ws.send_json(payload)
        except:
            pass

orchestrator = MasterOrchestrator(consoleCallback=sendToConsole)

@app.get("/")
async def root():
    return RedirectResponse(url="/console/")

@app.on_event("startup")
async def startup_event():
    orchestrator.start()

class LLMConfig(BaseModel):
    provider: str
    modelName: str
    apiKey: str = None
    privateMode: bool = False

@app.post("/api/config/llm")
async def configLLM(config: LLMConfig):
    orchestrator.setLLMConfig(config.provider, config.modelName, config.apiKey, config.privateMode)
    return {"status": "ok"}

@app.websocket("/ws/console")
async def console_websocket(websocket: WebSocket):
    global active_console_ws
    await websocket.accept()
    active_console_ws = websocket
    print("[Console WS] Connected")
    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)
            
            if msg.get("type") == "chat":
                asyncio.create_task(
                    orchestrator.handleUserMessage(
                        msg["content"], 
                        msg.get("mode", "autonomous"),
                        msg.get("tabContext")
                    )
                )
            elif msg.get("type") == "callback_reply":
                asyncio.create_task(
                    orchestrator.resumeTask(msg["taskId"], msg["content"])
                )
    except WebSocketDisconnect:
        active_console_ws = None
        print("[Console WS] Disconnected")

@app.websocket("/ws/extension")
async def extension_websocket(websocket: WebSocket):
    global extension_ws
    await websocket.accept()
    extension_ws = websocket
    print("[Extension WS] Connected")
    try:
        while True:
            data = await websocket.receive_text()
            print(f"[Extension] {data}")
    except WebSocketDisconnect:
        extension_ws = None
        print("[Extension WS] Disconnected")

@app.on_event("shutdown")
async def shutdown_event():
    await orchestrator.shutdown()
