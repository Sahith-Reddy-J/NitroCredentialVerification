from flask import Flask, request, jsonify, send_from_directory
from threading import Semaphore
import logging
import traceback

app = Flask(__name__, static_folder='../frontend')
sign_semaphore = Semaphore(10)

@app.route('/')
def serve_ui():
    return send_from_directory('../frontend', 'index.html')

@app.route('/sign-skill', methods=['POST'])
def handle_sign_request():
    if not sign_semaphore.acquire(blocking=False):
        return jsonify({"error": "System busy"}), 503
        
    try:
        data = request.get_json()
        print(f"Received data from frontend: {data}")
        # Validate input
        required = {'student_id', 'skill'}
        if not all(k in data for k in required):
            return jsonify({"error": "Missing student_id or skill"}), 400
            
        # Sanitize input
        sanitized_data = {
            "student_id": str(data['student_id']).strip()[:50],
            "skill": str(data['skill']).strip()[:100]
        }
        print(f"Sanitized data and sending to sign: {sanitized_data}")
        from client import sign_skill
        response = sign_skill(sanitized_data)
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Signing Error: {traceback.format_exc()}")
        return jsonify({"error": "Internal processing error"}), 500
        
    finally:
        sign_semaphore.release()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000)