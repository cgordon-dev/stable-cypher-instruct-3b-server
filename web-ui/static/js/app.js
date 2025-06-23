// Stable Cypher Instruct 3B Web UI Application
class CypherApp {
    constructor() {
        this.socket = null;
        this.charts = {};
        this.settings = {
            maxTokens: 512,
            temperature: 0.7,
            topP: 0.9
        };
        this.metricsHistory = {
            tokens: [],
            requests: [],
            timestamps: []
        };
        this.maxHistoryPoints = 20;
    }

    init() {
        this.initializeElements();
        this.initializeSocket();
        this.initializeEventListeners();
        this.initializeCharts();
        this.loadSettings();
        this.loadExamples();
        this.checkHealth();
        
        console.log('Cypher App initialized');
    }

    initializeElements() {
        this.elements = {
            chatForm: document.getElementById('chat-form'),
            chatInput: document.getElementById('chat-input'),
            chatMessages: document.getElementById('chat-messages'),
            sendBtn: document.getElementById('send-btn'),
            clearChatBtn: document.getElementById('clear-chat'),
            exportChatBtn: document.getElementById('export-chat'),
            settingsBtn: document.getElementById('settings-btn'),
            saveSettingsBtn: document.getElementById('save-settings'),
            themeToggle: document.getElementById('theme-toggle'),
            healthStatus: document.getElementById('health-status'),
            loadingOverlay: document.getElementById('loading-overlay'),
            examplesContainer: document.getElementById('examples-container'),
            
            // Settings
            maxTokensSlider: document.getElementById('max-tokens'),
            temperatureSlider: document.getElementById('temperature'),
            topPSlider: document.getElementById('top-p'),
            maxTokensValue: document.getElementById('max-tokens-value'),
            temperatureValue: document.getElementById('temperature-value'),
            topPValue: document.getElementById('top-p-value'),
            
            // Metrics
            healthMetric: document.getElementById('health-metric'),
            activeRequestsMetric: document.getElementById('active-requests-metric'),
            tokensPerSecondMetric: document.getElementById('tokens-per-second-metric'),
            totalRequests: document.getElementById('total-requests'),
            totalTokens: document.getElementById('total-tokens'),
            avgGenerationTime: document.getElementById('avg-generation-time'),
            metricsStatus: document.getElementById('metrics-status')
        };
    }

    initializeSocket() {
        this.socket = io();
        
        this.socket.on('connect', () => {
            console.log('Socket connected');
            this.updateMetricsStatus('Live', 'success');
        });
        
        this.socket.on('disconnect', () => {
            console.log('Socket disconnected');
            this.updateMetricsStatus('Offline', 'danger');
        });
        
        this.socket.on('metrics_update', (metrics) => {
            this.updateMetrics(metrics);
        });
    }

    initializeEventListeners() {
        // Chat form
        this.elements.chatForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.sendMessage();
        });

        // Enter key in textarea (but allow Shift+Enter for new lines)
        this.elements.chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        // Clear chat
        this.elements.clearChatBtn.addEventListener('click', () => {
            this.clearChat();
        });

        // Export chat
        this.elements.exportChatBtn.addEventListener('click', () => {
            this.exportChat();
        });

        // Settings sliders
        this.elements.maxTokensSlider.addEventListener('input', (e) => {
            this.elements.maxTokensValue.textContent = e.target.value;
        });

        this.elements.temperatureSlider.addEventListener('input', (e) => {
            this.elements.temperatureValue.textContent = e.target.value;
        });

        this.elements.topPSlider.addEventListener('input', (e) => {
            this.elements.topPValue.textContent = e.target.value;
        });

        // Save settings
        this.elements.saveSettingsBtn.addEventListener('click', () => {
            this.saveSettings();
        });

        // Theme toggle
        this.elements.themeToggle.addEventListener('click', () => {
            this.toggleTheme();
        });

        // Smooth scrolling for navigation
        document.querySelectorAll('a[href^="#"]').forEach(anchor => {
            anchor.addEventListener('click', (e) => {
                e.preventDefault();
                const target = document.querySelector(anchor.getAttribute('href'));
                if (target) {
                    target.scrollIntoView({ behavior: 'smooth' });
                }
            });
        });
    }

    initializeCharts() {
        // Tokens per second chart
        const tokensCtx = document.getElementById('tokensChart').getContext('2d');
        this.charts.tokens = new Chart(tokensCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Tokens/Second',
                    data: [],
                    borderColor: '#198754',
                    backgroundColor: 'rgba(25, 135, 84, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });

        // Requests chart
        const requestsCtx = document.getElementById('requestsChart').getContext('2d');
        this.charts.requests = new Chart(requestsCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'Active Requests',
                    data: [],
                    borderColor: '#0dcaf0',
                    backgroundColor: 'rgba(13, 202, 240, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false }
                },
                scales: {
                    y: { beginAtZero: true }
                }
            }
        });
    }

    async sendMessage() {
        const prompt = this.elements.chatInput.value.trim();
        if (!prompt) return;

        // Disable input and show loading
        this.setUIState(false);
        this.showTypingIndicator();

        try {
            // Add user message to chat
            this.addMessage('user', prompt);
            this.elements.chatInput.value = '';

            // Send request to API
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    prompt: prompt,
                    max_tokens: this.settings.maxTokens,
                    temperature: this.settings.temperature,
                    top_p: this.settings.topP
                })
            });

            const data = await response.json();

            if (response.ok) {
                this.hideTypingIndicator();
                this.addMessage('assistant', data.response, data);
            } else {
                this.hideTypingIndicator();
                this.addMessage('assistant', `Error: ${data.error}`, null, true);
            }
        } catch (error) {
            this.hideTypingIndicator();
            this.addMessage('assistant', `Network error: ${error.message}`, null, true);
        } finally {
            this.setUIState(true);
        }
    }

    addMessage(role, content, metadata = null, isError = false) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `chat-message ${role}`;

        const bubbleDiv = document.createElement('div');
        bubbleDiv.className = `message-bubble ${role}`;
        
        if (isError) {
            bubbleDiv.classList.add('border-danger');
        }

        // Process content for code blocks
        const processedContent = this.processMessageContent(content);

        let metaHtml = '';
        if (metadata) {
            const duration = metadata.duration ? `${metadata.duration.toFixed(2)}s` : '';
            const tokens = metadata.usage ? metadata.usage.completion_tokens || 0 : 0;
            metaHtml = `
                <div class="message-meta">
                    ${duration} • ${tokens} tokens
                </div>
            `;
        }

        bubbleDiv.innerHTML = `
            <div class="message-content">${processedContent}</div>
            ${metaHtml}
            ${role === 'assistant' && !isError ? this.getMessageActions(content) : ''}
        `;

        messageDiv.appendChild(bubbleDiv);
        this.elements.chatMessages.appendChild(messageDiv);
        this.scrollToBottom();

        // Initialize syntax highlighting
        if (bubbleDiv.querySelector('code')) {
            Prism.highlightAllUnder(bubbleDiv);
        }
    }

    processMessageContent(content) {
        // Convert code blocks to proper HTML with syntax highlighting
        return content
            .replace(/```cypher\n([\s\S]*?)\n```/g, (match, code) => {
                return `<div class="cypher-code"><pre><code class="language-cypher">${this.escapeHtml(code)}</code></pre><button class="copy-btn" onclick="cypherApp.copyToClipboard('${this.escapeHtml(code).replace(/'/g, "\\'")}')">Copy</button></div>`;
            })
            .replace(/```\n([\s\S]*?)\n```/g, (match, code) => {
                return `<div class="cypher-code"><pre><code>${this.escapeHtml(code)}</code></pre><button class="copy-btn" onclick="cypherApp.copyToClipboard('${this.escapeHtml(code).replace(/'/g, "\\'")}')">Copy</button></div>`;
            })
            .replace(/`([^`]+)`/g, '<code>$1</code>')
            .replace(/\n/g, '<br>');
    }

    getMessageActions(content) {
        return `
            <div class="message-actions">
                <button class="btn btn-outline-secondary btn-sm" onclick="cypherApp.copyToClipboard('${this.escapeHtml(content).replace(/'/g, "\\'")}')">
                    <i class="fas fa-copy"></i>
                </button>
                <button class="btn btn-outline-secondary btn-sm" onclick="cypherApp.useAsPrompt('${this.escapeHtml(content).replace(/'/g, "\\'")}')">
                    <i class="fas fa-redo"></i>
                </button>
            </div>
        `;
    }

    showTypingIndicator() {
        const indicator = document.createElement('div');
        indicator.className = 'typing-indicator';
        indicator.id = 'typing-indicator';
        indicator.innerHTML = `
            <span class="text-muted">Assistant is typing</span>
            <div class="typing-dots">
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
                <div class="typing-dot"></div>
            </div>
        `;
        this.elements.chatMessages.appendChild(indicator);
        this.scrollToBottom();
    }

    hideTypingIndicator() {
        const indicator = document.getElementById('typing-indicator');
        if (indicator) {
            indicator.remove();
        }
    }

    setUIState(enabled) {
        this.elements.chatInput.disabled = !enabled;
        this.elements.sendBtn.disabled = !enabled;
        
        if (enabled) {
            this.elements.sendBtn.innerHTML = '<i class="fas fa-paper-plane"></i>';
        } else {
            this.elements.sendBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
        }
    }

    scrollToBottom() {
        this.elements.chatMessages.scrollTop = this.elements.chatMessages.scrollHeight;
    }

    async clearChat() {
        if (confirm('Are you sure you want to clear the chat history?')) {
            try {
                await fetch('/api/chat/clear', { method: 'POST' });
                this.elements.chatMessages.innerHTML = `
                    <div class="text-center text-muted">
                        <i class="fas fa-comments fa-2x mb-2"></i>
                        <p>Chat cleared. Ask me to generate Cypher queries!</p>
                    </div>
                `;
            } catch (error) {
                console.error('Failed to clear chat:', error);
            }
        }
    }

    async exportChat() {
        try {
            const response = await fetch('/api/chat/history');
            const history = await response.json();
            
            const blob = new Blob([JSON.stringify(history, null, 2)], {
                type: 'application/json'
            });
            
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `cypher-chat-${new Date().toISOString().split('T')[0]}.json`;
            a.click();
            URL.revokeObjectURL(url);
        } catch (error) {
            console.error('Failed to export chat:', error);
        }
    }

    loadSettings() {
        const saved = localStorage.getItem('cypherAppSettings');
        if (saved) {
            this.settings = { ...this.settings, ...JSON.parse(saved) };
        }
        
        this.elements.maxTokensSlider.value = this.settings.maxTokens;
        this.elements.temperatureSlider.value = this.settings.temperature;
        this.elements.topPSlider.value = this.settings.topP;
        
        this.elements.maxTokensValue.textContent = this.settings.maxTokens;
        this.elements.temperatureValue.textContent = this.settings.temperature;
        this.elements.topPValue.textContent = this.settings.topP;
    }

    saveSettings() {
        this.settings = {
            maxTokens: parseInt(this.elements.maxTokensSlider.value),
            temperature: parseFloat(this.elements.temperatureSlider.value),
            topP: parseFloat(this.elements.topPSlider.value)
        };
        
        localStorage.setItem('cypherAppSettings', JSON.stringify(this.settings));
        
        // Close modal
        const modal = bootstrap.Modal.getInstance(document.getElementById('settingsModal'));
        modal.hide();
        
        this.showToast('Settings saved successfully!');
    }

    async loadExamples() {
        try {
            const response = await fetch('/api/examples');
            const examples = await response.json();
            
            this.elements.examplesContainer.innerHTML = examples.map(example => `
                <div class="col-md-4">
                    <div class="card example-card h-100" onclick="cypherApp.useExample('${this.escapeHtml(example.prompt)}')">
                        <div class="card-body">
                            <div class="d-flex justify-content-between align-items-start mb-2">
                                <h6 class="card-title">${example.title}</h6>
                                <span class="badge bg-secondary example-category">${example.category}</span>
                            </div>
                            <p class="card-text text-muted small">${example.prompt}</p>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Failed to load examples:', error);
        }
    }

    useExample(prompt) {
        this.elements.chatInput.value = prompt;
        this.elements.chatInput.focus();
        
        // Scroll to chat section
        document.getElementById('chat-section').scrollIntoView({ behavior: 'smooth' });
    }

    async checkHealth() {
        try {
            const response = await fetch('/api/health');
            const health = await response.json();
            
            let statusClass = 'text-success';
            let statusIcon = 'fa-circle';
            let statusText = 'Healthy';
            
            if (health.status === 'degraded') {
                statusClass = 'text-warning';
                statusText = 'Degraded';
            } else if (health.status === 'unhealthy') {
                statusClass = 'text-danger';
                statusText = 'Unhealthy';
            }
            
            this.elements.healthStatus.innerHTML = `
                <i class="fas ${statusIcon} ${statusClass}"></i> ${statusText}
            `;
        } catch (error) {
            this.elements.healthStatus.innerHTML = `
                <i class="fas fa-circle text-danger"></i> Offline
            `;
        }
    }

    updateMetrics(metrics) {
        if (metrics.error) {
            console.error('Metrics error:', metrics.error);
            return;
        }

        // Update metric displays
        this.elements.healthMetric.textContent = metrics.health_status || 'Unknown';
        this.elements.healthMetric.className = `health-${metrics.health_status}`;
        
        this.elements.activeRequestsMetric.textContent = metrics.active_requests || 0;
        this.elements.tokensPerSecondMetric.textContent = 
            Math.round(metrics.avg_tokens_per_second || 0);
        
        this.elements.totalRequests.textContent = Math.round(metrics.requests_total || 0);
        this.elements.totalTokens.textContent = Math.round(metrics.tokens_generated_total || 0);
        this.elements.avgGenerationTime.textContent = 
            `${Math.round(metrics.generation_duration_avg * 1000 || 0)}ms`;

        // Update charts
        this.updateChartsData(metrics);
    }

    updateChartsData(metrics) {
        const now = new Date().toLocaleTimeString();
        
        // Add new data points
        this.metricsHistory.timestamps.push(now);
        this.metricsHistory.tokens.push(metrics.avg_tokens_per_second || 0);
        this.metricsHistory.requests.push(metrics.active_requests || 0);
        
        // Keep only recent data
        if (this.metricsHistory.timestamps.length > this.maxHistoryPoints) {
            this.metricsHistory.timestamps.shift();
            this.metricsHistory.tokens.shift();
            this.metricsHistory.requests.shift();
        }
        
        // Update tokens chart
        this.charts.tokens.data.labels = [...this.metricsHistory.timestamps];
        this.charts.tokens.data.datasets[0].data = [...this.metricsHistory.tokens];
        this.charts.tokens.update('none');
        
        // Update requests chart
        this.charts.requests.data.labels = [...this.metricsHistory.timestamps];
        this.charts.requests.data.datasets[0].data = [...this.metricsHistory.requests];
        this.charts.requests.update('none');
    }

    updateMetricsStatus(status, type) {
        this.elements.metricsStatus.textContent = status;
        this.elements.metricsStatus.className = `badge bg-${type} live-indicator`;
    }

    toggleTheme() {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
        
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        
        const icon = this.elements.themeToggle.querySelector('i');
        icon.className = newTheme === 'dark' ? 'fas fa-sun' : 'fas fa-moon';
    }

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            this.showToast('Copied to clipboard!');
        });
    }

    useAsPrompt(text) {
        this.elements.chatInput.value = text;
        this.elements.chatInput.focus();
    }

    showToast(message) {
        // Simple toast implementation
        const toast = document.createElement('div');
        toast.className = 'position-fixed top-0 end-0 m-3 alert alert-success alert-dismissible';
        toast.style.zIndex = '9999';
        toast.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(toast);
        
        setTimeout(() => {
            toast.remove();
        }, 3000);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize app
window.cypherApp = new CypherApp();

// Initialize theme
const savedTheme = localStorage.getItem('theme') || 'light';
document.documentElement.setAttribute('data-theme', savedTheme);