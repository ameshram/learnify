/* Learnify - Quiz JavaScript */

let questions = [];
let currentIndex = 0;
let score = 0;
let selectedOption = null;
let answered = false;

async function initQuiz(sessionId) {
    const loadingEl = document.getElementById('quiz-loading');
    const containerEl = document.getElementById('quiz-container');
    const errorEl = document.getElementById('quiz-error');

    try {
        const response = await fetch(`/api/quiz/generate/${sessionId}`, {
            method: 'POST'
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        questions = data.questions;
        loadingEl.style.display = 'none';
        containerEl.style.display = 'block';

        document.getElementById('total-questions').textContent = questions.length;
        renderQuestion();
        setupEventListeners(sessionId);
    } catch (error) {
        console.error('Quiz init error:', error);
        loadingEl.style.display = 'none';
        errorEl.style.display = 'block';
        document.getElementById('error-message').textContent = error.message;
    }
}

function renderQuestion() {
    const question = questions[currentIndex];

    document.getElementById('question-counter').textContent =
        `Question ${currentIndex + 1} of ${questions.length}`;

    const progressPercent = ((currentIndex + 1) / questions.length) * 100;
    document.getElementById('quiz-progress-fill').style.width = progressPercent + '%';

    document.getElementById('concept-badge').textContent = question.concept_tested;
    document.getElementById('question-text').textContent = question.question;

    const optionsContainer = document.getElementById('options-container');
    optionsContainer.innerHTML = '';

    question.options.forEach(option => {
        const btn = document.createElement('button');
        btn.className = 'option-btn';
        btn.dataset.optionId = option.id;
        btn.innerHTML = `
            <span class="option-id">${option.id}</span>
            <span class="option-text">${option.text}</span>
        `;
        btn.addEventListener('click', () => selectOption(option.id));
        optionsContainer.appendChild(btn);
    });

    // Reset state
    selectedOption = null;
    answered = false;
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('submit-btn').style.display = 'inline-flex';
    document.getElementById('next-btn').style.display = 'none';
    document.getElementById('finish-btn').style.display = 'none';
    document.getElementById('feedback-container').style.display = 'none';
}

function selectOption(optionId) {
    if (answered) return;

    selectedOption = optionId;

    document.querySelectorAll('.option-btn').forEach(btn => {
        btn.classList.remove('selected');
        if (btn.dataset.optionId === optionId) {
            btn.classList.add('selected');
        }
    });

    document.getElementById('submit-btn').disabled = false;
}

function setupEventListeners(sessionId) {
    document.getElementById('submit-btn').addEventListener('click', () => submitAnswer(sessionId));
    document.getElementById('next-btn').addEventListener('click', nextQuestion);
    document.getElementById('finish-btn').addEventListener('click', () => {
        window.location.href = `/results/${sessionId}`;
    });
}

async function submitAnswer(sessionId) {
    if (!selectedOption || answered) return;

    answered = true;
    const question = questions[currentIndex];

    try {
        const response = await fetch(`/api/quiz/submit/${sessionId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                question_id: question.id,
                selected_option: selectedOption
            })
        });

        const result = await response.json();

        if (result.error) {
            throw new Error(result.error);
        }

        // Update score
        if (result.is_correct) {
            score++;
        }
        document.getElementById('current-score').textContent = score;

        // Show feedback
        const feedbackContainer = document.getElementById('feedback-container');
        const feedbackStatus = document.getElementById('feedback-status');
        const feedbackText = document.getElementById('feedback-text');
        const understandingText = document.getElementById('understanding-text');

        feedbackStatus.textContent = result.is_correct ? 'Correct!' : 'Incorrect';
        feedbackStatus.className = 'feedback-status ' + (result.is_correct ? 'correct' : 'incorrect');
        feedbackText.textContent = result.feedback;
        understandingText.textContent = result.understanding;
        feedbackContainer.style.display = 'block';

        // Update option styles
        document.querySelectorAll('.option-btn').forEach(btn => {
            btn.classList.remove('selected');
            const optionId = btn.dataset.optionId;

            // Find correct answer
            const correctOption = question.options.find(o => {
                // We don't have is_correct in the frontend data, use API response
                return optionId === selectedOption;
            });

            if (optionId === selectedOption) {
                btn.classList.add(result.is_correct ? 'correct' : 'incorrect');
            }
        });

        // Show next/finish button
        document.getElementById('submit-btn').style.display = 'none';
        if (currentIndex < questions.length - 1) {
            document.getElementById('next-btn').style.display = 'inline-flex';
        } else {
            document.getElementById('finish-btn').style.display = 'inline-flex';
        }
    } catch (error) {
        console.error('Submit error:', error);
        alert('Error submitting answer. Please try again.');
        answered = false;
    }
}

function nextQuestion() {
    currentIndex++;
    renderQuestion();
}
