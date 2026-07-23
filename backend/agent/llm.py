import json
import base64
import requests
from typing import Dict, Any, List, Optional

DEFAULT_OLLAMA_URL = "http://localhost:11434/api/chat"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

class LLMClient:
    def __init__(self, provider: str = "ollama", modelName: str = "llava", apiKey: Optional[str] = None, privateMode: bool = False):
        self.provider = provider
        self.modelName = modelName
        self.apiKey = apiKey
        self.privateMode = privateMode

    def query(self, messages: List[Dict[str, Any]], systemPrompt: Optional[str] = None, base64Images: List[str] = None) -> str:
        #enforce strict local privacy mode
        if self.privateMode and self.provider != "ollama":
            self.provider = "ollama"
            self.modelName = "llava"
            
        if self.provider == "openrouter":
            return self._queryOpenrouter(messages, systemPrompt, base64Images)
        return self._queryOllama(messages, systemPrompt, base64Images)

    def _queryOllama(self, messages: List[Dict[str, Any]], systemPrompt: Optional[str] = None, base64Images: List[str] = None) -> str:
        #format vl model payload for ollama
        formattedMessages = []
        if systemPrompt:
            formattedMessages.append({"role": "system", "content": systemPrompt})
            
        for msg in messages:
            content = msg["content"]
            role = msg["role"]
            newMsg = {"role": role, "content": content}
            if role == "user" and base64Images:
                #attach array of base64 images to message block
                newMsg["images"] = base64Images
            formattedMessages.append(newMsg)

        payload = {
            "model": self.modelName,
            "messages": formattedMessages,
            "stream": False
        }

        try:
            #dispatch sync http request
            response = requests.post(DEFAULT_OLLAMA_URL, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            return data.get("message", {}).get("content", "")
        except Exception as e:
            return f"[Ollama Error]: {str(e)}"

    def _queryOpenrouter(self, messages: List[Dict[str, Any]], systemPrompt: Optional[str] = None, base64Images: List[str] = None) -> str:
        #format vl model payload for openrouter
        formattedMessages = []
        if systemPrompt:
            formattedMessages.append({"role": "system", "content": systemPrompt})
            
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            
            if role == "user" and base64Images:
                #build openai compatible multimodal array
                contentArray = [{"type": "text", "text": content}]
                for b64 in base64Images:
                    contentArray.append({
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{b64}"}
                    })
                formattedMessages.append({"role": role, "content": contentArray})
            else:
                formattedMessages.append({"role": role, "content": content})

        headers = {
            "Authorization": f"Bearer {self.apiKey or ''}",
            "Content-Type": "application/json"
        }

        payload = {
            "model": self.modelName,
            "messages": formattedMessages
        }

        try:
            #dispatch sync http request
            response = requests.post(OPENROUTER_URL, headers=headers, json=payload, timeout=60)
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if choices:
                return choices[0].get("message", {}).get("content", "")
            return ""
        except Exception as e:
            return f"[OpenRouter Error]: {str(e)}"
