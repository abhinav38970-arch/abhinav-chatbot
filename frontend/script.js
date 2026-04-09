let chatHistory = []; 

function aiAvatar() {
    return `
        <div class="av ai-av">
            <svg width="22" height="22" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
                <path d="M50 10L10 30L15 80L50 90L85 80L90 30L50 10Z" fill="white" stroke="white" stroke-width="2"/>
                <path d="M50 20C40 20 30 25 30 40L40 70H60L70 40C70 25 60 20 50 20ZM50 70H40L35 45L45 30H55L65 45L60 70H50Z" fill="#ff6600"/>
                <circle cx="42" cy="40" r="3" fill="#ff6600"/>
                <circle cx="58" cy="40" r="3" fill="#ff6600"/>
            </svg>
        </div>
    `;
}

function showTyping() {
    const chat = document.getElementById("chat");
    const el = document.createElement("div");
    el.className = "msg-row";
    el.id = "typingIndicator";
    el.innerHTML = `${aiAvatar()}<div class="typing-bubble"><div class="dot"></div><div class="dot"></div><div class="dot"></div></div>`;
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
}

function quickAsk(el) {
    document.getElementById("userInput").value = el.textContent;
    sendMessage();
}

async function sendMessage() {
    const input = document.getElementById("userInput");
    const chat  = document.getElementById("chat");
    const text  = input.value.trim();
    if (!text) return;

    const userRow = document.createElement("div");
    userRow.className = "msg-row user-row";
    userRow.innerHTML = `<div class="av user-av">You</div><div class="msg-col user-col"><div class="bubble user-bubble">${text}</div></div>`;
    chat.appendChild(userRow);
    
    chatHistory.push({"role": "user", "content": text});
    if (chatHistory.length > 10) chatHistory = chatHistory.slice(-10);
    
    input.value = "";
    chat.scrollTop = chat.scrollHeight;
    showTyping();

    try {
        // Pointing to the new /api/ask route
        const backendUrl = window.location.origin + "/api/ask";
        
        const response = await fetch(backendUrl, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ query: text, history: chatHistory })
        });

        if (!response.ok) throw new Error('Server unreachable');

        const data = await response.json();
        const answerText = data.answer || "Information regarding this query is currently unavailable.";
        const sources = (data.sources && data.sources.length > 0) ? data.sources : ["https://fremontunified.org/washington/"];

        chatHistory.push({"role": "assistant", "content": answerText});
        removeTyping();

        const sourceHtml = sources.map(url => {
            let pageName = url.replace(/\/$/, "").split('/').pop() || "Home";
            pageName = pageName.charAt(0).toUpperCase() + pageName.slice(1);
            return `<a href="${url}" target="_blank" class="src-tag"><div class="src-dot"></div>Source: ${pageName}</a>`;
        }).join("");

        const aiRow = document.createElement("div");
        aiRow.className = "msg-row";
        aiRow.innerHTML = `
            ${aiAvatar()}
            <div class="msg-col">
                <div class="bubble ai-bubble">${answerText}</div>
                <div class="sources-list">${sourceHtml}</div>
                <div class="follow-ups">
                    <div class="fup" onclick="quickAsk(this)">Tell me more</div>
                    <div class="fup" onclick="quickAsk(this)">Related info</div>
                    <div class="fup" onclick="quickAsk(this)">Contact staff</div>
                </div>
            </div>
        `;
        chat.appendChild(aiRow);

    } catch (error) {
        removeTyping();
        console.error("Fetch Error:", error);
        const errorRow = document.createElement("div");
        errorRow.className = "msg-row";
        errorRow.innerHTML = `<div class="bubble ai-bubble" style="background: #ffcccc; color: #cc0000;">Connection Error: Check if backend is running.</div>`;
        chat.appendChild(errorRow);
    }
    chat.scrollTop = chat.scrollHeight;
}