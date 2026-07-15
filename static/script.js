// Global state
let currentJobId = null;
const STEMS = ['vocals', 'drums', 'bass', 'other'];

// DOM Elements
const urlInput = document.getElementById('youtube-url');
const downloadBtn = document.getElementById('download-btn');
const statusSection = document.getElementById('status-section');
const playbackSection = document.getElementById('playback-section');
const errorSection = document.getElementById('error-section');
const progressFill = document.getElementById('progress-fill');
const statusMessage = document.getElementById('status-message');
const errorMessage = document.getElementById('error-message');

// Event Listeners
downloadBtn.addEventListener('click', handleDownload);
urlInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') handleDownload();
});

// Handle Download
async function handleDownload() {
    const url = urlInput.value.trim();

    if (!url) {
        showError('Please enter a YouTube URL');
        return;
    }

    if (!url.includes('youtube.com') && !url.includes('youtu.be')) {
        showError('Please enter a valid YouTube URL');
        return;
    }

    downloadBtn.disabled = true;
    urlInput.disabled = true;

    showStatus();
    hideError();
    hidePlayback();

    try {
        // Start download and separation
        const response = await fetch('/api/download', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ url })
        });

        if (!response.ok) {
            throw new Error('Failed to start processing');
        }

        const data = await response.json();
        currentJobId = data.job_id;

        // Poll for status
        await pollStatus();

    } catch (error) {
        console.error('Error:', error);
        showError(error.message || 'An error occurred. Please try again.');
    } finally {
        downloadBtn.disabled = false;
        urlInput.disabled = false;
    }
}

// Poll Status
async function pollStatus() {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/api/status/${currentJobId}`);
        
        if (!response.ok) {
            throw new Error('Failed to get status');
        }

        const data = await response.json();

        updateStatus(data);

        if (data.status === 'completed') {
            onProcessingComplete(data);
        } else if (data.status === 'error') {
            showError(data.message || 'An error occurred');
        } else {
            // Continue polling
            setTimeout(pollStatus, 1000);
        }

    } catch (error) {
        console.error('Error polling status:', error);
        showError('Connection error. Please try again.');
    }
}

// Update Status Display
function updateStatus(data) {
    const progress = data.progress || 0;
    progressFill.style.width = progress + '%';

    let message = data.message || 'Processing...';
    if (data.status === 'downloading') {
        message = `📥 ${message}`;
    } else if (data.status === 'separating') {
        message = `⚙️ ${message}`;
    }

    statusMessage.textContent = message;
}

// Handle Processing Complete
async function onProcessingComplete(data) {
    hideStatus();
    showPlayback();

    // Load audio files
    if (data.stems) {
        for (const stem of STEMS) {
            if (data.stems[stem]) {
                loadStemAudio(stem, data.stems[stem]);
            }
        }
    }
}

// Load Stem Audio
function loadStemAudio(stemName, filePath) {
    const playerId = `${stemName}-player`;
    const player = document.getElementById(playerId);
    
    if (player) {
        const source = player.querySelector('source');
        source.src = `/api/stream-stem/${currentJobId}/${stemName}`;
        player.load();
    }
}

// Download Stem
async function downloadStem(stemName) {
    if (!currentJobId) return;

    try {
        const response = await fetch(`/api/download-stem/${currentJobId}/${stemName}`);
        
        if (!response.ok) {
            throw new Error('Download failed');
        }

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${stemName}.wav`;
        document.body.appendChild(a);
        a.click();
        a.remove();
        window.URL.revokeObjectURL(url);

    } catch (error) {
        console.error('Download error:', error);
        showError('Failed to download file');
    }
}

// Reset App
function resetApp() {
    currentJobId = null;
    urlInput.value = '';
    urlInput.disabled = false;
    downloadBtn.disabled = false;
    progressFill.style.width = '0%';

    hideStatus();
    hidePlayback();
    hideError();

    // Clear audio sources
    for (const stem of STEMS) {
        const playerId = `${stem}-player`;
        const player = document.getElementById(playerId);
        if (player) {
            const source = player.querySelector('source');
            source.src = '';
            player.load();
        }
    }

    urlInput.focus();
}

// UI Helpers
function showStatus() {
    statusSection.classList.remove('hidden');
    hidePlayback();
    hideError();
}

function hideStatus() {
    statusSection.classList.add('hidden');
}

function showPlayback() {
    playbackSection.classList.remove('hidden');
    hideStatus();
    hideError();
}

function hidePlayback() {
    playbackSection.classList.add('hidden');
}

function showError(message) {
    errorMessage.textContent = message;
    errorSection.classList.remove('hidden');
    hideStatus();
    hidePlayback();
}

function hideError() {
    errorSection.classList.add('hidden');
}

// Initialize
urlInput.focus();
