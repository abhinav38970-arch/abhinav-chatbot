async function sendMessage() {
    const input = document.getElementById("userInput");
    const chat = document.getElementById("chat");

    const text = input.value.trim();
    if (!text) return;

    // create user message
    const userMessage = document.createElement("div");
    userMessage.className = "message";

    userMessage.innerHTML = `
        <div class="avatar user-avatar">U</div>
        <div class="text">${text}</div>
    `;

    chat.appendChild(userMessage);
    input.value = "";
    chat.scrollTop = chat.scrollHeight;

    // create loading message
    const assistantMessage = document.createElement("div");
    assistantMessage.className = "message";

    assistantMessage.innerHTML = `
        <div class="avatar assistant-avatar">H</div>
        <div class="text">Thinking...</div>
    `;

    chat.appendChild(assistantMessage);
    chat.scrollTop = chat.scrollHeight;

    try {
        const response = await fetch(
            `http://127.0.0.1:8000/ask?query=${encodeURIComponent(text)}`
        );

        const data = await response.json();

        assistantMessage.querySelector(".text").innerText =
            data.answer || "No response found.";

    } catch (error) {
        assistantMessage.querySelector(".text").innerText =
            "⚠️ Could not connect to server.";
        console.error(error);
    }

    chat.scrollTop = chat.scrollHeight;
}