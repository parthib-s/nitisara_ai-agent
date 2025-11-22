// State & elements
const els = {
    chatBox: document.getElementById('chatBox'),
    msgInput: document.getElementById('msg'),
    sendBtn: document.getElementById('sendBtn'),
    tabs: document.querySelectorAll('.tab'),
    views: document.querySelectorAll('.view'),
    conversationsList: document.getElementById('conversationsList'),
    ordersList: document.getElementById('ordersList'),
    ordersTable: document.getElementById('ordersTable'),
    trackingList: document.getElementById('trackingList'),
    newChatBtn: document.getElementById('newChatBtn'),
    reloadHistoryBtn: document.getElementById('reloadHistoryBtn'),
    systemPrompt: document.getElementById('systemPrompt'),
    sessionContext: document.getElementById('sessionContext'),
    saveContextBtn: document.getElementById('saveContextBtn'),
    loginBtn: document.getElementById('loginBtn'),
    logoutBtn: document.getElementById('logoutBtn'),
    userLabel: document.getElementById('userLabel'),
    authModal: document.getElementById('authModal'),
    authUsername: document.getElementById('authUsername'),
    authEmail: document.getElementById('authEmail'),
    authCancel: document.getElementById('authCancel'),
    authConfirm: document.getElementById('authConfirm'),
    complianceQuery: document.getElementById('complianceQuery'),
    complianceCheckBtn: document.getElementById('complianceCheckBtn'),
    complianceResult: document.getElementById('complianceResult'),
    pdfUpload: document.getElementById('pdfUpload'),
    pdfUploadBtn: document.getElementById('pdfUploadBtn'),
    // Bill generator fields
    billForm: document.getElementById('billForm'),
    companyName: document.getElementById('companyName'),
    billItems: document.getElementById('billItems'),
    tax: document.getElementById('tax'),
    total: document.getElementById('total'),
    billResult: document.getElementById('billResult'),
    statActiveOrders: document.getElementById('stat-active-orders'),
    statInTransit: document.getElementById('stat-in-transit'),
    statEta: document.getElementById('stat-eta'),
    statRt: document.getElementById('stat-rt'),
};

const state = {
    user: JSON.parse(localStorage.getItem('nitisara_user') || 'null') || { id: 'guest', name: 'Guest' },
    sessionId: localStorage.getItem('nitisara_session') || `sess_${Date.now()}`,
    sessions: JSON.parse(localStorage.getItem('nitisara_sessions') || '[]'),
    systemPrompt: localStorage.getItem('nitisara_system_prompt') || '',
    sessionContext: localStorage.getItem('nitisara_session_context') || '',
    orders: [],
    conversations: [],
};

function currentUserKey() {
    return `${state.user.id || 'guest'}__${state.sessionId}`;
}

function persistSessions() {
    localStorage.setItem('nitisara_sessions', JSON.stringify(state.sessions));
    localStorage.setItem('nitisara_session', state.sessionId);
}

// Utils
function setUser(u) {
    state.user = u;
    localStorage.setItem('nitisara_user', JSON.stringify(u));
    els.userLabel.textContent = u.name || u.id;
    els.loginBtn.classList.toggle('hidden', true);
    els.logoutBtn.classList.toggle('hidden', false);
}
function clearUser() {
    state.user = { id: 'guest', name: 'Guest' };
    localStorage.removeItem('nitisara_user');
    els.userLabel.textContent = 'Guest';
    els.loginBtn.classList.toggle('hidden', false);
    els.logoutBtn.classList.toggle('hidden', true);
}
function saveContext() {
    localStorage.setItem('nitisara_system_prompt', els.systemPrompt.value || '');
    localStorage.setItem('nitisara_session_context', els.sessionContext.value || '');
}
function switchView(view) {
    els.tabs.forEach(t => t.classList.toggle('active', t.dataset.view === view));
    els.views.forEach(v => v.classList.toggle('active', v.id === `view-${view}`));
}

// Chat rendering
function addMsg(text, who) {
    const div = document.createElement('div');
    div.className = 'msg ' + who;
        div.textContent = text;
    els.chatBox.appendChild(div);
    els.chatBox.scrollTop = els.chatBox.scrollHeight;
}

async function sendMessage(message) {
    if (!message.trim()) return;
    addMsg(message, 'user');
    els.msgInput.value = '';
    
    const typingDiv = document.createElement('div');
    typingDiv.className = 'msg captain typing';
    typingDiv.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Captain is thinking...';
    els.chatBox.appendChild(typingDiv);
    els.chatBox.scrollTop = els.chatBox.scrollHeight;
    
    try {
        const payload = { message, user: currentUserKey() };
        const resp = await fetch('http://localhost:5000/api/chat', {
            method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload)
        });
        const data = await resp.json();
        els.chatBox.removeChild(typingDiv);
        if (resp.ok) {
            addMsg(data.reply, 'captain');
            extractOrdersFromReply(data.reply);
            refreshOrdersUI();
        } else {
            addMsg(`Error: ${data.reply || 'Something went wrong'}`, 'captain');
        }
    } catch (e) {
        els.chatBox.removeChild(typingDiv);
        addMsg('Sorry, I cannot connect to the server. Ensure backend is running.', 'captain');
        console.error(e);
    }
}

// Orders parsing (simple heuristics from Captain messages)
function extractOrdersFromReply(text) {
    const idMatch = text.match(/Order ID:\s*(NTS-\d{4})/i);
    if (idMatch) {
        const id = idMatch[1];
        const modeMatch = text.match(/Mode:\s*([^\n]+)/i);
        const routeMatch = text.match(/Route:\s*([^\n]+)/i);
        const order = { id, mode: modeMatch ? modeMatch[1].trim() : 'Unknown', route: routeMatch ? routeMatch[1].trim() : '', status: 'In Transit' };
        if (!state.orders.find(o => o.id === id)) {
            state.orders.unshift(order);
        }
    }
}

function refreshOrdersUI() {
    els.ordersList.innerHTML = '';
    state.orders.slice(0, 8).forEach(o => {
        const item = document.createElement('div');
        item.className = 'item';
        item.innerHTML = `<i class="fas fa-box"></i><div><div>${o.id}</div><div style="color:#94a3b8;font-size:12px;">${o.mode} • ${o.status}</div></div>`;
        item.onclick = () => { switchView('tracking'); renderTracking(); };
        els.ordersList.appendChild(item);
    });

    // Dashboard stats
    els.statActiveOrders.textContent = String(state.orders.length);
    els.statInTransit.textContent = String(state.orders.filter(o => o.status === 'In Transit').length);
    els.statEta.textContent = String(Math.min(state.orders.length, 3));
}

function renderTracking() {
    els.trackingList.innerHTML = '';
    state.orders.forEach(o => {
        const row = document.createElement('div');
        row.className = 'tracking-item';
        row.innerHTML = `<div><strong>${o.id}</strong><div style="color:#94a3b8;font-size:12px;">${o.route || 'Route unavailable'}</div></div><div>${o.status}</div>`;
        els.trackingList.appendChild(row);
    });
}

function renderSessionList() {
    els.conversationsList.innerHTML = '';
    if (!state.sessions.find(s => s.id === state.sessionId)) {
        state.sessions.unshift({ id: state.sessionId, label: 'New chat', createdAt: Date.now() });
        persistSessions();
    }
    state.sessions.forEach(s => {
        const item = document.createElement('div');
        item.className = 'item';
        const isActive = s.id === state.sessionId;
        item.style.borderColor = isActive ? '#3b82f6' : '';
        item.innerHTML = `<i class="fas fa-message"></i><div>${s.label || 'New chat'}</div>`;
        item.onclick = () => {
            state.sessionId = s.id;
            persistSessions();
            els.chatBox.innerHTML = '';
            loadHistory();
            switchView('chat');
        };
        els.conversationsList.appendChild(item);
    });
}

function updateActiveSessionLabelFromFirstUserMessage(text) {
    const sess = state.sessions.find(s => s.id === state.sessionId);
    if (sess && (!sess.label || sess.label === 'New chat')) {
        sess.label = (text || 'New chat').slice(0, 32);
        persistSessions();
        renderSessionList();
    }
}

// History load
async function loadHistory() {
    try {
        const resp = await fetch(`http://localhost:5000/api/history?user=${encodeURIComponent(currentUserKey())}`);
        const log = await resp.json();
        els.chatBox.innerHTML = '';
        if (Array.isArray(log) && log.length > 0) {
            state.conversations = log;
            for (let m of log) addMsg(m.content, m.role);
        } else {
            addMsg('Welcome to NITISARA Captain AI! Ask about rates, compliance, tracking, or ESG.', 'captain');
        }
        renderSessionList();
    } catch (e) {
        console.error('Failed to load history:', e);
        addMsg('Welcome to NITISARA Captain AI! How can I help today?', 'captain');
    }
}
// PDF Upload Compliance
async function uploadCompliancePDF() {
    const file = els.pdfUpload.files[0];
    if (!file) {
        els.complianceResult.innerHTML = "<p style='color:red;'>Please select a PDF file first.</p>";
        return;
    }

    const formData = new FormData();
    formData.append("file", file);

    els.complianceResult.innerHTML = "<p><i class='fas fa-spinner fa-spin'></i> Uploading and analyzing...</p>";

    try {
        const res = await fetch("http://127.0.0.1:5000/api/compliance/upload", {
            method: "POST",
            body: formData,
        });

        if (!res.ok) throw new Error("Upload failed");

        const data = await res.json();

        els.complianceResult.innerHTML = `
            <div class="result-card">
                <h3>📄 File: ${data.file_name}</h3>
                <p><strong>Product:</strong> ${data.key_fields.product_name}</p>
                <p><strong>HSN Code:</strong> ${data.key_fields.hsn_code}</p>
                <p><strong>Weight:</strong> ${data.key_fields.weight}</p>
                <hr>
                <p><strong>Summary:</strong><br>${data.summary}</p>
                <hr>
                <p><strong>Status:</strong> ${data.verification.status}</p>
                <p><strong>Remarks:</strong> ${data.verification.remarks}</p>
            </div>
        `;
    } catch (err) {
        els.complianceResult.innerHTML = `<p style='color:red;'>Error: ${err.message}</p>`;
    }
}

// Compliance shortcut using /api/rag
async function runCompliance() {
    const q = (els.complianceQuery.value || '').trim();
    if (!q) return;
    els.complianceResult.textContent = 'Checking...';
    try {
        const resp = await fetch('http://localhost:5000/api/rag', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ query: q, category: 'trade_compliance', user: state.user.id }) });
        const data = await resp.json();
        els.complianceResult.textContent = data.response || 'No result';
    } catch(e) {
        els.complianceResult.textContent = 'Failed to fetch compliance info.';
    }
}
// 🧾 Laid Bill Generator
// ==============================
// 🧾 Laid Bill Generator
// 🚢 Generate Laid Bill (Bill of Lading)
async function generateBill(event) {
    event.preventDefault();

    const data = {
        customer: document.getElementById("customer").value.trim(),
        operator: document.getElementById("operator").value.trim(),
        administrator: document.getElementById("administrator").value.trim(),
        carrier: document.getElementById("carrier").value.trim(),
        driver: document.getElementById("driver").value.trim(),
        truck_number: document.getElementById("truckNumber").value.trim(),
        trailer_number: document.getElementById("trailerNumber").value.trim(),
        gross: document.getElementById("gross").value.trim(),
        tare: document.getElementById("tare").value.trim(),
        net: document.getElementById("net").value.trim(),
        po_number: document.getElementById("poNumber").value.trim(),
        job_number: document.getElementById("jobNumber").value.trim(),
        so_number: document.getElementById("soNumber").value.trim(),
    };

    const resultDiv = document.getElementById("billResult");

    // Simple field check
    if (Object.values(data).some(v => !v)) {
        resultDiv.innerHTML = "<p style='color:red;'>Please fill all fields.</p>";
        return;
    }

    resultDiv.innerHTML = "<p><i class='fas fa-spinner fa-spin'></i> Generating Laid Bill PDF...</p>";

    try {
        const res = await fetch("http://127.0.0.1:5000/api/generate_laidbill", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify(data),
        });

        const result = await res.json();
        if (!res.ok) throw new Error(result.error || "Failed to generate bill");

        resultDiv.innerHTML = `
            <div class="result-card">
                <h3>✅ Laid Bill Generated</h3>
                <p><strong>Customer:</strong> ${result.customer}</p>
                <p><strong>Driver:</strong> ${result.driver}</p>
                <p><strong>Gross:</strong> ${result.gross}</p>
                <p><strong>Net:</strong> ${result.net}</p>
                <hr>
                <a href="${result.file_url}" download target="_blank">📥 Download Laid Bill PDF</a>
            </div>
        `;
    } catch (err) {
        resultDiv.innerHTML = `<p style='color:red;'>Error: ${err.message}</p>`;
    }
}

// Auth modal
function openAuth() { els.authModal.classList.remove('hidden'); }
function closeAuth() { els.authModal.classList.add('hidden'); }
function confirmAuth() {
    const name = (els.authUsername.value || '').trim() || 'User';
    const email = (els.authEmail.value || '').trim();
    setUser({ id: (email || name).toLowerCase().replace(/\s+/g,'_'), name, email });
    closeAuth();
    loadHistory();
}

// Events
els.sendBtn.onclick = () => sendMessage(els.msgInput.value.trim());
els.msgInput.addEventListener('keypress', (e) => { if (e.key === 'Enter') sendMessage(els.msgInput.value.trim()); });
document.querySelectorAll('.quick-btn').forEach(btn => {
    btn.addEventListener('click', () => {
        const action = btn.dataset.action;
        const map = { rate: 'I need a shipping rate quote', compliance: 'Check my compliance requirements', tracking: 'Track my shipment', esg: 'Show me ESG analytics' };
        const msg = map[action]; if (msg) { updateActiveSessionLabelFromFirstUserMessage(msg); sendMessage(msg); }
    });
});
els.tabs.forEach(t => t.addEventListener('click', () => switchView(t.dataset.view)));
els.newChatBtn.onclick = () => {
    state.sessionId = `sess_${Date.now()}`;
    state.orders = [];
    persistSessions();
    renderSessionList();
    els.chatBox.innerHTML = '';
    addMsg('New session started.', 'captain');
};
els.reloadHistoryBtn && (els.reloadHistoryBtn.onclick = () => loadHistory());
els.saveContextBtn.onclick = () => saveContext();
els.loginBtn.onclick = () => openAuth();
els.logoutBtn.onclick = () => { clearUser(); els.conversationsList.innerHTML=''; els.chatBox.innerHTML=''; loadHistory(); };
els.authCancel.onclick = () => closeAuth();
els.authConfirm.onclick = () => confirmAuth();
els.pdfUploadBtn && (els.pdfUploadBtn.onclick = () => uploadCompliancePDF());
els.billForm && els.billForm.addEventListener('submit', generateBill);


// Init
(function init() {
    els.userLabel.textContent = state.user.name || 'Guest';
    els.systemPrompt.value = state.systemPrompt;
    els.sessionContext.value = state.sessionContext;
    if (state.user.id === 'guest') { els.loginBtn.classList.remove('hidden'); els.logoutBtn.classList.add('hidden'); } else { els.loginBtn.classList.add('hidden'); els.logoutBtn.classList.remove('hidden'); }
    loadHistory();
})();
