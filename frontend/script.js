/* ============================================================
   HUSKY AI — script.js
   Washington High School
   Only the HTML structure changed from the original.
   The fetch() call, API URL, and response handling are
   completely untouched from your teammate's original code.
   ============================================================ */

/* ------ PAW SVG HELPER ------ */
/* Used inside dynamically created message rows */
function pawSVG() {
    return `
        <svg viewBox="0 0 64 64" fill="white" style="width:18px;height:18px;">
            <ellipse cx="16" cy="12" rx="6" ry="8"/>
            <ellipse cx="32" cy="8"  rx="6" ry="8"/>
            <ellipse cx="48" cy="12" rx="6" ry="8"/>
            <ellipse cx="56" cy="28" rx="5" ry="7"/>
            <path d="M10 36 Q6 22 18 20 Q26 20 32 28 Q38 20 46 20 Q58 22 54 36 Q50 54 32 58 Q14 54 10 36Z"/>
        </svg>
    `;
}

/* ------ AI AVATAR HTML ------ */
/* Shows real image if husky-logo.png exists, SVG paw as fallback */
function aiAvatar() {
    return `
        <div class="av ai-av">
            <img
                src="husky-logo.png"
                alt="H"
                class="av-img"
                onerror="this.style.display='none';this.nextElementSibling.style.display='block';"
            >
            <svg style="display:none;" viewBox="0 0 64 64" fill="white">
                <ellipse cx="16" cy="12" rx="6" ry="8"/>
                <ellipse cx="32" cy="8"  rx="6" ry="8"/>
                <ellipse cx="48" cy="12" rx="6" ry="8"/>
                <ellipse cx="56" cy="28" rx="5" ry="7"/>
                <path d="M10 36 Q6 22 18 20 Q26 20 32 28 Q38 20 46 20 Q58 22 54 36 Q50 54 32 58 Q14 54 10 36Z"/>
            </svg>
        </div>
    `;
}

/* ------ TYPING INDICATOR ------ */
function showTyping() {
    const chat = document.getElementById("chat");
    const el   = document.createElement("div");
    el.className = "msg-row";
    el.id        = "typingIndicator";
    el.innerHTML = `
        ${aiAvatar()}
        <div class="typing-bubble">
            <div class="dot"></div>
            <div class="dot"></div>
            <div class="dot"></div>
        </div>
    `;
    chat.appendChild(el);
    chat.scrollTop = chat.scrollHeight;
}

function removeTyping() {
    const el = document.getElementById("typingIndicator");
    if (el) el.remove();
}

/* ------ FOLLOW-UP BUTTON CLICK ------ */
function quickAsk(el) {
    document.getElementById("userInput").value = el.textContent;
    sendMessage();
}

/* ------ MAIN SEND FUNCTION ------ */
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
    showTyping();

    // ── API CALL — original fetch logic, completely unchanged ─
    try {
        const response = await fetch(
            `http://127.0.0.1:8000/ask?query=${encodeURIComponent(text)}`
        );
        const data = await response.json();
        const answerText = data.answer || "No response found.";

        removeTyping();

        // ── AI BUBBLE ─────────────────────────────────────────
        const aiRow = document.createElement("div");
        aiRow.className = "msg-row";
        aiRow.innerHTML = `
            ${aiAvatar()}
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
        removeTyping();

        // ── ERROR BUBBLE ──────────────────────────────────────
        const errRow = document.createElement("div");
        errRow.className = "msg-row";
        errRow.innerHTML = `
            ${aiAvatar()}
            <div class="msg-col">
                <div class="bubble ai-bubble">
                    Could not connect to the server. Please try again.
                </div>
            </div>
        `;
        chat.appendChild(errRow);
        console.error(error);
    }

    chat.scrollTop = chat.scrollHeight;
}
