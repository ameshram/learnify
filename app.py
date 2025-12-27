"""Learnify - AI-Powered Teaching Assistant"""
import os
import uuid
import json
import logging
from flask import Flask, render_template, request, jsonify, Response, session
from flask_cors import CORS
from config import get_config
from claude_client import ClaudeClient
from teaching_agent import TeachingAgent
from quiz_manager import QuizManager
from session_manager import SessionManager
from prompt_templates import InsightsPrompts
from security import rate_limit, sanitize_input, validate_topic, validate_difficulty, add_security_headers

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
config = get_config()
app.secret_key = config.SECRET_KEY
CORS(app)

claude_client = ClaudeClient()
teaching_agent = TeachingAgent(claude_client)
quiz_manager = QuizManager(claude_client)
session_manager = SessionManager()

teaching_content_store = {}
quiz_store = {}


@app.after_request
def after_request(response):
    return add_security_headers(response)


@app.route('/')
def index():
    stats = session_manager.get_stats()
    return render_template('index.html', stats=stats)


@app.route('/teach')
def teach_page():
    topic = request.args.get('topic', '')
    difficulty = request.args.get('difficulty', 'intermediate')
    return render_template('teaching.html', topic=topic, difficulty=difficulty)


@app.route('/api/teach', methods=['POST'])
@rate_limit
def api_teach():
    data = request.get_json()
    topic = sanitize_input(data.get('topic', ''))
    difficulty = data.get('difficulty', 'intermediate')

    valid, error = validate_topic(topic)
    if not valid:
        return jsonify({'error': error}), 400

    valid, error = validate_difficulty(difficulty)
    if not valid:
        return jsonify({'error': error}), 400

    session_id = str(uuid.uuid4())
    session_manager.create_session(session_id, topic, difficulty)

    def generate():
        content_parts = []
        try:
            for chunk in teaching_agent.teach(topic, difficulty):
                content_parts.append(chunk)
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            full_content = ''.join(content_parts)
            teaching_content_store[session_id] = full_content
            session_manager.update_teaching_content(session_id, full_content)
            yield f"data: {json.dumps({'done': True, 'session_id': session_id})}\n\n"
        except Exception as e:
            logger.error(f"Teaching error: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream',
                   headers={'Cache-Control': 'no-cache', 'X-Accel-Buffering': 'no'})


@app.route('/quiz/<session_id>')
def quiz_page(session_id):
    return render_template('quiz.html', session_id=session_id)


@app.route('/api/quiz/generate/<session_id>', methods=['POST'])
@rate_limit
def api_generate_quiz(session_id):
    try:
        content = teaching_content_store.get(session_id)
        if not content:
            db_session = session_manager.get_session(session_id)
            if db_session and db_session.teaching_content:
                content = db_session.teaching_content
            else:
                return jsonify({'error': 'Session not found'}), 404

        db_session = session_manager.get_session(session_id)
        topic = db_session.topic if db_session else "General Topic"
        difficulty = db_session.difficulty if db_session else "intermediate"

        quiz = quiz_manager.generate_quiz(topic, content, num_questions=4, difficulty=difficulty)
        quiz_store[session_id] = quiz

        questions_data = [
            {
                'id': q.id,
                'question': q.question,
                'concept_tested': q.concept_tested,
                'options': [{'id': o.id, 'text': o.text} for o in q.options]
            }
            for q in quiz.questions
        ]

        return jsonify({'questions': questions_data, 'total': len(questions_data)})
    except Exception as e:
        logger.error(f"Quiz generation error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/quiz/submit/<session_id>', methods=['POST'])
@rate_limit
def api_submit_answer(session_id):
    try:
        quiz = quiz_store.get(session_id)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404

        data = request.get_json()
        question_id = data.get('question_id')
        selected_option = data.get('selected_option')

        result = quiz_manager.submit_answer(quiz, question_id, selected_option)

        return jsonify({
            'is_correct': result.is_correct,
            'feedback': result.feedback,
            'understanding': result.understanding,
            'concept_tested': result.concept_tested
        })
    except ValueError as e:
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Submit error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/quiz/complete/<session_id>', methods=['POST'])
@rate_limit
def api_complete_quiz(session_id):
    try:
        quiz = quiz_store.get(session_id)
        if not quiz:
            return jsonify({'error': 'Quiz not found'}), 404

        analysis = quiz_manager.get_performance_analysis(quiz)
        session_manager.update_quiz_results(
            session_id, quiz.to_dict(), quiz.score, quiz.total
        )

        return jsonify({
            'score': quiz.score,
            'total': quiz.total,
            'percentage': quiz.percentage,
            'analysis': analysis
        })
    except Exception as e:
        logger.error(f"Complete error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/results/<session_id>')
def results_page(session_id):
    quiz = quiz_store.get(session_id)
    db_session = session_manager.get_session(session_id)

    if not quiz and not db_session:
        return render_template('404.html'), 404

    return render_template('results.html',
                          session_id=session_id,
                          topic=db_session.topic if db_session else "Topic")


@app.route('/api/insights/<session_id>')
@rate_limit
def api_get_insights(session_id):
    try:
        quiz = quiz_store.get(session_id)
        db_session = session_manager.get_session(session_id)

        if not quiz and not db_session:
            return jsonify({'error': 'Session not found'}), 404

        if quiz:
            topic = db_session.topic if db_session else "Topic"
            wrong_concepts = quiz.get_wrong_concepts()
            prompt = InsightsPrompts.get_insights_prompt(
                topic, quiz.score, quiz.total, wrong_concepts
            )
            insights = claude_client.generate_insights(
                InsightsPrompts.SYSTEM_PROMPT, prompt
            )
            return jsonify({'insights': insights})
        else:
            return jsonify({'insights': 'Complete the quiz to see personalized insights.'})
    except Exception as e:
        logger.error(f"Insights error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/history')
def history_page():
    return render_template('history.html')


@app.route('/api/history')
def api_history():
    try:
        history = session_manager.get_history(limit=20)
        stats = session_manager.get_stats()
        return jsonify({'sessions': history, 'stats': stats})
    except Exception as e:
        logger.error(f"History error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/usage')
def api_usage():
    return jsonify(claude_client.get_usage_stats())


@app.errorhandler(404)
def not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug, threaded=True)
