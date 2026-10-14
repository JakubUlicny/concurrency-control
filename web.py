from flask import Flask, render_template, jsonify
import configmap
import log

app = Flask(__name__)

def get_log_contents():
    try:
        with open(log.INFO_LOG_FILE, 'r') as f:
            lines = f.readlines()
            return ''.join(lines[-100:])
    except FileNotFoundError:
        return "Log file not found."

@app.route('/')
def machine_status():
    statuses = configmap.get_all_machine_statuses()
    wait_finish_runs = configmap.get_wait_finish_runs() or []
    log_contents = get_log_contents()
    return render_template('status.html', statuses=statuses, wait_finish_runs=wait_finish_runs, log_contents=log_contents)

@app.route('/log')
def log_data():
    return jsonify(log=get_log_contents())

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
