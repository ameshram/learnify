/* Learnify - Streaming JavaScript */

let sessionId = null;

async function initTeaching(topic, difficulty) {
    const loadingEl = document.getElementById('loading-indicator');
    const contentEl = document.getElementById('teaching-content');
    const completeEl = document.getElementById('teaching-complete');
    const statusEl = document.getElementById('status-text');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');
    const quizLink = document.getElementById('quiz-link');
    const restartBtn = document.getElementById('restart-btn');

    statusEl.textContent = 'Generating...';
    progressText.textContent = 'AI is thinking...';

    try {
        const response = await fetch('/api/teach', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ topic, difficulty })
        });

        if (!response.ok) {
            throw new Error('Failed to start teaching session');
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let content = '';
        let charCount = 0;
        const estimatedChars = 4000;

        loadingEl.style.display = 'none';
        contentEl.style.display = 'block';

        while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            const chunk = decoder.decode(value, { stream: true });
            const lines = chunk.split('\n');

            for (const line of lines) {
                if (line.startsWith('data: ')) {
                    try {
                        const data = JSON.parse(line.slice(6));

                        if (data.content) {
                            content += data.content;
                            charCount += data.content.length;
                            contentEl.innerHTML = marked.parse(content);

                            const progress = Math.min((charCount / estimatedChars) * 100, 95);
                            progressFill.style.width = progress + '%';
                            progressText.textContent = 'Generating content...';
                        }

                        if (data.done) {
                            sessionId = data.session_id;
                            progressFill.style.width = '100%';
                            progressText.textContent = 'Complete!';
                            statusEl.textContent = 'Complete';

                            quizLink.href = `/quiz/${sessionId}`;
                            completeEl.style.display = 'block';
                            restartBtn.style.display = 'inline-flex';

                            contentEl.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }

                        if (data.error) {
                            throw new Error(data.error);
                        }
                    } catch (e) {
                        if (e.message !== 'Unexpected end of JSON input') {
                            console.error('Parse error:', e);
                        }
                    }
                }
            }
        }
    } catch (error) {
        console.error('Teaching error:', error);
        loadingEl.innerHTML = `
            <div class="error-message">
                <h3>Error</h3>
                <p>${error.message}</p>
                <a href="/" class="btn btn-primary">Try Again</a>
            </div>
        `;
    }
}

// Restart button handler
document.addEventListener('DOMContentLoaded', () => {
    const restartBtn = document.getElementById('restart-btn');
    if (restartBtn) {
        restartBtn.addEventListener('click', () => {
            window.location.reload();
        });
    }
});
