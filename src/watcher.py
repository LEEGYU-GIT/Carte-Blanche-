"""
Carte Blanche - File Watcher
watchdog 기반 파일 시스템 감시자
"""
import os
import sys
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileCreatedEvent

# 프로젝트 루트 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_ROOT)

from src.engine import RuleEngine
from src.workers import execute_action


class FileEventHandler(FileSystemEventHandler):
    """파일 생성 및 수정 이벤트를 처리하는 핸들러"""
    
    def __init__(self, rule_engine: RuleEngine):
        self.rule_engine = rule_engine
        super().__init__()
    
    def _process_file(self, file_path: str, event_type: str):
        """파일 처리 공통 로직"""
        print(f"\n[Watcher] 파일 감지 ({event_type}): {file_path}")
        
        # 매칭되는 규칙 찾기 (file_created와 file_modified 모두 처리)
        matching_rules = self.rule_engine.find_matching_rules(
            file_path, 
            event_type="file_created"  # 규칙은 file_created로 통일
        )
        
        if not matching_rules:
            print(f"[Watcher] 매칭되는 규칙 없음")
            return
        
        # 매칭된 규칙들에 대해 액션 실행
        for rule in matching_rules:
            print(f"[Watcher] 규칙 적용: {rule.get('name')}")
            action = rule.get('action', {})
            action_type = action.get('type')
            output_path = action.get('output_path', '')
            
            if action_type:
                # 파일이 완전히 쓰여질 때까지 잠시 대기
                time.sleep(0.5)
                action_args = action.get('args', {})
                result = execute_action(action_type, file_path, output_path, args=action_args)
                print(f"[Watcher] 액션 결과: {result}")

    
    def on_created(self, event):
        if event.is_directory:
            return
        file_path = event.src_path.replace('\\', '/')
        self._process_file(file_path, "생성됨")
    
    def on_modified(self, event):
        if event.is_directory:
            return
        file_path = event.src_path.replace('\\', '/')
        self._process_file(file_path, "수정됨")


class FileWatcher:
    """파일 시스템 감시자"""
    
    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(PROJECT_ROOT, 'config', 'rules.json')
        
        self.rule_engine = RuleEngine(config_path)
        self.observer = Observer()
        self.event_handler = FileEventHandler(self.rule_engine)
        self._running = False
    
    def start(self):
        """감시 시작"""
        paths = self.rule_engine.get_watched_paths()
        
        if not paths:
            print("[Watcher] 감시할 경로가 없습니다.")
            return
        
        for path in paths:
            # 경로가 없으면 생성
            if not os.path.exists(path):
                os.makedirs(path, exist_ok=True)
                print(f"[Watcher] 폴더 생성됨: {path}")
            
            self.observer.schedule(self.event_handler, path, recursive=False)
            print(f"[Watcher] 감시 시작: {path}")
        
        self.observer.start()
        self._running = True
        print("\n[Watcher] === Carte Blanche 파일 감시자 실행 중 ===")
        print("[Watcher] 종료하려면 Ctrl+C를 누르세요.\n")
    
    def stop(self):
        """감시 중지"""
        if self._running:
            try:
                self.observer.stop()
                self.observer.join(timeout=2)
            except Exception as e:
                print(f"[Watcher] 중지 중 오류: {e}")
            self._running = False
            print("[Watcher] 감시 중지됨")
    
    def is_running(self):
        """실제 Observer 스레드 상태 확인"""
        # _running 플래그와 실제 스레드 상태 모두 확인
        if self._running and self.observer.is_alive():
            return True
        elif self._running and not self.observer.is_alive():
            # 스레드가 죽었으면 플래그 리셋
            print("[Watcher] ⚠️ Observer 스레드가 예기치 않게 종료됨")
            self._running = False
            return False
        return False
    
    def reload_rules(self):
        """규칙 다시 로드"""
        self.rule_engine.load_rules()
        print("[Watcher] 규칙 리로드됨")
    
    def restart(self):
        """감시 재시작"""
        self.stop()
        # 새 Observer 인스턴스 생성 (재사용 불가)
        self.observer = Observer()
        self.start()


# 전역 인스턴스 (Flask 앱에서 사용)
_watcher_instance = None


def get_watcher() -> FileWatcher:
    """싱글턴 Watcher 인스턴스 반환"""
    global _watcher_instance
    if _watcher_instance is None:
        _watcher_instance = FileWatcher()
    return _watcher_instance


if __name__ == "__main__":
    watcher = FileWatcher()
    watcher.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        watcher.stop()
        print("\n[Watcher] 프로그램 종료")
