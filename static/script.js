function toggleTheme() {
    const body = document.body;
    const btn = document.getElementById('themeBtn');
    if (body.classList.contains('dark-mode')) {
        body.classList.remove('dark-mode');
        body.classList.add('light-mode');
        btn.innerHTML = '🌙 Dark Mode';
        localStorage.setItem('theme', 'light');
    } else {
        body.classList.remove('light-mode');
        body.classList.add('dark-mode');
        btn.innerHTML = '☀️ Light Mode';
        localStorage.setItem('theme', 'dark');
    }
}

// Initialize theme
document.addEventListener('DOMContentLoaded', () => {
    const savedTheme = localStorage.getItem('theme');
    if (savedTheme === 'light') {
        document.body.classList.remove('dark-mode');
        document.body.classList.add('light-mode');
        document.getElementById('themeBtn').innerHTML = '🌙 Dark Mode';
    }
});

document.getElementById('generateBtn').addEventListener('click', generateSubtopics);

async function generateSubtopics() {
    const chapterInput = document.getElementById('chapterInput');
    if (!chapterInput) return;
    const chapter = chapterInput.value;
    if (!chapter) return alert('Please enter a chapter name');

    showLoading(true);
    try {
        const response = await fetch('/generate_subtopics', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ chapter })
        });
        const data = await response.json();
        
        if (data.error) throw new Error(data.error);
        
        displaySubtopics(data.content);
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        showLoading(false);
    }
}

function displaySubtopics(content) {
    const container = document.getElementById('subtopicsContainer');
    const list = document.getElementById('subtopicsList');
    list.innerHTML = '';
    
    // Simple parsing of bullet points
    const lines = content.split('\n').filter(line => line.trim().length > 0);
    
    lines.forEach(line => {
        const topic = line.replace(/^[•\-\d.]+\s*/, '').trim();
        if (topic) {
            const div = document.createElement('div');
            div.className = 'topic-item';
            div.innerHTML = `
                <h4>${topic}</h4>
                <p>Deep dive into ${topic.toLowerCase()} with AI notes</p>
            `;
            div.onclick = () => getDetail(topic);
            list.appendChild(div);
        }
    });
    
    container.classList.remove('hidden');
    document.getElementById('detailContainer').classList.add('hidden');
}

async function getDetail(topic) {
    const chapterInput = document.getElementById('chapterInput');
    if (!chapterInput) return;
    const chapter = chapterInput.value;
    showLoading(true);
    try {
        const response = await fetch('/get_detail', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, chapter })
        });
        const data = await response.json();
        
        if (data.error) throw new Error(data.error);
        
        const detailContent = document.getElementById('detailContent');
        // Use marked to parse markdown
        detailContent.innerHTML = `<h3>${topic}</h3>` + 
                                 marked.parse(data.content);
        
        document.getElementById('subtopicsContainer').classList.add('hidden');
        document.getElementById('detailContainer').classList.remove('hidden');
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        showLoading(false);
    }
}

function backToTopics() {
    document.getElementById('detailContainer').classList.add('hidden');
    document.getElementById('subtopicsContainer').classList.remove('hidden');
}

function showLoading(show) {
    const loader = document.getElementById('loading');
    if (loader) loader.classList.toggle('hidden', !show);
}

document.addEventListener('DOMContentLoaded', () => {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.addEventListener('change', () => {
            const label = document.getElementById('fileLabelText');
            if (fileInput.files && fileInput.files[0]) {
                label.textContent = '📄 ' + fileInput.files[0].name;
            } else {
                label.textContent = '📎 Choose a file (TXT, PDF, DOCX)';
            }
        });
    }
});

async function uploadFile() {
    const fileInput = document.getElementById('fileInput');
    if (!fileInput || !fileInput.files || !fileInput.files[0]) {
        return alert('Please choose a file first.');
    }
    const file = fileInput.files[0];
    if (file.size > 10 * 1024 * 1024) {
        return alert('File too large. Please upload a file under 10 MB.');
    }

    const formData = new FormData();
    formData.append('file', file);

    showLoading(true);
    try {
        const response = await fetch('/upload_file', {
            method: 'POST',
            body: formData
        });
        const data = await response.json();
        if (data.error) throw new Error(data.error);

        const detailContent = document.getElementById('detailContent');
        detailContent.innerHTML = `<h3>Notes from: ${data.filename}</h3>` + marked.parse(data.content);

        document.getElementById('subtopicsContainer').classList.add('hidden');
        document.getElementById('detailContainer').classList.remove('hidden');
    } catch (err) {
        alert('Error: ' + err.message);
    } finally {
        showLoading(false);
    }
}
