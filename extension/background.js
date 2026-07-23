let socket = null;

function connectWebSocket() {
  socket = new WebSocket("ws://localhost:8000/ws/extension");

  socket.onopen = () => {
    console.log("Connected to Agent Orchestrator");
  };

  socket.onmessage = (event) => {
    const msg = JSON.parse(event.data);
    if (msg.target === "content") {
      chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
        if (tabs[0]) {
          chrome.tabs.sendMessage(tabs[0].id, msg, (response) => {
            if (socket && socket.readyState === WebSocket.OPEN) {
              socket.send(JSON.stringify({ type: "content_response", data: response }));
            }
          });
        }
      });
    }
  };

  socket.onclose = () => {
    setTimeout(connectWebSocket, 3000);
  };
}

connectWebSocket();

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (socket && socket.readyState === WebSocket.OPEN) {
    socket.send(JSON.stringify(request));
  }
  sendResponse({ status: "relayed" });
});
