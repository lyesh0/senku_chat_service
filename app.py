"""
Flask web application for Qwen model fine-tuning service.

This application provides a web interface for users to:
- Select roles from predefined JSON files
- Configure training parameters
- Start fine-tuning jobs
- Monitor training progress
- Interact with fine-tuned models
"""

import os
import json
import requests
from pathlib import Path

# Attempt to import Flask and related utilities.  If Flask is unavailable
# (for example in environments where the web framework is not installed),
# substitute dummy implementations so that this module can be imported
# without raising ImportError.
try:
    from flask import Flask, render_template, request, jsonify, redirect, url_for  # type: ignore
except Exception:
    Flask = None  # type: ignore
    # Provide minimal stand‑ins for the functions we use.  These will raise
    # informative errors if invoked in environments without Flask.
    def render_template(*args, **kwargs):  # type: ignore
        raise RuntimeError("Flask is not available in this environment.")

    def jsonify(*args, **kwargs):  # type: ignore
        raise RuntimeError("Flask is not available in this environment.")

    def redirect(*args, **kwargs):  # type: ignore
        raise RuntimeError("Flask is not available in this environment.")

    def url_for(*args, **kwargs):  # type: ignore
        raise RuntimeError("Flask is not available in this environment.")

    class _DummyRequest:
        """Fallback request object when Flask is not installed."""
        def get_json(self):
            raise RuntimeError("Flask is not available in this environment.")
    request = _DummyRequest()  # type: ignore

# Create the Flask application if Flask is available; otherwise use None.
app = Flask(__name__) if Flask else None

# Configuration
SERVER_URL = os.getenv("SERVER_URL", "http://localhost:8000")
ROLES_DIR = Path(__file__).parent.parent / "roles"

if app:
    @app.route('/')
    def index():
        """Main page - Role selection and training interface."""
        return render_template('index.html')

if app:
    @app.route('/api/roles')
    def get_roles():
        """Get list of available roles."""
        try:
            roles = []
            if ROLES_DIR.exists():
                for role_file in ROLES_DIR.glob('*.json'):
                    if role_file.name.startswith('_'):
                        continue  # Skip template files

                    try:
                        with open(role_file, 'r', encoding='utf-8') as f:
                            role_data = json.load(f)

                        roles.append({
                            'name': role_data.get('character_name', role_file.stem),
                            'file': role_file.name,
                            'original_work': role_data.get('original_work', ''),
                            'description': role_data.get('character_description', {}).get('basic_info', '')
                        })
                    except Exception as e:
                        print(f"Error loading role {role_file}: {e}")
                        continue

            return jsonify({'roles': roles})
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if app:
    @app.route('/api/train', methods=['POST'])
    def start_training():
        """Start a fine‑tuning job."""
        try:
            data = request.get_json()

            # Validate required fields
            required_fields = ['role', 'batch_size', 'epochs']
            for field in required_fields:
                if field not in data:
                    return jsonify({'error': f'Missing required field: {field}'}), 400

            # Forward request to server, including optional parameters for training mode and LoRA usage.
            server_payload = {
                'role': data['role'],
                'batch_size': int(data['batch_size']),
                'epochs': int(data['epochs']),
                # Pass through training_mode if provided, default to 'local'
                'training_mode': data.get('training_mode', 'local'),
                'use_lora': bool(data.get('use_lora', True))
            }

            response = requests.post(f"{SERVER_URL}/train", json=server_payload)

            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Server error'}), response.status_code

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/ssh/status')
    def ssh_status_proxy():
        """Proxy endpoint to check SSH connection status via the backend server."""
        try:
            response = requests.get(f"{SERVER_URL}/ssh/status")
            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Server error'}), response.status_code
        except Exception as e:
            return jsonify({'error': str(e)}), 500

if app:
    @app.route('/api/status/<model_id>')
    def get_training_status(model_id):
        """Get training status for a specific model."""
        try:
            response = requests.get(f"{SERVER_URL}/status/{model_id}")

            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Server error'}), response.status_code

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/api/download/<model_id>')
    def download_model(model_id):
        """Download a trained model."""
        try:
            response = requests.get(f"{SERVER_URL}/download/{model_id}")

            if response.status_code == 200:
                return jsonify(response.json())
            else:
                return jsonify({'error': 'Server error'}), response.status_code

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    @app.route('/chat/<model_id>')
    def chat_interface(model_id):
        """Chat interface for a specific fine-tuned model."""
        return render_template('chat.html', model_id=model_id)

    @app.route('/api/chat/<model_id>', methods=['POST'])
    def chat_with_model(model_id):
        """Send a chat message to a fine-tuned model."""
        try:
            data = request.get_json()

            if 'message' not in data:
                return jsonify({'error': 'Missing message field'}), 400

            # Forward to server (this would need to be implemented on the server side)
            server_payload = {
                'model_id': model_id,
                'message': data['message'],
                'max_tokens': data.get('max_tokens', 256),
                'temperature': data.get('temperature', 0.7)
            }

            # For now, return a placeholder response
            # In production, this would call the actual model
            return jsonify({
                'response': f"This is a response from model {model_id} to: {data['message']}",
                'model_id': model_id
            })

        except Exception as e:
            return jsonify({'error': str(e)}), 500

    if __name__ == '__main__' and app:
        # Only run the development server when Flask is available.
        app.run(
            host=os.getenv('HOST', '0.0.0.0'),
            port=int(os.getenv('PORT', '5000')),
            debug=os.getenv('DEBUG', 'false').lower() == 'true'
        )
