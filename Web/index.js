lucide.createIcons();

const chatHistory = document.getElementById('chat-history');
const queryField = document.getElementById('QueryField');
const submitBtn = document.getElementById('SubmitQuery');
const providerSelect = document.getElementById('provider-select');
const modelInput = document.getElementById('model-input');
const apiKeyInput = document.getElementById('apikey-input');
const apiKeyLabel = document.getElementById('apikey-label');
const saveSettingsBtn = document.getElementById('save-settings-btn');
const privateModeToggle = document.getElementById('private-mode-toggle');

const callbackModal = document.getElementById('callback-modal');
const callbackQ = document.getElementById('callback-q');
const callbackInput = document.getElementById('callback-input');
const callbackSubmit = document.getElementById('callback-submit');

const modeTool = document.getElementById('ModeTool');
const toolName = modeTool.querySelector('.tool-name');

let socket = null;
let currentTaskId = null;
let currentMode = "autonomous";

function connectWS() {
    socket = new WebSocket(`ws://${window.location.host}/ws/console`);
    socket.onopen = () => addMessage("Connected to Agentic Backend", "system");
    
    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        if (msg.type === "agent_response") {
            addMessage(msg.content, "assistant");
        } else if (msg.type === "status") {
            addMessage(msg.content, "system");
        } else if (msg.type === "user_callback") {
            currentTaskId = msg.taskId;
            callbackQ.textContent = msg.question;
            callbackModal.classList.remove('hidden');
        }
    };
    socket.onclose = () => {
        addMessage("Disconnected. Retrying...", "system");
        setTimeout(connectWS, 3000);
    };
}
connectWS();

function addMessage(text, role) {
    const div = document.createElement('div');
    div.className = `message ${role}`;
    div.textContent = text;
    chatHistory.appendChild(div);
    chatHistory.scrollTop = chatHistory.scrollHeight;
}

// Tool expansion logic
modeTool.addEventListener('mouseenter', () => {
    modeTool.classList.add('expanded');
});
modeTool.addEventListener('mouseleave', () => {
    modeTool.classList.remove('expanded');
});

modeTool.addEventListener('click', (e) => {
    if(e.target.closest('.remove-tool')) {
        modeTool.style.display = "none";
    } else {
        currentMode = currentMode === "autonomous" ? "contextual" : "autonomous";
        toolName.textContent = currentMode.charAt(0).toUpperCase() + currentMode.slice(1);
    }
});

// Attachment @ mentions logic hook
queryField.addEventListener('input', (e) => {
    const val = queryField.value;
    if (val.includes('@')) {
        document.getElementById('AttachmentsRow').classList.remove('hidden');
    }
});

submitBtn.addEventListener('click', () => {
    const text = queryField.value.trim();
    if (!text || !socket || socket.readyState !== WebSocket.OPEN) return;
    
    addMessage(text, "user");
    queryField.value = "";
    document.getElementById('AttachmentsRow').classList.add('hidden');
    
    socket.send(JSON.stringify({
        type: "chat",
        content: text,
        mode: currentMode,
        tabContext: ""
    }));
});

queryField.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        submitBtn.click();
    }
});

callbackSubmit.addEventListener('click', () => {
    const text = callbackInput.value.trim();
    if (!text || !socket) return;
    
    socket.send(JSON.stringify({ type: "callback_reply", taskId: currentTaskId, content: text }));
    callbackModal.classList.add('hidden');
    callbackInput.value = "";
    addMessage(`Replied: ${text}`, "user");
});

providerSelect.addEventListener('change', () => {
    if (providerSelect.value === 'openrouter') {
        apiKeyLabel.style.display = 'block';
        apiKeyInput.style.display = 'block';
        modelInput.value = 'openai/gpt-4o-mini';
    } else {
        apiKeyLabel.style.display = 'none';
        apiKeyInput.style.display = 'none';
        modelInput.value = 'llava';
    }
});

saveSettingsBtn.addEventListener('click', async () => {
    const payload = {
        provider: providerSelect.value,
        modelName: modelInput.value,
        apiKey: apiKeyInput.value,
        privateMode: privateModeToggle.checked
    };
    saveSettingsBtn.textContent = "Saving...";
    try {
        await fetch('/api/config/llm', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload) });
        saveSettingsBtn.textContent = "Saved!";
        document.getElementById('ModelSelector').innerHTML = `${modelInput.value} <i data-lucide="chevrons-up-down" class="Buttons" style="margin-left: 4px;"></i>`;
        lucide.createIcons();
    } catch(e) {
        saveSettingsBtn.textContent = "Error";
    }
    setTimeout(() => { saveSettingsBtn.textContent = "Save Settings"; }, 2000);
});

async function fetchOllamaModels() {
    try {
        const response = await fetch('http://localhost:11434/api/tags');
        if (!response.ok) return;
        const data = await response.json();
        const datalist = document.getElementById('ollama-models');
        if (datalist && data.models) {
            datalist.innerHTML = '';
            data.models.forEach(m => {
                const option = document.createElement('option');
                option.value = m.name;
                datalist.appendChild(option);
            });
        }
    } catch(e) {
        console.log("Could not fetch Ollama models, ensure Ollama is running:", e);
    }
}
fetchOllamaModels();