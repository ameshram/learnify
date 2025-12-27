/**
 * Learnify - Streaming JavaScript
 *
 * Handles real-time streaming of teaching content using Server-Sent Events (SSE)
 */

let sessionId = null;

async function initTeaching(topic, difficulty) {
    const loadingState = document.getElementById('loading-state');
    const contentArea = document.getElementById('content-area');
    const teachingContent = document.getElementById('teaching-content');
    const quizCta = document.getElementById('quiz-cta');
    const quizLink = document.getElementById('quiz-link');
    const statusText = document.getElementById('status-text');
    const progressFill = document.getElementById('progress-fill');
    const progressText = document.getElementById('progress-text');

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

        // Show content area, hide loading
        loadingState.classList.add('hidden');
        contentArea.classList.remove('hidden');
        progressText.textContent = 'Generating content...';

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

                            // Render markdown
                            teachingContent.innerHTML = marked.parse(content);

                            // Update progress
                            const progress = Math.min((charCount / estimatedChars) * 100, 95);
                            progressFill.style.width = progress + '%';

                            // Scroll to keep new content visible
                            teachingContent.scrollTop = teachingContent.scrollHeight;
                        }

                        if (data.done) {
                            sessionId = data.session_id;

                            // Update UI
                            progressFill.style.width = '100%';
                            progressText.textContent = 'Complete!';
                            statusText.textContent = 'Complete';
                            statusText.style.color = 'var(--color-success)';

                            // Show quiz CTA
                            quizLink.href = `/quiz/${sessionId}`;
                            quizCta.classList.remove('hidden');

                            // Re-init icons
                            if (window.lucide) {
                                lucide.createIcons();
                            }

                            // Smooth scroll to quiz CTA
                            setTimeout(() => {
                                quizCta.scrollIntoView({ behavior: 'smooth', block: 'center' });
                            }, 500);
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

        loadingState.innerHTML = `
            <div style="text-align: center; padding: var(--space-8);">
                <div style="font-size: 3rem; margin-bottom: var(--space-4);">😕</div>
                <h3 style="margin-bottom: var(--space-2);">Something went wrong</h3>
                <p style="color: var(--color-text-secondary); margin-bottom: var(--space-6);">${error.message}</p>
                <a href="/" class="btn btn-primary">Try Again</a>
            </div>
        `;

        statusText.textContent = 'Error';
        statusText.style.color = 'var(--color-error)';
    }
}
