"""
Carte Blanche - Action Handler Module
실제 PC 조작 (GUI Automation) 기능
"""
import os
import subprocess
import time
from datetime import datetime

# GUI 자동화 라이브러리
import pyautogui
import pyperclip


class ActionHandler:
    """PC GUI 조작을 수행하는 핸들러"""
    
    def __init__(self):
        # pyautogui 안전 설정
        pyautogui.FAILSAFE = True  # 마우스를 왼쪽 상단으로 이동하면 중지
        pyautogui.PAUSE = 0.1  # 각 동작 사이 딜레이
    
    def open_notepad_and_write(self, content: str, save_path: str = None) -> dict:
        """
        내용을 파일로 저장하고 메모장에서 엽니다.
        
        Args:
            content: 저장할 내용
            save_path: 저장할 전체 경로 (None이면 자동 생성)
        
        Returns:
            결과 딕셔너리
        """
        try:
            # 1. 저장 경로 설정
            if save_path is None:
                save_path = f"완료_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            
            print(f"[ActionHandler] 파일 저장 중: {save_path}")
            
            # 2. 직접 파일로 저장 (GUI 저장 대신)
            with open(save_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            print("[ActionHandler] 파일 저장 완료!")
            
            # 3. 저장된 파일을 메모장으로 열기 (확인용)
            print("[ActionHandler] 메모장에서 열기...")
            process = subprocess.Popen(['notepad.exe', save_path])
            
            # 메모장이 열릴 때까지 잠시 대기
            time.sleep(1)
            
            print(f"[ActionHandler] 완료: {save_path}")
            return {
                "success": True, 
                "message": f"저장 완료: {save_path}",
                "output_file": save_path,
                "process_id": process.pid
            }
            
        except Exception as e:
            print(f"[ActionHandler] 오류 발생: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def _type_text_korean(self, text: str):
        """
        한글 텍스트를 클립보드를 통해 입력합니다.
        (pyautogui는 한글 직접 입력이 안 되므로)
        """
        # 클립보드에 텍스트 복사
        pyperclip.copy(text)
        
        # Ctrl+V로 붙여넣기
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.3)
    
    def close_active_window(self):
        """현재 활성 창을 닫습니다 (Alt+F4)"""
        pyautogui.hotkey('alt', 'F4')
        time.sleep(0.5)
    
    def click_at(self, x: int, y: int):
        """특정 좌표를 클릭합니다"""
        pyautogui.click(x, y)
    
    def type_text(self, text: str, korean: bool = True):
        """텍스트를 입력합니다"""
        if korean:
            self._type_text_korean(text)
        else:
            pyautogui.typewrite(text)
    
    def press_key(self, key: str):
        """키를 누릅니다"""
        pyautogui.press(key)
    
    def hotkey(self, *keys):
        """단축키를 누릅니다 (예: hotkey('ctrl', 'c'))"""
        pyautogui.hotkey(*keys)
import json

# 처리 로그 파일 경로
PROCESSED_LOG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'processed_log.json')


def load_processed_log() -> dict:
    """처리 완료된 파일 목록 로드"""
    try:
        if os.path.exists(PROCESSED_LOG_PATH):
            with open(PROCESSED_LOG_PATH, 'r', encoding='utf-8') as f:
                return json.load(f)
    except:
        pass
    return {"gui_actions": {}}


def save_processed_log(log: dict):
    """처리 완료된 파일 목록 저장"""
    os.makedirs(os.path.dirname(PROCESSED_LOG_PATH), exist_ok=True)
    with open(PROCESSED_LOG_PATH, 'w', encoding='utf-8') as f:
        json.dump(log, f, indent=2, ensure_ascii=False)


def mark_as_processed(file_path: str, action_type: str):
    """파일을 처리 완료로 기록"""
    log = load_processed_log()
    if action_type not in log:
        log[action_type] = {}
    log[action_type][file_path] = {
        "processed_at": datetime.now().isoformat(),
        "mtime": os.path.getmtime(file_path)
    }
    save_processed_log(log)


def is_already_processed(file_path: str, action_type: str) -> bool:
    """파일이 이미 처리되었는지 확인 (수정 시각 기준)"""
    log = load_processed_log()
    if action_type in log and file_path in log[action_type]:
        recorded = log[action_type][file_path]
        current_mtime = os.path.getmtime(file_path)
        return recorded.get("mtime") == current_mtime
    return False


def process_output_and_open_notepad(file_path: str, output_path: str = None) -> dict:
    """
    Input 파일을 읽고 메모장에서 열어 작성 후 output 폴더에 저장합니다.
    
    Args:
        file_path: 읽을 파일 경로
        output_path: 저장할 폴더 경로
    
    Returns:
        처리 결과
    """
    try:
        # 파일 내용 읽기
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 저장 파일명 생성 (notepad_원본파일명)
        original_filename = os.path.basename(file_path)
        save_filename = f"notepad_{original_filename}"
        
        # output_path가 있으면 전체 경로 생성
        if output_path:
            os.makedirs(output_path, exist_ok=True)
            full_save_path = os.path.join(output_path, save_filename)
        else:
            full_save_path = save_filename
        
        print(f"\n[ActionHandler] 파일 처리 시작: {original_filename}")
        print(f"[ActionHandler] 저장 위치: {full_save_path}")
        print("[ActionHandler] ⚠️ GUI 작업 중 - 마우스/키보드 조작을 피해주세요!")
        
        # 메모장에 열고 저장
        handler = ActionHandler()
        result = handler.open_notepad_and_write(content, full_save_path)
        
        # 성공 시 처리 완료로 기록
        if result.get("success"):
            mark_as_processed(file_path, "open_in_notepad")
            print("[ActionHandler] ✅ 처리 완료 기록됨")
        
        return result
        
    except Exception as e:
        return {"success": False, "error": str(e)}


# 테스트 코드
if __name__ == "__main__":
    handler = ActionHandler()
    
    test_content = """=== Carte Blanche 테스트 ===
    
이것은 LAM 서비스의 GUI 자동화 테스트입니다.
한글도 잘 입력되는지 확인합니다.

작성 시간: """ + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    result = handler.open_notepad_and_write(test_content)
    print(f"결과: {result}")
