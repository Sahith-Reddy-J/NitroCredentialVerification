from flask import Flask, request, jsonify, send_from_directory
from threading import Semaphore
import logging

app = Flask(__name__, static_folder='../frontend')
sign_semaphore = Semaphore(10)  # Rate limiting

@app.route('/')
def serve_ui():
    return send_from_directory('../frontend', 'index.html')

@app.route('/home')
def serve_ui():
    return "Hello, World!"

@app.route('/sign-skill', methods=['POST'])
def handle_sign_request():
    if not sign_semaphore.acquire(blocking=False):
        return jsonify({"error": "System busy"}), 503
        
    try:
        data = request.get_json()
        required = {'student_id', 'skill'}
        
        if not all(k in data for k in required):
            return jsonify({"error": "Missing fields"}), 400
            
        if len(data['skill']) > 100 or len(data['student_id']) > 50:
            return jsonify({"error": "Invalid input"}), 400
            
        from client import sign_skill
        response = sign_skill(data)
        return jsonify(response)
        
    except Exception as e:
        logging.error(f"Signing error: {str(e)}")
        return jsonify({"error": "Processing failed"}), 500
        
    finally:
        sign_semaphore.release()

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    app.run(host='0.0.0.0', port=5000)