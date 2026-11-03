import hmac
import os
from functools import wraps
from flask import Flask, render_template, jsonify, request
import configmap
import machines
import log

API_TOKEN = os.environ.get("API_TOKEN")

app = Flask(__name__)

def get_log_contents():
    try:
        with open(log.INFO_LOG_FILE, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-100:])
    except FileNotFoundError:
        return "Log file not found."

def require_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        if not API_TOKEN:
            return jsonify(error="machine API disabled, set API_TOKEN to enable it"), 403
        auth = request.headers.get("Authorization", "")
        if not hmac.compare_digest(auth, f"Bearer {API_TOKEN}"):
            return jsonify(error="unauthorized"), 401
        return f(*args, **kwargs)
    return wrapper

@app.errorhandler(machines.MachineError)
def handle_machine_error(e):
    return jsonify(error=str(e)), e.http_code

@app.route('/')
def machine_status():
    statuses = configmap.get_all_machine_statuses()
    wait_finish_runs = configmap.get_wait_finish_runs() or []
    log_contents = get_log_contents()
    return render_template('status.html', statuses=statuses, wait_finish_runs=wait_finish_runs, log_contents=log_contents)

@app.route('/log')
def log_data():
    return jsonify(log=get_log_contents())

@app.route('/api/machines', methods=['GET'])
def list_machines():
    return jsonify(machines.list_machines())

@app.route('/api/machines', methods=['POST'])
@require_token
def add_machine():
    body = request.get_json(silent=True) or {}
    name = body.get("name")
    machines.add_machine(name, body.get("host"), body.get("username"), body.get("private_key"))
    return jsonify(name=name, status="free"), 201

@app.route('/api/machines/<name>', methods=['DELETE'])
@require_token
def remove_machine(name):
    machines.remove_machine(name)
    return "", 204

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
