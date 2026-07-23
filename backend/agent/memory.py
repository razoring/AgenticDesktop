import os
import time
import hashlib
import chromadb
from typing import List, Dict, Any

class MemoryStore:
    def __init__(self, dbPath: str = None):
        if dbPath is None:
            dbPath = os.path.join(os.path.dirname(__file__), "..", "..", "chroma_db")
        self.client = chromadb.PersistentClient(path=dbPath)
        self.collection = self.client.get_or_create_collection(name="agent_memory")

    def addMemory(self, content: str, metadata: Dict[str, Any] = None) -> None:
        #generate unique id for memory
        docId = hashlib.md5(f"{content}{time.time()}".encode()).hexdigest()
        
        if metadata is None:
            metadata = {}
        metadata["timestamp"] = time.time()
            
        self.collection.add(
            documents=[content],
            metadatas=[metadata],
            ids=[docId]
        )

    def searchMemories(self, query: str, topK: int = 5) -> List[Dict[str, Any]]:
        #retrieve semantic matches
        results = self.collection.query(
            query_texts=[query],
            n_results=topK
        )
        
        memories = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                meta = results["metadatas"][0][i] if results.get("metadatas") else {}
                memories.append({"content": doc, "metadata": meta})
        return memories

    def clearMemories(self) -> None:
        #wipe all memory
        self.client.delete_collection("agent_memory")
        self.collection = self.client.create_collection("agent_memory")
