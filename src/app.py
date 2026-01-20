"""
Carte Blanche - Flask Web Server
웹 UI 및 REST API 제공
"""
import os
import sys
import threading

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from src.engine import RuleEngine
from src.watcher import get_watcher

app = Flask(__name__, static_folder='../web')
CORS(app)

# 설정 경로
CONFIG_PATH = os.path.join(PROJECT_ROOT, 'config', 'rules.json')
rule_engine = RuleEngine(CONFIG_PATH)


# ==================== Static Files ====================

@app.route('/')
def index():
    """메인 페이지"""
    return send_from_directory(app.static_folder, 'index.html')


@app.route('/<path:filename>')
def static_files(filename):
    """정적 파일 서빙"""
    return send_from_directory(app.static_folder, filename)


# ==================== Rules API ====================

@app.route('/api/rules', methods=['GET'])
def get_rules():
    """모든 규칙 조회"""
    rules = rule_engine.get_all_rules()
    return jsonify({"success": True, "rules": rules})


@app.route('/api/rules', methods=['POST'])
def add_rule():
    """새 규칙 추가"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    success = rule_engine.add_rule(data)
    if success:
        return jsonify({"success": True, "message": "Rule added"})
    return jsonify({"success": False, "error": "Failed to add rule"}), 500


@app.route('/api/rules/<rule_id>', methods=['GET'])
def get_rule(rule_id):
    """특정 규칙 조회"""
    rule = rule_engine.get_rule(rule_id)
    if rule:
        return jsonify({"success": True, "rule": rule})
    return jsonify({"success": False, "error": "Rule not found"}), 404


@app.route('/api/rules/<rule_id>', methods=['PUT'])
def update_rule(rule_id):
    """규칙 업데이트"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "No data provided"}), 400
    
    success = rule_engine.update_rule(rule_id, data)
    if success:
        return jsonify({"success": True, "message": "Rule updated"})
    return jsonify({"success": False, "error": "Failed to update rule"}), 404


@app.route('/api/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """규칙 삭제"""
    success = rule_engine.delete_rule(rule_id)
    if success:
        return jsonify({"success": True, "message": "Rule deleted"})
    return jsonify({"success": False, "error": "Failed to delete rule"}), 404


# ==================== Watcher Control API ====================

@app.route('/api/watcher/status', methods=['GET'])
def watcher_status():
    """Watcher 상태 조회"""
    watcher = get_watcher()
    return jsonify({
        "success": True,
        "running": watcher.is_running(),
        "watched_paths": rule_engine.get_watched_paths()
    })


@app.route('/api/watcher/start', methods=['POST'])
def start_watcher():
    """Watcher 시작"""
    watcher = get_watcher()
    if watcher.is_running():
        return jsonify({"success": True, "message": "Watcher already running"})
    
    # 백그라운드 스레드에서 시작
    thread = threading.Thread(target=watcher.start, daemon=True)
    thread.start()
    
    return jsonify({"success": True, "message": "Watcher started"})


@app.route('/api/watcher/stop', methods=['POST'])
def stop_watcher():
    """Watcher 중지"""
    watcher = get_watcher()
    watcher.stop()
    return jsonify({"success": True, "message": "Watcher stopped"})


@app.route('/api/watcher/reload', methods=['POST'])
def reload_rules():
    """규칙 리로드"""
    rule_engine.load_rules()
    watcher = get_watcher()
    watcher.reload_rules()
    return jsonify({"success": True, "message": "Rules reloaded"})


# ==================== Action Types API ====================

@app.route('/api/actions', methods=['GET'])
def get_action_types():
    """사용 가능한 액션 타입 목록"""
    actions = [
        {"type": "process_txt", "name": "텍스트 파일 처리", "description": "텍스트 파일 읽기 및 요약"},
        {"type": "process_xlsx", "name": "엑셀 파일 처리", "description": "엑셀 파일 데이터 추출"},
    ]
    return jsonify({"success": True, "actions": actions})


if __name__ == '__main__':
    print("\n=== Carte Blanche Web Server ===")
    print("URL: http://localhost:5000")
    print("API: http://localhost:5000/api/rules")
    print("================================\n")
    app.run(debug=True, port=5000)
