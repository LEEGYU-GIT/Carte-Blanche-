"""
Carte Blanche - Tool Registry
재사용 가능한 도구 함수들의 집합
"""
import os
import subprocess
import time
from datetime import datetime
from typing import Any, Callable

# 선택적 GUI 라이브러리
try:
    import pyautogui
    import pyperclip
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False


class ToolRegistry:
    """도구 함수를 등록하고 실행하는 레지스트리"""
    
    def __init__(self):
        self._tools: dict[str, Callable] = {}
        self._register_default_tools()
    
    def register(self, name: str, func: Callable, description: str = ""):
        """새 도구 등록"""
        self._tools[name] = {
            "func": func,
            "description": description
        }
        print(f"[ToolRegistry] 도구 등록: {name}")
    
    def get(self, name: str) -> Callable:
        """도구 함수 반환"""
        if name not in self._tools:
            raise ValueError(f"등록되지 않은 도구: {name}")
        return self._tools[name]["func"]
    
    def list_tools(self) -> list:
        """등록된 모든 도구 목록"""
        return [
            {"name": name, "description": info["description"]}
            for name, info in self._tools.items()
        ]
    
    def execute(self, name: str, **kwargs) -> Any:
        """도구 실행"""
        func = self.get(name)
        return func(**kwargs)
    
    def _register_default_tools(self):
        """기본 도구들 등록"""
        self.register("read_file", read_file, "파일 내용을 읽어서 반환")
        self.register("save_to_output", save_to_output, "내용을 파일로 저장")
        self.register("open_notepad", open_notepad, "메모장에서 파일 열기")
        self.register("open_excel", open_excel, "엑셀에서 파일 열기")
        self.register("open_browser", open_browser, "브라우저에서 URL 열기")
        self.register("copy_file", copy_file, "파일 복사")
        self.register("move_file", move_file, "파일 이동")
        self.register("summarize_text", summarize_text, "텍스트 요약 정보 생성")


# ==================== 도구 함수들 ====================

def read_file(path: str, encoding: str = "utf-8") -> dict:
    """
    파일 내용을 읽어서 반환
    
    Args:
        path: 파일 경로
        encoding: 인코딩 (기본: utf-8)
    
    Returns:
        {"success": bool, "result": str or error}
    """
    try:
        with open(path, 'r', encoding=encoding) as f:
            content = f.read()
        return {
            "success": True,
            "result": content,
            "file_path": path,
            "size": len(content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def save_to_output(content: str, output_dir: str, prefix: str = "", 
                   filename: str = None, encoding: str = "utf-8") -> dict:
    """
    내용을 파일로 저장
    
    Args:
        content: 저장할 내용
        output_dir: 출력 디렉토리
        prefix: 파일명 접두사
        filename: 파일명 (없으면 자동 생성)
        encoding: 인코딩
    
    Returns:
        {"success": bool, "result": 저장된 파일 경로}
    """
    try:
        os.makedirs(output_dir, exist_ok=True)
        
        if filename is None:
            filename = f"{prefix}{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        else:
            filename = f"{prefix}{filename}"
        
        output_path = os.path.join(output_dir, filename)
        
        with open(output_path, 'w', encoding=encoding) as f:
            f.write(content)
        
        return {
            "success": True,
            "result": output_path,
            "size": len(content)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def open_notepad(file_path: str = None, text: str = None) -> dict:
    """
    메모장에서 파일 열기 또는 텍스트 표시
    
    Args:
        file_path: 열 파일 경로
        text: 직접 작성할 텍스트 (file_path가 없을 때)
    
    Returns:
        {"success": bool, "result": process_id}
    """
    try:
        if file_path and os.path.exists(file_path):
            # 기존 파일 열기
            process = subprocess.Popen(['notepad.exe', file_path])
        elif text:
            # 임시 파일에 저장 후 열기
            temp_path = os.path.join(os.environ.get('TEMP', '.'), 
                                     f"carte_blanche_{datetime.now().strftime('%H%M%S')}.txt")
            with open(temp_path, 'w', encoding='utf-8') as f:
                f.write(text)
            process = subprocess.Popen(['notepad.exe', temp_path])
        else:
            # 빈 메모장 열기
            process = subprocess.Popen(['notepad.exe'])
        
        return {
            "success": True,
            "result": process.pid,
            "message": "메모장 실행됨"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def open_excel(file_path: str) -> dict:
    """
    엑셀에서 파일 열기
    
    Args:
        file_path: 열 파일 경로
    
    Returns:
        {"success": bool, "result": process_id}
    """
    try:
        # Windows에서 기본 연결 프로그램으로 열기
        os.startfile(file_path)
        return {
            "success": True,
            "result": file_path,
            "message": "엑셀 파일 열림"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def open_browser(url: str) -> dict:
    """
    기본 브라우저에서 URL 열기
    
    Args:
        url: 열 URL
    
    Returns:
        {"success": bool, "result": url}
    """
    try:
        import webbrowser
        webbrowser.open(url)
        return {
            "success": True,
            "result": url,
            "message": "브라우저에서 URL 열림"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def copy_file(source: str, destination: str) -> dict:
    """
    파일 복사
    
    Args:
        source: 원본 파일 경로
        destination: 대상 경로 (파일명 또는 디렉토리)
    
    Returns:
        {"success": bool, "result": 복사된 파일 경로}
    """
    try:
        import shutil
        
        # destination이 디렉토리면 같은 이름으로 복사
        if os.path.isdir(destination):
            dest_path = os.path.join(destination, os.path.basename(source))
        else:
            dest_path = destination
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        shutil.copy2(source, dest_path)
        return {
            "success": True,
            "result": dest_path,
            "message": f"파일 복사됨: {source} -> {dest_path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def move_file(source: str, destination: str) -> dict:
    """
    파일 이동
    
    Args:
        source: 원본 파일 경로
        destination: 대상 경로
    
    Returns:
        {"success": bool, "result": 이동된 파일 경로}
    """
    try:
        import shutil
        
        if os.path.isdir(destination):
            dest_path = os.path.join(destination, os.path.basename(source))
        else:
            dest_path = destination
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        shutil.move(source, dest_path)
        return {
            "success": True,
            "result": dest_path,
            "message": f"파일 이동됨: {source} -> {dest_path}"
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


def summarize_text(content: str) -> dict:
    """
    텍스트 요약 정보 생성
    
    Args:
        content: 요약할 텍스트
    
    Returns:
        {"success": bool, "result": 요약 정보 문자열}
    """
    try:
        lines = content.split('\n')
        words = content.split()
        
        summary = f"""=== 텍스트 요약 ===
총 줄 수: {len(lines)}
총 단어 수: {len(words)}
총 문자 수: {len(content)}
처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

=== 미리보기 (처음 200자) ===
{content[:200]}{'...' if len(content) > 200 else ''}
"""
        return {
            "success": True,
            "result": summary,
            "stats": {
                "lines": len(lines),
                "words": len(words),
                "chars": len(content)
            }
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


# 전역 레지스트리 인스턴스
tool_registry = ToolRegistry()


# ==================== 도구별 인자 템플릿 (비개발자용) ====================

TOOL_TEMPLATES = {
    "read_file": {
        "label": "📖 파일 읽기",
        "description": "파일 내용을 읽어옵니다",
        "args": [
            {
                "key": "path",
                "label": "파일 경로",
                "type": "select",
                "options": [
                    {"value": "{trigger.file_path}", "label": "📁 트리거된 파일 (자동)"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": True,
                "hint": "어떤 파일을 읽을지 선택하세요",
                "ui_type": "file_picker"
            }
        ]
    },
    "save_to_output": {
        "label": "💾 파일 저장",
        "description": "내용을 새 파일로 저장합니다",
        "args": [
            {
                "key": "content",
                "label": "저장할 내용",
                "type": "select",
                "options": [
                    {"value": "{step1.result}", "label": "📄 1단계 결과"},
                    {"value": "{step2.result}", "label": "📄 2단계 결과"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": True,
                "hint": "어떤 내용을 저장할지 선택하세요"
            },
            {
                "key": "output_dir",
                "label": "저장 폴더",
                "type": "text",
                "default": "C:/Users/내이름/Documents/Output",
                "required": True,
                "hint": "파일을 저장할 폴더 경로",
                "ui_type": "folder_picker"
            },
            {
                "key": "prefix",
                "label": "파일명 앞에 붙일 말",
                "type": "text",
                "default": "processed_",
                "required": False,
                "hint": "예: processed_ → processed_파일명.txt"
            }
        ]
    },
    "open_notepad": {
        "label": "📝 메모장 열기",
        "description": "메모장에서 파일을 엽니다",
        "args": [
            {
                "key": "file_path",
                "label": "열 파일",
                "type": "select",
                "options": [
                    {"value": "{trigger.file_path}", "label": "📁 트리거된 파일"},
                    {"value": "{step1.result}", "label": "📄 1단계 결과 파일"},
                    {"value": "{step2.result}", "label": "📄 2단계 결과 파일"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": False,
                "hint": "메모장에서 열 파일을 선택하세요",
                "ui_type": "file_picker"
            }
        ]
    },
    "open_excel": {
        "label": "📊 엑셀 열기",
        "description": "엑셀에서 파일을 엽니다",
        "args": [
            {
                "key": "file_path",
                "label": "열 파일",
                "type": "select",
                "options": [
                    {"value": "{trigger.file_path}", "label": "📁 트리거된 파일"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": True,
                "hint": "엑셀에서 열 파일을 선택하세요",
                "ui_type": "file_picker"
            }
        ]
    },
    "open_browser": {
        "label": "🌐 브라우저 열기",
        "description": "웹 브라우저에서 URL을 엽니다",
        "args": [
            {
                "key": "url",
                "label": "웹 주소",
                "type": "text",
                "default": "https://google.com",
                "required": True,
                "hint": "열고 싶은 웹사이트 주소"
            }
        ]
    },
    "copy_file": {
        "label": "📋 파일 복사",
        "description": "파일을 다른 위치로 복사합니다",
        "args": [
            {
                "key": "source",
                "label": "원본 파일",
                "type": "select",
                "options": [
                    {"value": "{trigger.file_path}", "label": "📁 트리거된 파일"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": True,
                "hint": "복사할 원본 파일"
            },
            {
                "key": "destination",
                "label": "복사할 위치",
                "type": "text",
                "default": "C:/Users/내이름/Documents/Backup",
                "required": True,
                "hint": "파일을 복사할 폴더 경로",
                "ui_type": "folder_picker"
            }
        ]
    },
    "move_file": {
        "label": "📦 파일 이동",
        "description": "파일을 다른 위치로 이동합니다",
        "args": [
            {
                "key": "source",
                "label": "원본 파일",
                "type": "select",
                "options": [
                    {"value": "{trigger.file_path}", "label": "📁 트리거된 파일"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": True,
                "hint": "이동할 원본 파일"
            },
            {
                "key": "destination",
                "label": "이동할 위치",
                "type": "text",
                "default": "C:/Users/내이름/Documents/Archive",
                "required": True,
                "hint": "파일을 이동할 폴더 경로",
                "ui_type": "folder_picker"
            }
        ]
    },
    "summarize_text": {
        "label": "📄 텍스트 요약",
        "description": "텍스트의 통계 정보를 생성합니다",
        "args": [
            {
                "key": "content",
                "label": "요약할 내용",
                "type": "select",
                "options": [
                    {"value": "{step1.result}", "label": "📄 1단계 결과"},
                    {"value": "{trigger.file_path}", "label": "📁 트리거된 파일 내용"},
                    {"value": "", "label": "✏️ 직접 입력"}
                ],
                "required": True,
                "hint": "요약할 텍스트를 선택하세요"
            }
        ]
    }
}


def get_tool_templates():
    """도구 템플릿 목록 반환 (API용)"""
    return TOOL_TEMPLATES

