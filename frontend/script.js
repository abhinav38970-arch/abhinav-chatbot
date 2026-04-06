let chatHistory = []; 

function aiAvatar() {
    return `
        <div class="av ai-av">
            <img src="https://img.icons8.com/ios-filled/50/ffffff/husky.png" alt="Husky" width="20" height="20">
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
    
    if (chatHistory.length > 10) {
        chatHistory = chatHistory.slice(-10);
    }
    
    input.value = "";
    chat.scrollTop = chat.scrollHeight;
    showTyping();

    try {
        // ✅ LOCALHOST URL: Points to the backend running in your terminal
        const response = await fetch(`http://127.0.0.1:8000/ask`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                query: text,
                history: chatHistory
            })
        });

        const data = await response.json();
        const answerText = data.answer || "I couldn't find that information.";
        
        chatHistory.push({"role": "assistant", "content": answerText});

        removeTyping();

        const aiRow = document.createElement("div");
        aiRow.className = "msg-row";
        aiRow.innerHTML = `
            ${aiAvatar()}
            <div class="msg-col">
                <div class="bubble ai-bubble">${answerText}</div>
                <div class="src-tag"><div class="src-dot"></div>Source: fremontunified.org/washington/</div>
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
        console.error("Connection Error:", error);
        // Alert if the backend isn't running
        const errorRow = document.createElement("div");
        errorRow.className = "msg-row";
        errorRow.innerHTML = `<div class="bubble ai-bubble" style="background: #ffcccc; color: #cc0000;">Error: Is the backend terminal running?</div>`;
        chat.appendChild(errorRow);
    }
    chat.scrollTop = chat.scrollHeight;
}