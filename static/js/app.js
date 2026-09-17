document.addEventListener("DOMContentLoaded", () => {
    // Tab Navigation
    const tabs = document.querySelectorAll(".nav-tab");
    const panels = document.querySelectorAll(".tab-panel");

    tabs.forEach(tab => {
        tab.addEventListener("click", () => {
            const targetId = `panel-${tab.dataset.tab}`;
            tabs.forEach(t => t.classList.remove("active"));
            panels.forEach(p => p.classList.remove("active"));
            tab.classList.add("active");
            document.getElementById(targetId)?.classList.add("active");

            if (tab.dataset.tab === "documents") {
                loadDocuments();
            }
        });
    });

    // System Health Check
    async function checkHealth() {
        const pill = document.getElementById("system-status-pill");
        const label = document.getElementById("system-status-text");
        try {
            const res = await fetch("/health");
            const data = await res.json();
            if (data.status === "healthy") {
                pill.style.background = "rgba(16, 185, 129, 0.15)";
                pill.style.borderColor = "rgba(16, 185, 129, 0.3)";
                label.style.color = "#10B981";
                label.textContent = "All Systems Operational";
            } else if (data.status === "degraded") {
                pill.style.background = "rgba(245, 158, 11, 0.15)";
                pill.style.borderColor = "rgba(245, 158, 11, 0.3)";
                label.style.color = "#F59E0B";
                label.textContent = "Memory Degraded";
            } else {
                pill.style.background = "rgba(239, 68, 68, 0.15)";
                pill.style.borderColor = "rgba(239, 68, 68, 0.3)";
                label.style.color = "#EF4444";
                label.textContent = "Service Offline";
            }
        } catch (err) {
            pill.style.background = "rgba(239, 68, 68, 0.15)";
            label.style.color = "#EF4444";
            label.textContent = "Disconnected";
        }
    }
    checkHealth();
    setInterval(checkHealth, 20000);

    // ==========================================
    // 1. CHAT LOGIC
    // ==========================================
    const chatMessages = document.getElementById("chat-messages");
    const chatForm = document.getElementById("chat-form");
    const chatInput = document.getElementById("chat-input");
    const sessionInput = document.getElementById("session-id-input");
    const btnLoadSession = document.getElementById("btn-load-session");
    const btnNewSession = document.getElementById("btn-new-session");
    const btnClearHistory = document.getElementById("btn-clear-history");
    const paramTopK = document.getElementById("param-topk");
    const paramThreshold = document.getElementById("param-threshold");
    const topkVal = document.getElementById("topk-val");
    const thresholdVal = document.getElementById("threshold-val");

    paramTopK.addEventListener("input", () => topkVal.textContent = paramTopK.value);
    paramThreshold.addEventListener("input", () => thresholdVal.textContent = paramThreshold.value);

    // Auto-resize chat textarea
    chatInput.addEventListener("input", function() {
        this.style.height = "auto";
        this.style.height = (this.scrollHeight) + "px";
    });

    chatInput.addEventListener("keydown", function(e) {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            chatForm.dispatchEvent(new Event("submit"));
        }
    });

    document.querySelectorAll(".chip").forEach(chip => {
        chip.addEventListener("click", () => {
            chatInput.value = chip.dataset.q;
            chatForm.dispatchEvent(new Event("submit"));
        });
    });

    async function loadChatHistory() {
        const sessionId = sessionInput.value.trim() || "default";
        try {
            const res = await fetch(`/api/v1/chat/history/${encodeURIComponent(sessionId)}`);
            if (!res.ok) return;
            const data = await res.json();
            
            chatMessages.innerHTML = "";
            if (data.messages && data.messages.length > 0) {
                data.messages.forEach(msg => {
                    appendMessage(msg.role, msg.content);
                });
            } else {
                renderWelcomeCard();
            }
        } catch (e) {
            console.error("Failed to load session history:", e);
        }
    }

    function renderWelcomeCard() {
        chatMessages.innerHTML = `
            <div class="welcome-card">
                <div class="welcome-badge">⚡ DocQuery RAG Active</div>
                <h2>Welcome to your Document Assistant</h2>
                <p>Ask questions grounded directly in your company documents. The assistant uses <strong>PostgreSQL pgvector</strong> for dense semantic retrieval, retains context via <strong>Redis memory</strong>, and generates citations for every response.</p>
                <div class="quick-questions">
                    <span>Try asking:</span>
                    <button class="chip" data-q="How many annual leave days do interns receive?">Leave days for interns?</button>
                    <button class="chip" data-q="What is the policy for emergency leave?">Emergency leave policy?</button>
                    <button class="chip" data-q="Who approves leave requests?">Approval process?</button>
                </div>
            </div>
        `;
        document.querySelectorAll(".chip").forEach(chip => {
            chip.addEventListener("click", () => {
                chatInput.value = chip.dataset.q;
                chatForm.dispatchEvent(new Event("submit"));
            });
        });
    }

    btnLoadSession.addEventListener("click", loadChatHistory);
    btnNewSession.addEventListener("click", () => {
        sessionInput.value = "session-" + Math.random().toString(36).substring(2, 7);
        loadChatHistory();
    });

    btnClearHistory.addEventListener("click", async () => {
        const sessionId = sessionInput.value.trim() || "default";
        if (confirm(`Clear all conversation memory for session '${sessionId}'?`)) {
            await fetch(`/api/v1/chat/history/${encodeURIComponent(sessionId)}`, { method: "DELETE" });
            renderWelcomeCard();
        }
    });

    function appendMessage(role, text, sources = []) {
        // Remove welcome card if present
        const welcomeCard = chatMessages.querySelector(".welcome-card");
        if (welcomeCard) welcomeCard.remove();

        const bubble = document.createElement("div");
        bubble.className = `message-bubble ${role}`;

        const avatar = document.createElement("div");
        avatar.className = "message-avatar";
        avatar.textContent = role === "user" ? "You" : "AI";

        const content = document.createElement("div");
        content.className = "message-content";

        const msgText = document.createElement("div");
        msgText.className = "message-text";
        msgText.innerHTML = formatMarkdown(text);
        content.appendChild(msgText);

        if (sources && sources.length > 0) {
            const citationsRow = document.createElement("div");
            citationsRow.className = "citations-row";
            sources.forEach(src => {
                const pill = document.createElement("button");
                pill.type = "button";
                pill.className = "citation-pill";
                pill.innerHTML = `<span>📄</span> ${src.source} [C${src.chunk_index}] • ${(src.similarity * 100).toFixed(0)}%`;
                pill.addEventListener("click", () => openCitationModal(src));
                citationsRow.appendChild(pill);
            });
            content.appendChild(citationsRow);
        }

        bubble.appendChild(avatar);
        bubble.appendChild(content);
        chatMessages.appendChild(bubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }

    function formatMarkdown(str) {
        if (!str) return "";
        return str
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/\*(.*?)\*/g, "<em>$1</em>")
            .replace(/`([^`]+)`/g, "<code>$1</code>")
            .replace(/\n/g, "<br>");
    }

    chatForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const question = chatInput.value.trim();
        if (!question) return;

        const sessionId = sessionInput.value.trim() || "default";
        const topK = parseInt(paramTopK.value, 10);
        const threshold = parseFloat(paramThreshold.value);

        appendMessage("user", question);
        chatInput.value = "";
        chatInput.style.height = "auto";

        // Add loading placeholder
        const loadingId = "loading-" + Date.now();
        const loadingBubble = document.createElement("div");
        loadingBubble.className = "message-bubble assistant";
        loadingBubble.id = loadingId;
        loadingBubble.innerHTML = `
            <div class="message-avatar">AI</div>
            <div class="message-content">
                <div class="message-text">
                    <span class="spinner"></span> Searching knowledge base & generating grounded response...
                </div>
            </div>
        `;
        chatMessages.appendChild(loadingBubble);
        chatMessages.scrollTop = chatMessages.scrollHeight;

        try {
            const res = await fetch("/api/v1/chat", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    question: question,
                    session_id: sessionId,
                    top_k: topK,
                    similarity_threshold: threshold,
                    include_sources: true
                })
            });

            const data = await res.json();
            document.getElementById(loadingId)?.remove();

            if (res.ok) {
                appendMessage("assistant", data.answer, data.sources);
            } else {
                appendMessage("assistant", `❌ Error: ${data.detail || "Unable to retrieve response."}`);
            }
        } catch (err) {
            document.getElementById(loadingId)?.remove();
            appendMessage("assistant", `❌ Network error: ${err.message}`);
        }
    });

    // ==========================================
    // 2. DOCUMENTS LOGIC
    // ==========================================
    const dropzone = document.getElementById("upload-dropzone");
    const dropzoneTrigger = document.getElementById("dropzone-trigger");
    const fileInput = document.getElementById("file-input");
    const uploadProgress = document.getElementById("upload-progress");
    const documentsGrid = document.getElementById("documents-grid");
    const docCount = document.getElementById("doc-count");
    const chunkCountBadge = document.getElementById("chunk-count-badge");
    const btnScanFolder = document.getElementById("btn-scan-folder");

    dropzoneTrigger.addEventListener("click", () => fileInput.click());

    dropzone.addEventListener("dragover", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--accent-primary)";
    });

    dropzone.addEventListener("dragleave", () => {
        dropzone.style.borderColor = "var(--border-accent)";
    });

    dropzone.addEventListener("drop", (e) => {
        e.preventDefault();
        dropzone.style.borderColor = "var(--border-accent)";
        if (e.dataTransfer.files.length > 0) {
            handleFileUpload(e.dataTransfer.files[0]);
        }
    });

    fileInput.addEventListener("change", () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]);
        }
    });

    async function handleFileUpload(file) {
        const formData = new FormData();
        formData.append("file", file);

        dropzoneTrigger.style.display = "none";
        uploadProgress.style.display = "block";

        try {
            const res = await fetch("/api/v1/documents/upload", {
                method: "POST",
                body: formData
            });
            const data = await res.json();
            if (res.ok) {
                alert(`Success: ${data.message}`);
                loadDocuments();
            } else {
                alert(`Error: ${data.detail}`);
            }
        } catch (err) {
            alert(`Upload failed: ${err.message}`);
        } finally {
            dropzoneTrigger.style.display = "block";
            uploadProgress.style.display = "none";
            fileInput.value = "";
        }
    }

    async function loadDocuments() {
        try {
            const res = await fetch("/api/v1/documents");
            const data = await res.json();
            docCount.textContent = data.total_documents;
            chunkCountBadge.textContent = `${data.total_chunks} Chunks in DB`;

            documentsGrid.innerHTML = "";
            if (data.documents.length === 0) {
                documentsGrid.innerHTML = `<p class="placeholder-text">No documents indexed. Upload a file above or re-scan the folder.</p>`;
                return;
            }

            data.documents.forEach(doc => {
                const card = document.createElement("div");
                card.className = "doc-card";
                card.innerHTML = `
                    <div class="doc-card-header">
                        <span class="doc-title">📄 ${doc.source}</span>
                        <button class="btn-delete-doc" title="Delete document" data-source="${doc.source}">
                            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/></svg>
                        </button>
                    </div>
                    <div class="doc-meta">
                        <span><strong>${doc.chunk_count}</strong> chunks</span>
                        <span>•</span>
                        <span>Hash: <code>${doc.file_hash.substring(0, 8)}</code></span>
                    </div>
                    <div class="doc-preview">"${doc.preview || 'No preview available.'}"</div>
                `;
                card.querySelector(".btn-delete-doc").addEventListener("click", async (e) => {
                    const src = e.currentTarget.dataset.source;
                    if (confirm(`Delete '${src}' and all its vector chunks?`)) {
                        await fetch(`/api/v1/documents/${encodeURIComponent(src)}`, { method: "DELETE" });
                        loadDocuments();
                    }
                });
                documentsGrid.appendChild(card);
            });
        } catch (e) {
            documentsGrid.innerHTML = `<p class="placeholder-text">Failed to load documents: ${e.message}</p>`;
        }
    }

    btnScanFolder.addEventListener("click", async () => {
        try {
            btnScanFolder.disabled = true;
            btnScanFolder.textContent = "Scanning...";
            const res = await fetch("/api/v1/documents/ingest-folder", { method: "POST" });
            const data = await res.json();
            alert(`Folder Scan Complete:\n• Ingested/Updated: ${data.ingested}\n• Unchanged (Skipped): ${data.skipped}\n• Chunks: ${data.total_chunks}`);
            loadDocuments();
        } catch (err) {
            alert(`Scan failed: ${err.message}`);
        } finally {
            btnScanFolder.disabled = false;
            btnScanFolder.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Re-Scan /documents Folder`;
        }
    });

    // ==========================================
    // 3. VECTOR EXPLORER LOGIC
    // ==========================================
    const explorerQuery = document.getElementById("explorer-query");
    const btnRunSearch = document.getElementById("btn-run-search");
    const searchResultsList = document.getElementById("search-results-list");
    const searchResultCount = document.getElementById("search-result-count");

    async function runVectorSearch() {
        const query = explorerQuery.value.trim();
        if (!query) return;

        searchResultsList.innerHTML = `<div class="loading-state"><span class="spinner"></span> Computing query embedding and calculating cosine distances...</div>`;

        try {
            const res = await fetch("/api/v1/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    top_k: 5,
                    similarity_threshold: 0.1
                })
            });
            const data = await res.json();
            searchResultCount.textContent = data.total_results;
            searchResultsList.innerHTML = "";

            if (data.results.length === 0) {
                searchResultsList.innerHTML = `<p class="placeholder-text">No matching vectors found.</p>`;
                return;
            }

            data.results.forEach((item, idx) => {
                const simPct = (item.similarity * 100).toFixed(1);
                const card = document.createElement("div");
                card.className = "search-result-card";
                card.innerHTML = `
                    <div class="result-card-header">
                        <span><strong>#${idx + 1}</strong> • 📄 ${item.source} (Chunk ${item.chunk_index})</span>
                        <div class="similarity-bar-wrapper">
                            <span class="setting-val">${simPct}% match</span>
                            <div class="sim-bar">
                                <div class="sim-fill" style="width: ${simPct}%;"></div>
                            </div>
                            <span class="badge badge-subtle">dist: ${item.distance.toFixed(4)}</span>
                        </div>
                    </div>
                    <div class="doc-preview">"${item.content}"</div>
                `;
                searchResultsList.appendChild(card);
            });
        } catch (err) {
            searchResultsList.innerHTML = `<p class="placeholder-text">Search failed: ${err.message}</p>`;
        }
    }

    btnRunSearch.addEventListener("click", runVectorSearch);
    explorerQuery.addEventListener("keydown", (e) => {
        if (e.key === "Enter") runVectorSearch();
    });

    // ==========================================
    // 4. AGENT LOGIC
    // ==========================================
    const agentPrompt = document.getElementById("agent-prompt");
    const btnRunAgent = document.getElementById("btn-run-agent");
    const agentOutputCard = document.getElementById("agent-output-card");
    const agentToolsUsed = document.getElementById("agent-tools-used");
    const agentAnswer = document.getElementById("agent-answer");

    btnRunAgent.addEventListener("click", async () => {
        const prompt = agentPrompt.value.trim();
        if (!prompt) return;

        btnRunAgent.disabled = true;
        btnRunAgent.textContent = "Agent Executing Tools...";
        agentOutputCard.style.display = "none";

        try {
            const res = await fetch("/api/v1/agent/run", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ prompt: prompt, session_id: "agent-demo" })
            });
            const data = await res.json();
            agentToolsUsed.innerHTML = "";
            (data.tools_used || []).forEach(t => {
                const badge = document.createElement("div");
                badge.className = "tool-badge";
                badge.innerHTML = `⚙️ Tool <strong>${t.tool_name}</strong> ➔ ${t.tool_output}`;
                agentToolsUsed.appendChild(badge);
            });
            agentAnswer.innerHTML = formatMarkdown(data.answer);
            agentOutputCard.style.display = "flex";
        } catch (err) {
            alert(`Agent failed: ${err.message}`);
        } finally {
            btnRunAgent.disabled = false;
            btnRunAgent.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg> Execute Agent Task`;
        }
    });

    // ==========================================
    // 5. CITATION MODAL LOGIC
    // ==========================================
    const modal = document.getElementById("citation-modal");
    const modalClose = document.getElementById("modal-close");
    const modalTitle = document.getElementById("modal-source-title");
    const modalSimBadge = document.getElementById("modal-sim-badge");
    const modalChunkBadge = document.getElementById("modal-chunk-badge");
    const modalText = document.getElementById("modal-chunk-text");

    function openCitationModal(src) {
        modalTitle.textContent = `Source: ${src.source}`;
        modalSimBadge.textContent = `Cosine Similarity: ${(src.similarity * 100).toFixed(1)}%`;
        modalChunkBadge.textContent = `Chunk Index: ${src.chunk_index} (Distance: ${src.distance.toFixed(4)})`;
        modalText.textContent = src.content;
        modal.classList.add("active");
    }

    modalClose.addEventListener("click", () => modal.classList.remove("active"));
    modal.addEventListener("click", (e) => {
        if (e.target === modal) modal.classList.remove("active");
    });
});
