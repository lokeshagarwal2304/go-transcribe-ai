// Professional Transcriber Controller with Word (.docx) & Zero Stray Colons

let selectedFile = null;
let currentTranscriptionData = null;

// DOM Elements
const dropzone = document.getElementById('dropzone');
const dropzoneContent = document.getElementById('dropzoneContent');
const fileInfoPreview = document.getElementById('fileInfoPreview');
const audioFileInput = document.getElementById('audioFileInput');
const fileNameDisplay = document.getElementById('fileNameDisplay');
const fileSizeDisplay = document.getElementById('fileSizeDisplay');
const clearFileBtn = document.getElementById('clearFileBtn');
const audioPlayerSection = document.getElementById('audioPlayerSection');
const audioPreview = document.getElementById('audioPreview');

const timestampRuleSelect = document.getElementById('timestampRule');
const speakerModeSelect = document.getElementById('speakerMode');
const speaker1NameInput = document.getElementById('speaker1Name');
const speaker2NameInput = document.getElementById('speaker2Name');
const languageModeSelect = document.getElementById('languageMode');
const modelSizeSelect = document.getElementById('modelSize');
const transcribeBtn = document.getElementById('transcribeBtn');

const emptyState = document.getElementById('emptyState');
const loadingState = document.getElementById('loadingState');
const transcriptDisplayArea = document.getElementById('transcriptDisplayArea');
const exportActions = document.getElementById('exportActions');
const metricsBar = document.getElementById('metricsBar');

const metricTime = document.getElementById('metricTime');
const metricLang = document.getElementById('metricLang');
const metricTurns = document.getElementById('metricTurns');

const formattedTranscriptBox = document.getElementById('formattedTranscriptBox');
const cleanTranscriptText = document.getElementById('cleanTranscriptText');
const timelineList = document.getElementById('timelineList');

// Modal Elements
const slangModal = document.getElementById('slangModal');
const viewSlangsBtn = document.getElementById('viewSlangsBtn');
const closeSlangModal = document.getElementById('closeSlangModal');
const slangGlossaryGrid = document.getElementById('slangGlossaryGrid');

// Export & Copy Buttons
const copyFinalBtn = document.getElementById('copyFinalBtn');
const exportDocxBtn = document.getElementById('exportDocxBtn');
const exportTxtBtn = document.getElementById('exportTxtBtn');
const exportSrtBtn = document.getElementById('exportSrtBtn');
const exportJsonBtn = document.getElementById('exportJsonBtn');

document.addEventListener('DOMContentLoaded', () => {
    setupDropzone();
    setupTabs();
    setupExports();
    setupSlangModal();
});

function setupDropzone() {
    dropzone.addEventListener('click', (e) => {
        if (e.target !== clearFileBtn) {
            audioFileInput.click();
        }
    });

    audioFileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
            handleFileSelect(e.target.files[0]);
        }
    });

    dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
        dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropzone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileSelect(e.dataTransfer.files[0]);
        }
    });

    clearFileBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        resetFileInput();
    });

    transcribeBtn.addEventListener('click', startTranscription);
}

function handleFileSelect(file) {
    selectedFile = file;
    fileNameDisplay.textContent = file.name;
    fileSizeDisplay.textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';

    dropzoneContent.style.display = 'none';
    fileInfoPreview.style.display = 'flex';

    const audioUrl = URL.createObjectURL(file);
    audioPreview.src = audioUrl;
    audioPlayerSection.style.display = 'block';

    transcribeBtn.disabled = false;
}

function resetFileInput() {
    selectedFile = null;
    audioFileInput.value = '';
    dropzoneContent.style.display = 'block';
    fileInfoPreview.style.display = 'none';
    audioPlayerSection.style.display = 'none';
    audioPreview.src = '';
    transcribeBtn.disabled = true;
}

async function startTranscription() {
    if (!selectedFile) return;

    transcribeBtn.disabled = true;
    transcribeBtn.querySelector('.btn-text').textContent = 'Transcribing & Formatting...';
    transcribeBtn.querySelector('.spinner').style.display = 'inline-block';

    emptyState.style.display = 'none';
    transcriptDisplayArea.style.display = 'none';
    metricsBar.style.display = 'none';
    exportActions.style.display = 'none';
    loadingState.style.display = 'block';

    let secondsElapsed = 0;
    const loadingSubtext = loadingState.querySelector('p');
    const loadingTimer = setInterval(() => {
        secondsElapsed += 1;
        if (loadingSubtext) {
            loadingSubtext.textContent = `Analyzing audio & generating 100% clean transcript... (${secondsElapsed}s elapsed)`;
        }
    }, 1000);

    const formData = new FormData();
    formData.append('audio', selectedFile);
    formData.append('language_mode', languageModeSelect.value);
    formData.append('model_size', modelSizeSelect.value);
    formData.append('timestamp_rule', timestampRuleSelect.value);
    formData.append('speaker_mode', speakerModeSelect ? speakerModeSelect.value : 'auto');
    formData.append('speaker1_name', speaker1NameInput.value);
    formData.append('speaker2_name', speaker2NameInput.value);
    formData.append('gotranscript_mode', 'true');

    try {
        const response = await fetch('/api/transcribe', {
            method: 'POST',
            body: formData
        });

        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || 'Transcription request failed');
        }

        const data = await response.json();
        currentTranscriptionData = data;
        renderResults(data);

    } catch (err) {
        alert('Error: ' + err.message);
        emptyState.style.display = 'block';
    } finally {
        clearInterval(loadingTimer);
        loadingState.style.display = 'none';
        transcribeBtn.disabled = false;
        transcribeBtn.querySelector('.btn-text').textContent = '🚀 Generate Formatted Transcript';
        transcribeBtn.querySelector('.spinner').style.display = 'none';
    }
}

function renderResults(data) {
    metricTime.textContent = data.processing_time_seconds + 's';
    metricLang.textContent = (data.detected_language || 'Auto').toUpperCase();
    
    const formatted = data.formatted || {};
    const dialogues = formatted.dialogues || [];
    metricTurns.textContent = dialogues.length;

    metricsBar.style.display = 'grid';
    exportActions.style.display = 'flex';
    transcriptDisplayArea.style.display = 'block';

    // 1. Render Formatted Document View WITHOUT leading colons
    formattedTranscriptBox.innerHTML = '';
    if (dialogues.length > 0) {
        dialogues.forEach(item => {
            const p = document.createElement('div');
            p.className = 'dialogue-paragraph';

            let bodyHtml = escapeHtml(item.content);
            bodyHtml = bodyHtml.replace(/(\[inaudible\s+\d{2}:\d{2}:\d{2}\])/g, '<span class="tag-inaudible">$1</span>');
            bodyHtml = bodyHtml.replace(/(\[unintelligible\s+\d{2}:\d{2}:\d{2}\])/g, '<span class="tag-unintelligible">$1</span>');

            // Only add speaker label if speaker name is NOT empty
            let speakerHtml = '';
            if (item.speaker && item.speaker.trim()) {
                speakerHtml = `<span class="speaker-label">${escapeHtml(item.speaker)}: </span>`;
            }

            const tsHtml = item.timestamp_tag ? `<span class="timestamp-marker">${item.timestamp_tag} </span>` : '';
            
            p.innerHTML = `${speakerHtml}${tsHtml}${bodyHtml}`;
            formattedTranscriptBox.appendChild(p);
        });
    } else {
        formattedTranscriptBox.innerHTML = '<em>No speech segments detected.</em>';
    }

    cleanTranscriptText.textContent = formatted.formatted_text || data.normalized_transcript || '';

    // 3. Render Segments Timeline
    timelineList.innerHTML = '';
    if (data.segments && data.segments.length > 0) {
        data.segments.forEach(seg => {
            const item = document.createElement('div');
            item.className = 'timeline-item';
            item.innerHTML = `
                <span class="timeline-timestamp">${seg.start_formatted || formatSeconds(seg.start)} - ${seg.end_formatted || formatSeconds(seg.end)}</span>
                <span class="timeline-text">${escapeHtml(seg.normalized_text)}</span>
            `;
            timelineList.appendChild(item);
        });
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function formatSeconds(sec) {
    const mins = Math.floor(sec / 60);
    const secs = Math.floor(sec % 60);
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
}

function setupTabs() {
    const tabBtns = document.querySelectorAll('.tab-btn');
    tabBtns.forEach(btn => {
        btn.addEventListener('click', () => {
            tabBtns.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

            btn.classList.add('active');
            const target = btn.getAttribute('data-tab');
            if (target === 'formatted-view') {
                document.getElementById('tabFormattedView').classList.add('active');
            } else if (target === 'clean-text') {
                document.getElementById('tabCleanText').classList.add('active');
            } else {
                document.getElementById('tabTimeline').classList.add('active');
            }
        });
    });
}

function setupExports() {
    // 1-Click Clean Copy Button
    copyFinalBtn.addEventListener('click', () => {
        if (!currentTranscriptionData) return;
        const textToCopy = currentTranscriptionData.formatted?.formatted_text || currentTranscriptionData.normalized_transcript;
        navigator.clipboard.writeText(textToCopy);
        const originalText = copyFinalBtn.innerHTML;
        copyFinalBtn.innerHTML = '✅ Copied Clean Text!';
        copyFinalBtn.style.background = '#10b981';
        setTimeout(() => { 
            copyFinalBtn.innerHTML = originalText;
            copyFinalBtn.style.background = '';
        }, 2500);
    });

    exportDocxBtn.addEventListener('click', () => downloadExport('docx'));
    exportTxtBtn.addEventListener('click', () => downloadExport('txt'));
    exportSrtBtn.addEventListener('click', () => downloadExport('srt'));
    exportJsonBtn.addEventListener('click', () => downloadExport('json'));
}

async function downloadExport(format) {
    if (!currentTranscriptionData) return;
    try {
        const response = await fetch(`/api/export/${format}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(currentTranscriptionData)
        });
        if (!response.ok) throw new Error('Export download failed');

        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        
        const base = (currentTranscriptionData.original_filename || 'transcript').replace(/\.[^/.]+$/, "");
        a.download = `${base}.${format}`;
        document.body.appendChild(a);
        a.click();
        a.remove();
    } catch (err) {
        alert('Export error: ' + err.message);
    }
}

function setupSlangModal() {
    viewSlangsBtn.addEventListener('click', async () => {
        slangModal.style.display = 'flex';
        if (slangGlossaryGrid.children.length === 0) {
            try {
                const res = await fetch('/api/slangs');
                const data = await res.json();
                slangGlossaryGrid.innerHTML = '';
                for (const [roman, norm] of Object.entries(data.roman_slangs)) {
                    const dev = data.devanagari_slangs[roman] || '';
                    const item = document.createElement('div');
                    item.className = 'slang-grid-item';
                    item.innerHTML = `
                        <div class="slang-word">${roman}</div>
                        <div class="slang-dev">${dev ? dev : 'Normalized: ' + norm}</div>
                    `;
                    slangGlossaryGrid.appendChild(item);
                }
            } catch (e) {
                slangGlossaryGrid.innerHTML = '<p>Could not load dictionary.</p>';
            }
        }
    });

    closeSlangModal.addEventListener('click', () => {
        slangModal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === slangModal) {
            slangModal.style.display = 'none';
        }
    });
}
