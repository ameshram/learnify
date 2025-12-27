/**
 * Learnify - Quiz JavaScript
 *
 * Handles quiz functionality:
 * - Loading and displaying questions
 * - Option selection
 * - Answer submission
 * - Progress tracking
 * - Feedback display
 */

let questions = [];
let currentIndex = 0;
let score = 0;
let selectedOption = null;
let answered = false;
let progressDots = [];

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

        // Generate progress dots
        const dotsContainer = document.getElementById('progress-dots');
        dotsContainer.innerHTML = '';
        questions.forEach((_, i) => {
            const dot = document.createElement('div');
            dot.className = 'progress-dot' + (i === 0 ? ' active' : '');
            dotsContainer.appendChild(dot);
            progressDots.push(dot);
        });

        // Update total
        document.getElementById('total-questions').textContent = questions.length;

        // Hide loading, show quiz
        loadingEl.classList.add('hidden');
        containerEl.classList.remove('hidden');

        // Render first question
        renderQuestion();
        setupEventListeners(sessionId);

        // Init icons
        if (window.lucide) {
            lucide.createIcons();
        }
    } catch (error) {
        console.error('Quiz init error:', error);
        loadingEl.classList.add('hidden');
        errorEl.classList.remove('hidden');
        document.getElementById('error-message').textContent = error.message;
    }
}

function renderQuestion() {
    const question = questions[currentIndex];

    // Update question number
    document.getElementById('question-number').textContent =
        `Question ${currentIndex + 1} of ${questions.length}`;

    // Update question text
    document.getElementById('question-text').textContent = question.question;

    // Render options
    const optionsList = document.getElementById('options-list');
    optionsList.innerHTML = '';

    question.options.forEach(option => {
        const optionCard = document.createElement('div');
        optionCard.className = 'option-card';
        optionCard.dataset.optionId = option.id;
        optionCard.innerHTML = `
            <span class="option-letter">${option.id}</span>
            <span class="option-text">${option.text}</span>
        `;
        optionCard.addEventListener('click', () => selectOption(option.id, optionCard));
        optionsList.appendChild(optionCard);
    });

    // Reset state
    selectedOption = null;
    answered = false;

    // Reset buttons
    document.getElementById('submit-btn').disabled = true;
    document.getElementById('submit-btn').classList.remove('hidden');
    document.getElementById('next-btn').classList.add('hidden');
    document.getElementById('finish-btn').classList.add('hidden');

    // Hide feedback
    document.getElementById('feedback-card').classList.add('hidden');
}

function selectOption(optionId, optionCard) {
    if (answered) return;

    selectedOption = optionId;

    // Update visual selection
    document.querySelectorAll('.option-card').forEach(card => {
        card.classList.remove('selected');
    });
    optionCard.classList.add('selected');

    // Enable submit button
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

    // Disable all options
    document.querySelectorAll('.option-card').forEach(card => {
        card.classList.add('disabled');
    });

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
            progressDots[currentIndex].classList.add('completed');
        } else {
            progressDots[currentIndex].classList.add('wrong');
        }
        document.getElementById('current-score').textContent = score;

        // Show correct/incorrect on options
        document.querySelectorAll('.option-card').forEach(card => {
            const optionId = card.dataset.optionId;
            if (optionId === selectedOption) {
                card.classList.add(result.is_correct ? 'correct' : 'incorrect');
            }
        });

        // Show feedback
        const feedbackCard = document.getElementById('feedback-card');
        const feedbackStatus = document.getElementById('feedback-status');
        const feedbackText = document.getElementById('feedback-text');
        const feedbackIcon = document.getElementById('feedback-icon');

        feedbackCard.classList.remove('hidden', 'correct', 'incorrect');
        feedbackCard.classList.add(result.is_correct ? 'correct' : 'incorrect');

        feedbackStatus.textContent = result.is_correct ? 'Correct!' : 'Incorrect';
        feedbackText.textContent = result.feedback;

        // Update icon
        feedbackIcon.setAttribute('data-lucide', result.is_correct ? 'check-circle' : 'x-circle');
        if (window.lucide) {
            lucide.createIcons();
        }

        // Show appropriate next button
        document.getElementById('submit-btn').classList.add('hidden');
        if (currentIndex < questions.length - 1) {
            document.getElementById('next-btn').classList.remove('hidden');
        } else {
            document.getElementById('finish-btn').classList.remove('hidden');
        }

        // Re-init icons for buttons
        if (window.lucide) {
            lucide.createIcons();
        }
    } catch (error) {
        console.error('Submit error:', error);
        if (window.Toast) {
            Toast.error('Error submitting answer. Please try again.');
        }
        answered = false;

        // Re-enable options
        document.querySelectorAll('.option-card').forEach(card => {
            card.classList.remove('disabled');
        });
    }
}

function nextQuestion() {
    currentIndex++;

    // Update progress dots
    progressDots.forEach((dot, i) => {
        dot.classList.remove('active');
        if (i === currentIndex) {
            dot.classList.add('active');
        }
    });

    renderQuestion();
}
