async function sendMessage() {
    const input = document.getElementById("userInput");
    const chat  = document.getElementById("chat");
    const text  = input.value.trim();
    if (!text) return;

    // ── USER BUBBLE ───────────────────────────────────────────
    const userRow = document.createElement("div");
    userRow.className = "msg-row user-row";
    userRow.innerHTML = `
        <div class="av user-av">You</div>
        <div class="msg-col user-col">
            <div class="bubble user-bubble">${text}</div>
        </div>
    `;
    chat.appendChild(userRow);
    input.value = "";
    chat.scrollTop = chat.scrollHeight;

    // ── TYPING INDICATOR ─────────────────────────────────────
    const typingRow = document.createElement("div");
    typingRow.className = "msg-row";
    typingRow.id = "typingIndicator";
    typingRow.innerHTML = `
        <div class="av ai-av">
            <img src="husky-logo.png" alt="H" class="av-img"
                 onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
            <svg style="display:none;" viewBox="0 0 100 100" fill="white">
                <ellipse cx="24" cy="20" rx="11" ry="14"/>
                <ellipse cx="50" cy="14" rx="11" ry="14"/>
                <ellipse cx="76" cy="20" rx="11" ry="14"/>
                <ellipse cx="89" cy="46" rx="9"  ry="12"/>
                <path d="M14 58 Q8 36 26 34 Q42 34 50 46 Q58 34 74 34 Q92 36 86 58 Q80 84 50 90 Q20 84 14 58Z"/>
            </svg>
        </div>
        <div class="typing-bubble">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    chat.appendChild(typingRow);
    chat.scrollTop = chat.scrollHeight;

    // ── FETCH FROM API ────────────────────────────────────────
    // This section is unchanged — same API call as before
    try {
        const response = await fetch(
            `http://127.0.0.1:8000/ask?query=${encodeURIComponent(text)}`
        );
        const data = await response.json();
        const answerText = data.answer || "No response found.";

        document.getElementById("typingIndicator")?.remove();

        // ── AI RESPONSE BUBBLE ────────────────────────────────
        const aiRow = document.createElement("div");
        aiRow.className = "msg-row";
        aiRow.innerHTML = `
            <div class="av ai-av">
                <img src="husky-logo.png" alt="H" class="av-img"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
                <svg style="display:none;" viewBox="0 0 100 100" fill="white">
                    <ellipse cx="24" cy="20" rx="11" ry="14"/>
                    <ellipse cx="50" cy="14" rx="11" ry="14"/>
                    <ellipse cx="76" cy="20" rx="11" ry="14"/>
                    <ellipse cx="89" cy="46" rx="9"  ry="12"/>
                    <path d="M14 58 Q8 36 26 34 Q42 34 50 46 Q58 34 74 34 Q92 36 86 58 Q80 84 50 90 Q20 84 14 58Z"/>
                </svg>
            </div>
            <div class="msg-col">
                <div class="bubble ai-bubble">${answerText}</div>
                <div class="src-tag">
                    <div class="src-dot"></div>
                    Source: fremontunified.org/washington/
                </div>
                <div class="follow-ups">
                    <div class="fup" onclick="quickAsk(this)">Tell me more</div>
                    <div class="fup" onclick="quickAsk(this)">Related info</div>
                    <div class="fup" onclick="quickAsk(this)">Contact staff</div>
                </div>
            </div>
        `;
        chat.appendChild(aiRow);

    } catch (error) {
        document.getElementById("typingIndicator")?.remove();

        const errRow = document.createElement("div");
        errRow.className = "msg-row";
        errRow.innerHTML = `
            <div class="av ai-av">
                <img src="husky-logo.png" alt="H" class="av-img"
                     onerror="this.style.display='none';this.nextElementSibling.style.display='block';">
                <svg style="display:none;" viewBox="0 0 100 100" fill="white">
                    <ellipse cx="24" cy="20" rx="11" ry="14"/>
                    <ellipse cx="50" cy="14" rx="11" ry="14"/>
                    <ellipse cx="76" cy="20" rx="11" ry="14"/>
                    <ellipse cx="89" cy="46" rx="9"  ry="12"/>
                    <path d="M14 58 Q8 36 26 34 Q42 34 50 46 Q58 34 74 34 Q92 36 86 58 Q80 84 50 90 Q20 84 14 58Z"/>
                </svg>
            </div>
            <div class="msg-col">
                <div class="bubble ai-bubble">Could not connect to server.</div>
            </div>
        `;
        chat.appendChild(errRow);
        console.error(error);
    }

    chat.scrollTop = chat.scrollHeight;
}

// Follow-up button sends that text as a new message
function quickAsk(el) {
    document.getElementById("userInput").value = el.textContent;
    sendMessage();
}
