async function sendMessage() {
    const input = document.getElementById("userInput");
    const chat = document.getElementById("chat");
    const text = input.value.trim();
    if (!text) return;
 
    const time = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
 
    // ── USER MESSAGE ──────────────────────────────────────────
    const userMessage = document.createElement("div");
    userMessage.className = "msg-row user-row";
    userMessage.innerHTML = `
        <div class="av user-av">You</div>
        <div class="msg-col user-col">
            <div class="bubble user-bubble">${text}</div>
            <div class="msg-ts">${time}</div>
        </div>
    `;
    chat.appendChild(userMessage);
    input.value = "";
    chat.scrollTop = chat.scrollHeight;
 
    // ── TYPING INDICATOR ─────────────────────────────────────
    const typingRow = document.createElement("div");
    typingRow.className = "msg-row";
    typingRow.id = "typingIndicator";
    typingRow.innerHTML = `
        <div class="av ai-av">
            <img src="husky-logo.png" alt="H" class="av-img"
                 onerror="this.style.display='none';this.nextElementSibling.style.display='inline';">
            <span class="av-fallback" style="display:none;">🐾</span>
        </div>
        <div class="typing-bubble">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    chat.appendChild(typingRow);
    chat.scrollTop = chat.scrollHeight;
 
    // ── FETCH ANSWER FROM API ────────────────────────────────
    // Nothing below this line has changed — same API call as before
    try {
        const response = await fetch(
            `http://127.0.0.1:8000/ask?query=${encodeURIComponent(text)}`
        );
        const data = await response.json();
 
        const answerText = data.answer || "No response found.";
 
        // Remove typing indicator
        const typing = document.getElementById("typingIndicator");
        if (typing) typing.remove();
 
        // ── AI RESPONSE MESSAGE ───────────────────────────────
        const replyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const assistantMessage = document.createElement("div");
        assistantMessage.className = "msg-row";
        assistantMessage.innerHTML = `
            <div class="av ai-av">
                <img src="husky-logo.png" alt="H" class="av-img"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='inline';">
                <span class="av-fallback" style="display:none;">🐾</span>
            </div>
            <div class="msg-col">
                <div class="bubble ai-bubble">${answerText}</div>
                <div class="src-tag">
                    <div class="src-dot"></div>
                    Source: Washington High / FUSD · Indexed today
                </div>
                <div class="follow-ups">
                    <div class="fup" onclick="quickAsk(this)">Tell me more</div>
                    <div class="fup" onclick="quickAsk(this)">Related info</div>
                    <div class="fup" onclick="quickAsk(this)">Contact staff</div>
                </div>
                <div class="msg-ts">${replyTime}</div>
            </div>
        `;
        chat.appendChild(assistantMessage);
 
    } catch (error) {
        // Remove typing indicator on error too
        const typing = document.getElementById("typingIndicator");
        if (typing) typing.remove();
 
        const replyTime = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const errorMessage = document.createElement("div");
        errorMessage.className = "msg-row";
        errorMessage.innerHTML = `
            <div class="av ai-av">
                <img src="husky-logo.png" alt="H" class="av-img"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='inline';">
                <span class="av-fallback" style="display:none;">🐾</span>
            </div>
            <div class="msg-col">
                <div class="bubble ai-bubble">Could not connect to server.</div>
                <div class="msg-ts">${replyTime}</div>
            </div>
        `;
        chat.appendChild(errorMessage);
        console.error(error);
    }
 
    chat.scrollTop = chat.scrollHeight;
}
 
// ── FOLLOW-UP BUTTON CLICK ────────────────────────────────────
function quickAsk(el) {
    document.getElementById("userInput").value = el.textContent;
    sendMessage();
}
