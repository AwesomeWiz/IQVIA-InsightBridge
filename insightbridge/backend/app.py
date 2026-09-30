"""Flask API for InsightBridge."""

import sqlite3

from flask import Flask, jsonify, request

from intent_parser import parse_question
from ollama_client import interpret_with_ollama
from query_engine import answer_question


app = Flask(__name__)


@app.after_request
def add_cors_headers(response):
    response.headers["Access-Control-Allow-Origin"] = "http://localhost:5173"
    response.headers["Access-Control-Allow-Headers"] = "Content-Type"
    response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
    return response


@app.route("/api/query", methods=["POST", "OPTIONS"])
def query():
    if request.method == "OPTIONS":
        return "", 204

    payload = request.get_json(silent=True) or {}
    question = payload.get("question")
    if not isinstance(question, str) or not question.strip():
        return jsonify({"error": "Please enter a business question."}), 400
    if len(question) > 500:
        return jsonify({"error": "Please keep the question under 500 characters."}), 400

    parsed = parse_question(question.strip())
    if parsed["intent"] == "clarification":
        return jsonify({
            "summary": parsed["clarification"], "columns": [], "rows": [], "sql": None,
            "explanation": {"intent": "clarification", "tables": [], "filters": [], "parser": "rules"},
            "clarification": parsed["clarification"],
        })

    if parsed["intent"] == "unsupported":
        parsed = interpret_with_ollama(question.strip()) or parsed
    if parsed["intent"] == "unsupported":
        return jsonify({
            "summary": parsed["clarification"], "columns": [], "rows": [], "sql": None,
            "explanation": {"intent": "unsupported", "tables": [], "filters": [], "parser": "rules"},
            "clarification": parsed["clarification"],
        })

    try:
        return jsonify(answer_question(parsed))
    except (sqlite3.Error, ValueError):
        app.logger.exception("Could not answer query")
        return jsonify({"error": "The question could not be answered because the data query failed."}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
