//inject set-of-mark visual bounding boxes
function applySetOfMark() {
    //remove existing marks
    document.querySelectorAll('.agent-som-mark').forEach(el => el.remove());
    
    //find interactive elements
    const elements = document.querySelectorAll('a, button, input, textarea, select, [role="button"], [tabindex="0"]');
    let markId = 1;
    const elementsMap = [];

    elements.forEach(el => {
        const rect = el.getBoundingClientRect();
        //only mark visible elements
        if (rect.width > 5 && rect.height > 5 && rect.top >= 0 && rect.left >= 0 && rect.bottom <= (window.innerHeight || document.documentElement.clientHeight) && rect.right <= (window.innerWidth || document.documentElement.clientWidth)) {
            
            //create visual tag
            const tag = document.createElement('div');
            tag.className = 'agent-som-mark';
            tag.innerText = markId;
            tag.style.position = 'fixed';
            tag.style.top = `${rect.top}px`;
            tag.style.left = `${rect.left}px`;
            tag.style.backgroundColor = 'red';
            tag.style.color = 'white';
            tag.style.padding = '2px 4px';
            tag.style.fontSize = '12px';
            tag.style.fontWeight = 'bold';
            tag.style.zIndex = '999999';
            tag.style.pointerEvents = 'none';
            tag.style.border = '1px solid black';
            document.body.appendChild(tag);
            
            //create bounding box
            const box = document.createElement('div');
            box.className = 'agent-som-mark';
            box.style.position = 'fixed';
            box.style.top = `${rect.top}px`;
            box.style.left = `${rect.left}px`;
            box.style.width = `${rect.width}px`;
            box.style.height = `${rect.height}px`;
            box.style.border = '2px solid red';
            box.style.zIndex = '999998';
            box.style.pointerEvents = 'none';
            document.body.appendChild(box);

            elementsMap.push({
                id: markId,
                tagName: el.tagName,
                text: el.innerText ? el.innerText.trim().slice(0, 50) : '',
                x: Math.round(rect.left + rect.width / 2),
                y: Math.round(rect.top + rect.height / 2)
            });
            
            markId++;
        }
    });

    return elementsMap;
}

function clearSetOfMark() {
    document.querySelectorAll('.agent-som-mark').forEach(el => el.remove());
}

chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
    if (message.action === "apply_som") {
        const map = applySetOfMark();
        sendResponse({ status: "applied", map: map });
    } else if (message.action === "clear_som") {
        clearSetOfMark();
        sendResponse({ status: "cleared" });
    } else if (message.action === "scroll") {
        window.scrollBy({ top: message.amount, behavior: "smooth" });
        sendResponse({ status: "scrolled" });
    }
});
