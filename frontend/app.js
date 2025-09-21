const chatBox = document.getElementById('chatBox');
const msgInput = document.getElementById('msg');
const sendBtn = document.getElementById('sendBtn');

function addMsg(text, who) {
    const div = document.createElement('div');
    div.className = 'msg ' + who;
    div.textContent = text;
    chatBox.appendChild(div);
    chatBox.scrollTop = chatBox.scrollHeight;
}

sendBtn.onclick = async function() {
    const message = msgInput.value.trim();
    if (!message) return;
    addMsg(message, 'user');
    msgInput.value = "";
    const resp = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({message: message, user: "demo"})
    });
    const data = await resp.json();
    addMsg(data.reply, 'captain');
};
// Show chat history on load
window.onload = async () => {
    const resp = await fetch('/api/history?user=demo');
    const log = await resp.json();
    for (let m of log) addMsg(m.content, m.role);
};
