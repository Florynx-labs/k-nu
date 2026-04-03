// KÁNU Local Dashboard - JavaScript
const API_BASE = 'http://localhost:5000/api';

// State
let lossChart = null;
let resourceChart = null;
let trainingInterval = null;
let monitorInterval = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    initTabs();
    initCharts();
    checkSystemStatus();
    loadSavedConfig();
    loadChatHistory();
    loadTrainingHistory();
    initDarkMode();
    
    // Auto-refresh system status every 5 seconds
    setInterval(checkSystemStatus, 5000);
    
    // Enter key to send message
    document.getElementById('chatInput').addEventListener('keydown', (e) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
});

// Load saved configuration
function loadSavedConfig() {
    const savedModel = localStorage.getItem('kanu_model_size');
    const savedDevice = localStorage.getItem('kanu_device');
    
    if (savedModel) {
        document.getElementById('configModelSize').value = savedModel;
    }
    if (savedDevice) {
        document.getElementById('configDevice').value = savedDevice;
    }
}

// Save configuration
function saveConfig(modelSize, device) {
    localStorage.setItem('kanu_model_size', modelSize);
    localStorage.setItem('kanu_device', device);
    localStorage.setItem('kanu_last_load', new Date().toISOString());
}

// Tab Management
function initTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            const tabName = btn.dataset.tab;
            
            // Update buttons
            tabBtns.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            
            // Update panes
            document.querySelectorAll('.tab-pane').forEach(pane => {
                pane.classList.remove('active');
            });
            document.getElementById(tabName).classList.add('active');
            
            // Load data for specific tabs
            if (tabName === 'dataset') loadDataset();
            if (tabName === 'monitor') refreshMonitor();
        });
    });
}

// System Status
async function checkSystemStatus() {
    try {
        const response = await fetch(`${API_BASE}/system/status`);
        const data = await response.json();
        
        const indicator = document.getElementById('statusIndicator');
        const statusText = document.getElementById('statusText');
        
        if (data.orchestrator_loaded) {
            indicator.classList.add('active');
            statusText.textContent = 'System Loaded';
        } else {
            indicator.classList.remove('active');
            statusText.textContent = 'System Not Loaded';
        }
    } catch (error) {
        console.error('Status check failed:', error);
    }
}

// Load System
async function loadSystem() {
    const modelSize = document.getElementById('configModelSize').value;
    const checkpoint = document.getElementById('configCheckpoint').value;
    const device = document.getElementById('configDevice').value;
    
    const statusDiv = document.getElementById('loadStatus');
    statusDiv.textContent = 'Loading system...';
    statusDiv.className = 'load-status';
    
    try {
        const response = await fetch(`${API_BASE}/system/load`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                model_size: modelSize,
                checkpoint: checkpoint || null,
                device: device
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Save configuration
            saveConfig(modelSize, device);
            
            statusDiv.className = 'load-status success';
            statusDiv.innerHTML = `
                <h4>✓ System Loaded Successfully</h4>
                <p>Model: ${modelSize.toUpperCase()}</p>
                <p>Parameters: ${data.parameters}</p>
                <p>Device: ${data.device.toUpperCase()}</p>
            `;
            checkSystemStatus();
        } else {
            throw new Error(data.error);
        }
    } catch (error) {
        statusDiv.className = 'load-status error';
        statusDiv.innerHTML = `<h4>❌ Error</h4><p>${error.message}</p>`;
    }
}

// Chat Functions
async function sendMessage() {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    
    if (!message) return;
    
    const mode = document.querySelector('input[name="mode"]:checked').value;
    
    // Add user message to UI
    addMessageToChat('user', message);
    input.value = '';
    
    // Show typing indicator
    const typingId = addTypingIndicator();
    
    try {
        const response = await fetch(`${API_BASE}/chat`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message, mode })
        });
        
        const data = await response.json();
        
        // Remove typing indicator
        removeTypingIndicator(typingId);
        
        if (data.success) {
            addMessageToChat('assistant', data.response);
            
            // Save to history
            saveChatMessage(message, data.response, mode);
            
            // Update info
            document.getElementById('chatMode').textContent = data.mode;
            document.getElementById('chatSource').textContent = data.source;
            
            const physicsEl = document.getElementById('chatPhysics');
            if (data.physics_validated) {
                physicsEl.textContent = '✓ Valid';
                physicsEl.className = 'status-ok';
            } else {
                physicsEl.textContent = '⚠ Warnings';
                physicsEl.className = 'status-warning';
            }
            
            // Show warnings if any
            if (data.warnings && data.warnings.length > 0) {
                const warningsBox = document.getElementById('warningsBox');
                const warningsList = document.getElementById('warningsList');
                warningsList.innerHTML = data.warnings.map(w => `<li>${w}</li>`).join('');
                warningsBox.style.display = 'block';
            } else {
                document.getElementById('warningsBox').style.display = 'none';
            }
        } else {
            addMessageToChat('system', `Error: ${data.error}`);
        }
    } catch (error) {
        removeTypingIndicator(typingId);
        addMessageToChat('system', `Error: ${error.message}`);
    }
}

// Typing indicator
function addTypingIndicator() {
    const messagesDiv = document.getElementById('chatMessages');
    const typingDiv = document.createElement('div');
    const id = 'typing-' + Date.now();
    typingDiv.id = id;
    typingDiv.className = 'message assistant typing';
    typingDiv.innerHTML = `
        <div class="message-meta">KÁNU</div>
        <div class="typing-indicator">
            <span></span><span></span><span></span>
        </div>
    `;
    messagesDiv.appendChild(typingDiv);
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    const el = document.getElementById(id);
    if (el) el.remove();
}

// Save chat history
function saveChatMessage(userMsg, assistantMsg, mode) {
    const history = JSON.parse(localStorage.getItem('kanu_chat_history') || '[]');
    history.push({
        timestamp: new Date().toISOString(),
        user: userMsg,
        assistant: assistantMsg,
        mode: mode
    });
    
    // Keep only last 100 messages
    if (history.length > 100) {
        history.splice(0, history.length - 100);
    }
    
    localStorage.setItem('kanu_chat_history', JSON.stringify(history));
}

// Load chat history
function loadChatHistory() {
    const history = JSON.parse(localStorage.getItem('kanu_chat_history') || '[]');
    // Could display in UI if needed
}

// Training history
function saveTrainingSession(config, status) {
    const history = JSON.parse(localStorage.getItem('kanu_training_history') || '[]');
    history.push({
        timestamp: new Date().toISOString(),
        config: config,
        status: status
    });
    
    if (history.length > 50) {
        history.splice(0, history.length - 50);
    }
    
    localStorage.setItem('kanu_training_history', JSON.stringify(history));
}

function loadTrainingHistory() {
    const history = JSON.parse(localStorage.getItem('kanu_training_history') || '[]');
    // Could display in UI if needed
}

// Dark Mode
function initDarkMode() {
    const darkMode = localStorage.getItem('kanu_dark_mode') === 'true';
    if (darkMode) {
        document.body.classList.add('dark-mode');
        document.getElementById('darkModeIcon').textContent = '☀️';
    }
}

function toggleDarkMode() {
    const isDark = document.body.classList.toggle('dark-mode');
    localStorage.setItem('kanu_dark_mode', isDark);
    document.getElementById('darkModeIcon').textContent = isDark ? '☀️' : '🌙';
}

function addMessageToChat(role, content) {
    const messagesDiv = document.getElementById('chatMessages');
    
    // Remove welcome message if present
    const welcome = messagesDiv.querySelector('.welcome-message');
    if (welcome) welcome.remove();
    
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}`;
    
    const meta = document.createElement('div');
    meta.className = 'message-meta';
    meta.textContent = role === 'user' ? 'You' : (role === 'assistant' ? 'KÁNU' : 'System');
    
    const text = document.createElement('div');
    text.textContent = content;
    
    messageDiv.appendChild(meta);
    messageDiv.appendChild(text);
    messagesDiv.appendChild(messageDiv);
    
    // Scroll to bottom
    messagesDiv.scrollTop = messagesDiv.scrollHeight;
}

async function clearChat() {
    try {
        await fetch(`${API_BASE}/chat/clear`, { method: 'POST' });
        
        const messagesDiv = document.getElementById('chatMessages');
        messagesDiv.innerHTML = `
            <div class="welcome-message">
                <h2>Welcome to KÁNU</h2>
                <p>Ask me anything about physics, engineering, or request a design.</p>
            </div>
        `;
        
        document.getElementById('warningsBox').style.display = 'none';
    } catch (error) {
        console.error('Clear chat failed:', error);
    }
}

// Reasoning Functions
async function solveStepByStep() {
    const problem = document.getElementById('reasoningProblem').value.trim();
    const language = document.getElementById('reasoningLanguage').value;
    
    if (!problem) return;
    
    const stepsDiv = document.getElementById('reasoningSteps');
    const answerDiv = document.getElementById('reasoningAnswer');
    const validationDiv = document.getElementById('reasoningValidation');
    
    stepsDiv.innerHTML = '<p>Solving...</p>';
    answerDiv.innerHTML = '';
    validationDiv.innerHTML = '';
    
    try {
        const response = await fetch(`${API_BASE}/reasoning`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ problem, language })
        });
        
        const data = await response.json();
        
        if (data.success) {
            const result = data.result;
            
            // Display steps
            if (result.steps && result.steps.length > 0) {
                stepsDiv.innerHTML = result.steps.map((step, i) => 
                    `<div class="step"><strong>Step ${i+1}:</strong> ${step}</div>`
                ).join('');
            } else {
                stepsDiv.innerHTML = `<p>${result.reasoning}</p>`;
            }
            
            // Display answer
            answerDiv.innerHTML = `<p>${result.final_answer || 'See reasoning above'}</p>`;
            
            // Display validation
            if (result.physics_validated) {
                validationDiv.innerHTML = '<p class="status-ok">✓ All physics checks passed</p>';
            } else {
                validationDiv.innerHTML = `
                    <p class="status-warning">⚠️ Physics warnings detected:</p>
                    <ul>${result.warnings.map(w => `<li>${w}</li>`).join('')}</ul>
                `;
            }
        } else {
            stepsDiv.innerHTML = `<p class="error">Error: ${data.error}</p>`;
        }
    } catch (error) {
        stepsDiv.innerHTML = `<p class="error">Error: ${error.message}</p>`;
    }
}

// Training Functions
async function startTraining() {
    const duration = parseFloat(document.getElementById('trainDuration').value);
    const device = document.getElementById('trainDevice').value;
    const checkpoint_freq = document.getElementById('trainCheckpoint').value;
    const adaptive = document.getElementById('trainAdaptive').checked;
    const enrichment = document.getElementById('trainEnrichment').checked;
    
    try {
        const response = await fetch(`${API_BASE}/training/start`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                duration,
                device,
                checkpoint_freq,
                adaptive,
                enrichment
            })
        });
        
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('trainingStatusText').textContent = data.message;
            
            // Start monitoring
            if (trainingInterval) clearInterval(trainingInterval);
            trainingInterval = setInterval(updateTrainingStatus, 2000);
        } else {
            alert(`Error: ${data.error}`);
        }
    } catch (error) {
        alert(`Error: ${error.message}`);
    }
}

async function stopTraining() {
    try {
        const response = await fetch(`${API_BASE}/training/stop`, { method: 'POST' });
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('trainingStatusText').textContent = 'Training stopped';
            if (trainingInterval) {
                clearInterval(trainingInterval);
                trainingInterval = null;
            }
        }
    } catch (error) {
        console.error('Stop training failed:', error);
    }
}

async function updateTrainingStatus() {
    try {
        const response = await fetch(`${API_BASE}/training/status`);
        const data = await response.json();
        
        if (!data.active) {
            if (trainingInterval) {
                clearInterval(trainingInterval);
                trainingInterval = null;
            }
            return;
        }
        
        const status = data.status;
        
        // Update progress
        const progress = status.progress_percent || 0;
        document.getElementById('trainingProgress').style.width = `${progress}%`;
        document.getElementById('trainingProgressText').textContent = `${progress.toFixed(1)}%`;
        
        // Update status text
        const elapsed = formatTime(status.elapsed_seconds);
        const remaining = formatTime(status.remaining_seconds);
        document.getElementById('trainingStatusText').textContent = 
            `Running - Elapsed: ${elapsed} | Remaining: ${remaining}`;
        
        // Update metrics
        const latest = status.latest_metrics;
        if (latest) {
            document.getElementById('metricLoss').textContent = latest.loss.toFixed(4);
            document.getElementById('metricLR').textContent = latest.learning_rate.toExponential(2);
            document.getElementById('metricGPU').textContent = `${latest.gpu_usage_percent.toFixed(0)}%`;
            document.getElementById('metricCPU').textContent = `${latest.cpu_usage_percent.toFixed(0)}%`;
            document.getElementById('metricTokens').textContent = latest.tokens_per_second.toFixed(0);
            document.getElementById('metricStep').textContent = status.global_step;
        }
        
        // Update charts
        updateTrainingCharts();
    } catch (error) {
        console.error('Training status update failed:', error);
    }
}

async function updateTrainingCharts() {
    try {
        const response = await fetch(`${API_BASE}/training/metrics`);
        const data = await response.json();
        
        if (!data.success || !data.metrics.length) return;
        
        const metrics = data.metrics;
        
        // Update loss chart
        if (lossChart) {
            lossChart.data.labels = metrics.map(m => m.step);
            lossChart.data.datasets[0].data = metrics.map(m => m.loss);
            lossChart.update('none');
        }
        
        // Update resource chart
        if (resourceChart) {
            resourceChart.data.labels = metrics.map(m => m.step);
            resourceChart.data.datasets[0].data = metrics.map(m => m.gpu_usage);
            resourceChart.data.datasets[1].data = metrics.map(m => m.cpu_usage);
            resourceChart.update('none');
        }
    } catch (error) {
        console.error('Chart update failed:', error);
    }
}

function formatTime(seconds) {
    const h = Math.floor(seconds / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);
    return `${h}h ${m}m ${s}s`;
}

// Dataset Functions
async function loadDataset() {
    const tbody = document.getElementById('datasetTableBody');
    tbody.innerHTML = '<tr><td colspan="3" class="text-center">Loading...</td></tr>';
    
    try {
        const response = await fetch(`${API_BASE}/dataset/view`);
        const data = await response.json();
        
        if (data.success) {
            document.getElementById('datasetTotal').textContent = data.total;
            
            tbody.innerHTML = data.dataset.map(item => `
                <tr>
                    <td>${item.category}</td>
                    <td>${item.language}</td>
                    <td>${item.text.substring(0, 100)}...</td>
                </tr>
            `).join('');
        } else {
            tbody.innerHTML = `<tr><td colspan="3" class="text-center">Error: ${data.error}</td></tr>`;
        }
    } catch (error) {
        tbody.innerHTML = `<tr><td colspan="3" class="text-center">Error: ${error.message}</td></tr>`;
    }
}

// Monitor Functions
async function refreshMonitor() {
    try {
        const response = await fetch(`${API_BASE}/resources`);
        const data = await response.json();
        
        if (data.success) {
            const res = data.resources;
            
            // CPU
            const cpuUsage = res.cpu.usage_percent;
            document.getElementById('monitorCPU').textContent = `${cpuUsage.toFixed(1)}%`;
            document.getElementById('monitorCPUBar').style.width = `${cpuUsage}%`;
            
            // RAM
            const ramUsage = res.ram.usage_percent;
            document.getElementById('monitorRAM').textContent = `${ramUsage.toFixed(1)}%`;
            document.getElementById('monitorRAMBar').style.width = `${ramUsage}%`;
            
            // GPU
            if (res.gpu.available && res.gpu.devices.length > 0) {
                const gpuUsage = res.gpu.devices[0].utilization_percent;
                document.getElementById('monitorGPU').textContent = `${gpuUsage.toFixed(1)}%`;
                document.getElementById('monitorGPUBar').style.width = `${gpuUsage}%`;
            } else {
                document.getElementById('monitorGPU').textContent = 'N/A';
                document.getElementById('monitorGPUBar').style.width = '0%';
            }
            
            // System info
            const systemInfo = document.getElementById('systemInfo');
            systemInfo.textContent = JSON.stringify(res, null, 2);
        }
    } catch (error) {
        console.error('Monitor refresh failed:', error);
    }
}

// Chart Initialization
function initCharts() {
    // Loss Chart
    const lossCtx = document.getElementById('lossChart').getContext('2d');
    lossChart = new Chart(lossCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [{
                label: 'Loss',
                data: [],
                borderColor: '#2563eb',
                backgroundColor: 'rgba(37, 99, 235, 0.1)',
                tension: 0.4
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: 'Training Loss' }
            },
            scales: {
                y: { beginAtZero: false }
            }
        }
    });
    
    // Resource Chart
    const resourceCtx = document.getElementById('resourceChart').getContext('2d');
    resourceChart = new Chart(resourceCtx, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'GPU %',
                    data: [],
                    borderColor: '#10b981',
                    backgroundColor: 'rgba(16, 185, 129, 0.1)',
                    tension: 0.4
                },
                {
                    label: 'CPU %',
                    data: [],
                    borderColor: '#f59e0b',
                    backgroundColor: 'rgba(245, 158, 11, 0.1)',
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                title: { display: true, text: 'Resource Usage' }
            },
            scales: {
                y: { beginAtZero: true, max: 100 }
            }
        }
    });
}
