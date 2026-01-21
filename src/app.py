"""
Carte Blanche - Flask Web Server
웹 UI 및 REST API 제공
"""
import os
import sys
import time
import json
import threading

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

from src.engine import RuleEngine
from src.watcher import get_watcher, FileEventHandler
from watchdog.observers import Observer

app = Flask(__name__, static_folder='../web')
CORS(app)

# 규칙 엔진 및 Watcher 초기화
_watcher = get_watcher()
rule_engine = _watcher.rule_engine


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
        get_watcher().reload_rules()
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
        get_watcher().reload_rules()
        return jsonify({"success": True, "message": "Rule updated"})
    return jsonify({"success": False, "error": "Failed to update rule"}), 404


@app.route('/api/rules/<rule_id>', methods=['DELETE'])
def delete_rule(rule_id):
    """규칙 삭제"""
    success = rule_engine.delete_rule(rule_id)
    if success:
        get_watcher().reload_rules()
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
    
    # 이미 실행 중이면 패스
    if watcher.is_running():
        return jsonify({"success": True, "message": "Watcher already running"})
    
    # Observer가 재사용 불가능하면 재시작
    if not watcher.observer.is_alive() and watcher._running == False:
        watcher.observer = Observer()
        watcher.event_handler = FileEventHandler(watcher.rule_engine)
    
    # 백그라운드 스레드에서 시작
    thread = threading.Thread(target=watcher.start, daemon=True)
    thread.start()
    
    # 시작 확인을 위해 잠시 대기
    time.sleep(0.5)
    
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


# ==================== Batch Processing API ====================

@app.route('/api/rules/<rule_id>/scan', methods=['GET'])
def scan_unprocessed_files(rule_id):
    """규칙에 맞는 미처리 파일 스캔"""
    rule = rule_engine.get_rule(rule_id)
    if not rule:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    
    trigger = rule.get('trigger', {})
    input_path = trigger.get('path', '')
    extensions = trigger.get('extensions', [])
    
    action = rule.get('action', {})
    output_path = action.get('output_path', '')
    action_type = action.get('type', '')
    
    if not os.path.exists(input_path):
        return jsonify({"success": False, "error": "Input path does not exist"}), 400
    
    # 액션 타입별 설명
    action_labels = {
        'process_txt': '텍스트 요약',
        'process_xlsx': '엑셀 추출', 
        'open_in_notepad': '메모장 열기 (GUI)',
        'run_workflow': '워크플로우 실행'
    }
    
    # Input 폴더의 파일들 스캔
    unprocessed = []
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)
        if not os.path.isfile(file_path):
            continue
        
        # 확장자 체크
        file_ext = os.path.splitext(filename)[1].lower()
        if extensions and file_ext not in extensions:
            continue
        
        # GUI 액션 (메모장) - output 파일 존재 여부로 확인
        if action_type == 'open_in_notepad':
            output_file = os.path.join(output_path, f"notepad_{filename}")
            
            if not os.path.exists(output_file):
                unprocessed.append({
                    "filename": filename, 
                    "path": file_path, 
                    "status": "액션 대기",
                    "action_type": action_type
                })
            elif os.path.getmtime(file_path) > os.path.getmtime(output_file):
                unprocessed.append({
                    "filename": filename, 
                    "path": file_path, 
                    "status": "업데이트 필요",
                    "action_type": action_type
                })
            continue
        
        # Output 파일 존재 여부 확인 (파일 처리 액션)
        if action_type == 'process_txt':
            # 사용자 요청: 기본 텍스트 요약은 summary_로 고정
            output_file = os.path.join(output_path, f"summary_{filename}")
        elif action_type == 'process_xlsx':
            output_file = os.path.join(output_path, f"extract_{os.path.splitext(filename)[0]}.txt")
        elif action_type == 'run_workflow':
            # 워크플로우 내의 prefix 설정을 동적으로 찾아서 패턴에 추가
            wf_patterns = [filename]
            # 기본 패턴 추가 (커버리지 확보) - summary_를 최우선으로 체크하도록 순서 조정
            for p in ["summary_", "processed_", "처리됨_"]:
                pattern = f"{p}{filename}"
                if pattern not in wf_patterns: wf_patterns.append(pattern)
                
            wf_args = action.get('args', {})
            wf_name = wf_args.get('workflow_name', 'workflow.json')
            wf_path = os.path.join(WORKFLOWS_DIR, wf_name if wf_name.endswith('.json') else f"{wf_name}.json")
            
            if os.path.exists(wf_path):
                try:
                    with open(wf_path, 'r', encoding='utf-8') as f:
                        wf_data = json.load(f)
                        for wf_act in wf_data.get('actions', []):
                            if wf_act.get('tool') == 'save_to_output':
                                p = wf_act.get('args', {}).get('prefix', '')
                                if p: wf_patterns.insert(0, f"{p}{filename}")
                except: pass
            
            # 기본 패턴 추가 (커버리지 확보)
            for p in ["summary_", "processed_", "처리됨_"]:
                pattern = f"{p}{filename}"
                if pattern not in wf_patterns: wf_patterns.append(pattern)
                
            output_file = os.path.join(output_path, filename) # 기본값
            for p in wf_patterns:
                tmp = os.path.join(output_path, p)
                if os.path.exists(tmp):
                    output_file = tmp
                    break
        else:
            output_file = os.path.join(output_path, filename)
        
        # 미처리 파일 또는 Input이 Output보다 최신인 파일
        if not os.path.exists(output_file):
            unprocessed.append({
                "filename": filename, 
                "path": file_path, 
                "status": "미처리",
                "action_type": action_type
            })
        elif os.path.getmtime(file_path) > os.path.getmtime(output_file):
            unprocessed.append({
                "filename": filename, 
                "path": file_path, 
                "status": "업데이트 필요",
                "action_type": action_type
            })
    
    return jsonify({
        "success": True,
        "rule_name": rule.get('name'),
        "action_type": action_type,
        "action_label": action_labels.get(action_type, action_type),
        "unprocessed_files": unprocessed,
        "count": len(unprocessed)
    })


@app.route('/api/rules/<rule_id>/process-all', methods=['POST'])
def process_all_files(rule_id):
    """규칙에 맞는 모든 미처리 파일 일괄 처리"""
    import time
    from src.workers import execute_action
    
    rule = rule_engine.get_rule(rule_id)
    if not rule:
        return jsonify({"success": False, "error": "Rule not found"}), 404
    
    trigger = rule.get('trigger', {})
    input_path = trigger.get('path', '')
    extensions = trigger.get('extensions', [])
    
    action = rule.get('action', {})
    output_path = action.get('output_path', '')
    action_type = action.get('type', '')
    
    if not os.path.exists(input_path):
        return jsonify({"success": False, "error": "Input path does not exist"}), 400
    
    # 처리할 파일 목록 (요청에서 받거나 전체)
    data = request.get_json() or {}
    files_to_process = data.get('files', None)
    
    # GUI 액션 여부 판별 (워크플로우 내부 도구 포함)
    is_gui_action = action_type == 'open_in_notepad'
    if action_type == 'run_workflow':
        wf_args = action.get('args', {})
        wf_name = wf_args.get('workflow_name', 'workflow.json')
        wf_path = os.path.join(WORKFLOWS_DIR, wf_name if wf_name.endswith('.json') else f"{wf_name}.json")
        if os.path.exists(wf_path):
            try:
                with open(wf_path, 'r', encoding='utf-8') as f:
                    wf_data = json.load(f)
                    for wf_act in wf_data.get('actions', []):
                        if wf_act.get('tool') in ['open_notepad', 'open_excel', 'open_browser']:
                            is_gui_action = True
                            break
            except: pass

    if is_gui_action:
        print(f"\n⚠️ [Batch] GUI 액동 일괄 처리 시작 ({action_type}) - 마우스/키보드 조작을 피해주세요!")
    
    results = []
    success_count = 0
    for filename in os.listdir(input_path):
        file_path = os.path.join(input_path, filename)
        if not os.path.isfile(file_path):
            continue
        
        # 확장자 체크
        file_ext = os.path.splitext(filename)[1].lower()
        if extensions and file_ext not in extensions:
            continue
        
        # 특정 파일만 처리하는 경우
        if files_to_process and filename not in files_to_process:
            continue
        
        # 액션 실행
        action_args = action.get('args', {})
        try:
            result = execute_action(action_type, file_path, output_path, args=action_args)
            if result.get('success'):
                success_count += 1
            results.append({"filename": filename, "result": result})
        except Exception as e:
            results.append({"filename": filename, "result": {"success": False, "error": str(e)}})
        
        # GUI 액션은 파일 간 딜레이를 줘서 안정성 확보
        if is_gui_action:
            time.sleep(2)  # 2초 대기 (다음 파일을 위해)
    
    if is_gui_action:
        print("✅ [Batch] GUI 액션 일괄 처리 완료!\n")
    
    return jsonify({
        "success": success_count > 0, # 최소 하나라도 성공하면 success: True (UI 피드백용)
        "processed": success_count,
        "results": results
    })


# ==================== Action Types API ====================

@app.route('/api/actions', methods=['GET'])
def get_action_types():
    """사용 가능한 액션 타입 목록"""
    actions = [
        {"type": "process_txt", "name": "텍스트 파일 처리", "description": "텍스트 파일 읽기 및 요약"},
        {"type": "process_xlsx", "name": "엑셀 파일 처리", "description": "엑셀 파일 데이터 추출"},
        {"type": "open_in_notepad", "name": "메모장에서 열기", "description": "GUI 자동화 - 메모장 실행 및 내용 작성"},
        {"type": "run_workflow", "name": "워크플로우 실행", "description": "JSON 기반 동적 워크플로우 실행"},
    ]
    return jsonify({"success": True, "actions": actions})


# ==================== Workflow API ====================

WORKFLOWS_DIR = os.path.join(PROJECT_ROOT, 'config', 'workflows')
os.makedirs(WORKFLOWS_DIR, exist_ok=True)

@app.route('/api/workflows', methods=['GET'])
def list_workflows():
    """워크플로우 파일 목록 조회 (내부 이름 포함)"""
    try:
        workflows = []
        for f in os.listdir(WORKFLOWS_DIR):
            if f.endswith('.json'):
                path = os.path.join(WORKFLOWS_DIR, f)
                try:
                    with open(path, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        workflows.append({
                            "filename": f,
                            "name": data.get("workflow_name", f.replace('.json', ''))
                        })
                except:
                    workflows.append({"filename": f, "name": f.replace('.json', '')})
        return jsonify({"success": True, "workflows": workflows})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/workflow/<name>', methods=['GET'])
def get_workflow(name):
    """특정 워크플로우 설정 조회"""
    try:
        path = os.path.join(WORKFLOWS_DIR, name if name.endswith('.json') else f"{name}.json")
        if os.path.exists(path):
            with open(path, 'r', encoding='utf-8') as f:
                workflow = json.load(f)
            return jsonify({"success": True, "workflow": workflow})
        return jsonify({"success": False, "error": f"Workflow '{name}' not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/workflow/<name>', methods=['PUT'])
def update_workflow(name):
    """워크플로우 설정 저장"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        path = os.path.join(WORKFLOWS_DIR, name if name.endswith('.json') else f"{name}.json")
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        return jsonify({"success": True, "message": f"Workflow '{name}' saved"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/workflow/<name>', methods=['DELETE'])
def delete_workflow(name):
    """워크플로우 파일 삭제"""
    try:
        path = os.path.join(WORKFLOWS_DIR, name if name.endswith('.json') else f"{name}.json")
        if os.path.exists(path):
            os.remove(path)
            return jsonify({"success": True, "message": f"Workflow '{name}' deleted"})
        return jsonify({"success": False, "error": "File not found"})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/workflow/tools', methods=['GET'])
def get_available_tools_with_templates():
    """사용 가능한 도구 및 사용자 친화적 템플릿 목록"""
    try:
        from src.tools import tool_registry, get_tool_templates
        tools = tool_registry.list_tools()
        templates = get_tool_templates()
        
        # 템플릿 정보 병합
        for tool in tools:
            tool_name = tool['name']
            if tool_name in templates:
                tool.update(templates[tool_name])
        
        return jsonify({"success": True, "tools": tools})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/workflow/test', methods=['POST'])
def test_workflow():
    """워크플로우 테스트 실행"""
    try:
        from src.workflow_engine import WorkflowEngine
        
        data = request.get_json() or {}
        test_file = data.get('test_file', '')
        
        # 테스트할 워크플로우 경로 (기본값 또는 요청된 것)
        wf_name = data.get('workflow_name', 'workflow.json')
        path = os.path.join(WORKFLOWS_DIR, wf_name if wf_name.endswith('.json') else f"{wf_name}.json")
        
        if not os.path.exists(path):
            # 구버전 config 폴더도 체크
            path = os.path.join(PROJECT_ROOT, 'config', wf_name if wf_name.endswith('.json') else f"{wf_name}.json")

        engine = WorkflowEngine(path)
        result = engine.execute({
            "trigger.file_path": test_file or "test_input.txt",
            "trigger.file_name": os.path.basename(test_file) if test_file else "test_input.txt",
            "trigger.file_dir": os.path.dirname(test_file) if test_file else os.getcwd(),
            "trigger.output_path": os.getcwd() # 테스트 시에는 현재 작업 디렉토리 기준
        })
        
        return jsonify({"success": True, "result": result})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


@app.route('/api/utils/picker', methods=['GET'])
def path_picker():
    """네이티브 파일/폴더 선택창 오픈"""
    mode = request.args.get('mode', 'folder') # folder or file
    title = request.args.get('title', '경로 선택')
    
    try:
        import tkinter as tk
        from tkinter import filedialog
        
        root = tk.Tk()
        root.withdraw() # 메인 창 숨기기
        root.attributes('-topmost', True) # 창을 최상단으로
        
        selected_path = ""
        if mode == 'folder':
            selected_path = filedialog.askdirectory(title=title, parent=root)
        else:
            selected_path = filedialog.askopenfilename(title=title, parent=root)
            
        root.destroy()
        
        if selected_path:
            # 윈도우 경로 구분자 정규화 (Backslash -> Slash)
            selected_path = selected_path.replace('\\', '/')
            return jsonify({"success": True, "path": selected_path})
        else:
            return jsonify({"success": False, "error": "Cancelled"})
            
    except Exception as e:
        return jsonify({"success": False, "error": str(e)})


if __name__ == '__main__':
    import json
    print("\n=== Carte Blanche Web Server ===")
    print("URL: http://localhost:5000")
    print("API: http://localhost:5000/api/rules")
    print("Workflow Editor: http://localhost:5000/workflow.html")
    print("================================\n")
    app.run(debug=True, port=5000)

