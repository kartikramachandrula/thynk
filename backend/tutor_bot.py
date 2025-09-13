from flask import Flask, request, jsonify
import os
import json
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration
CLAUDE_API_KEY = os.getenv('CLAUDE_KEY')
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

if not CLAUDE_API_KEY:
    raise ValueError("CLAUDE_KEY environment variable is required")

def call_claude_api(messages: List[Dict[str, str]], max_tokens: int = 1000) -> Dict[str, Any]:
    """
    Call the Claude API with the given messages
    """
    headers = {
        "Content-Type": "application/json",
        "x-api-key": CLAUDE_API_KEY,
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": "claude-sonnet-4-20250514",
        "max_tokens": max_tokens,
        "messages": messages
    }
    
    try:
        response = requests.post(CLAUDE_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        # Add more detailed error information
        error_msg = f"Claude API request failed: {str(e)}"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
                error_msg += f" - Response: {error_detail}"
            except:
                error_msg += f" - Status: {e.response.status_code}, Text: {e.response.text[:200]}"
        raise Exception(error_msg)

def format_student_work(work_steps: List[Dict[str, Any]]) -> str:
    """
    Format student work steps into a readable string for Claude
    """
    if not work_steps:
        return "No work steps provided."
    
    formatted_work = "Student's work (step by step):\n"
    for i, step in enumerate(work_steps, 1):
        formatted_work += f"Step {i}: {json.dumps(step, indent=2)}\n"
    
    return formatted_work

def format_lesson_context(lesson: Dict[str, Any]) -> str:
    """
    Format lesson context into a readable string for Claude
    """
    if not lesson or not any(lesson.values()):
        return "No lesson context provided (empty lesson)."
    
    return f"Lesson context:\n{json.dumps(lesson, indent=2)}"

@app.route('/check', methods=['GET'])
def check_work():
    """
    Endpoint 1: Check student work and identify the first incorrect step
    """
    try:
        # Get JSON data from request
        work_data = request.json
        if not work_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        student_work = work_data.get('work', [])
        lesson_context = work_data.get('lesson', {})
        
        # Format the data for Claude
        work_formatted = format_student_work(student_work)
        lesson_formatted = format_lesson_context(lesson_context)
        
        # Create prompt for Claude
        prompt = f"""You are an expert tutor reviewing a student's mathematical work. Your task is to:

1. Carefully examine each step of the student's work
2. Identify the FIRST incorrect step (if any)
3. Explain why it's incorrect
4. Provide guidance on how to fix it

{lesson_formatted}

{work_formatted}

Please respond in JSON format with the following structure:
{{
    "is_correct": boolean,
    "first_error_step": number or null,
    "error_description": "string describing what's wrong",
    "correction_guidance": "string explaining how to fix it",
    "overall_feedback": "string with general feedback"
}}

If all steps are correct, set "is_correct" to true and "first_error_step" to null."""

        # Call Claude API
        messages = [{"role": "user", "content": prompt}]
        claude_response = call_claude_api(messages)
        
        # Extract the response content
        response_content = claude_response.get('content', [{}])[0].get('text', '')
        
        # Try to parse as JSON, fallback to text response if parsing fails
        try:
            result = json.loads(response_content)
        except json.JSONDecodeError:
            result = {
                "is_correct": False,
                "first_error_step": None,
                "error_description": "Could not parse Claude response",
                "correction_guidance": response_content,
                "overall_feedback": "Please review the work manually"
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/hint', methods=['GET'])
def get_hint():
    """
    Endpoint 2: Check work accuracy and provide hint for next step
    """
    try:
        # Get JSON data from request
        work_data = request.json
        if not work_data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        student_work = work_data.get('work', [])
        lesson_context = work_data.get('lesson', {})
        
        # Format the data for Claude
        work_formatted = format_student_work(student_work)
        lesson_formatted = format_lesson_context(lesson_context)
        
        # Create prompt for Claude
        prompt = f"""You are an expert tutor helping a student with their mathematical work. Your task is to:

1. First, check if the current work is accurate
2. Then, provide a helpful hint for the next step (without giving away the complete solution)

{lesson_formatted}

{work_formatted}

Please respond in JSON format with the following structure:
{{
    "work_is_accurate": boolean,
    "accuracy_feedback": "string describing any issues with current work",
    "next_step_hint": "string with a helpful hint for the next step",
    "encouragement": "string with encouraging feedback"
}}

Make sure your hint guides the student toward the solution without solving it completely for them."""

        # Call Claude API
        messages = [{"role": "user", "content": prompt}]
        claude_response = call_claude_api(messages)
        
        # Extract the response content
        response_content = claude_response.get('content', [{}])[0].get('text', '')
        
        # Try to parse as JSON, fallback to text response if parsing fails
        try:
            result = json.loads(response_content)
        except json.JSONDecodeError:
            result = {
                "work_is_accurate": True,
                "accuracy_feedback": "Could not parse Claude response",
                "next_step_hint": response_content,
                "encouragement": "Keep up the good work!"
            }
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint
    """
    return jsonify({"status": "healthy", "message": "Tutor bot is running"})

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=3000)
