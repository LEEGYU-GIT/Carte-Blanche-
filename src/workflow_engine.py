"""
Carte Blanche - Workflow Engine (Dynamic Dispatcher)
JSON 워크플로우 설정을 읽고 동적으로 도구를 실행하는 엔진
"""
import os
import re
import json
from typing import Any
from datetime import datetime

from src.tools import tool_registry


class WorkflowEngine:
    """워크플로우를 로드하고 실행하는 동적 디스패처"""
    
    def __init__(self, workflow_path: str = None):
        self.workflow_path = workflow_path
        self.workflow = None
        self.context = {}  # 각 단계 결과를 저장하는 컨텍스트
        
        if workflow_path:
            self.load_workflow(workflow_path)
    
    def load_workflow(self, path: str) -> dict:
        """워크플로우 JSON 로드"""
        with open(path, 'r', encoding='utf-8') as f:
            self.workflow = json.load(f)
        print(f"[WorkflowEngine] 워크플로우 로드: {self.workflow.get('workflow_name', 'Unknown')}")
        return self.workflow
    
    def execute(self, trigger_context: dict = None) -> dict:
        """
        워크플로우 전체 실행
        
        Args:
            trigger_context: 트리거에서 전달받은 초기 컨텍스트
                            예: {"trigger.file_path": "/path/to/file.txt"}
        
        Returns:
            {"success": bool, "results": list, "context": dict}
        """
        if not self.workflow:
            return {"success": False, "error": "워크플로우가 로드되지 않음"}
        
        # 컨텍스트 초기화
        self.context = trigger_context or {}
        self.context["workflow.name"] = self.workflow.get("workflow_name", "")
        self.context["workflow.timestamp"] = datetime.now().isoformat()
        
        actions = self.workflow.get("actions", [])
        results = []
        
        print(f"\n[WorkflowEngine] === 워크플로우 실행 시작 ===")
        print(f"[WorkflowEngine] 총 {len(actions)}개 액션")
        
        for i, action in enumerate(actions, 1):
            step_id = action.get("id", f"step{i}")
            tool_name = action.get("tool")
            description = action.get("description", "")
            args = action.get("args", {})
            
            print(f"\n[WorkflowEngine] [{i}/{len(actions)}] {step_id}: {tool_name}")
            if description:
                print(f"[WorkflowEngine]    └─ {description}")
            
            # 인자에서 변수 치환
            resolved_args = self._resolve_variables(args)
            
            try:
                # 도구 실행
                result = tool_registry.execute(tool_name, **resolved_args)
                
                # 결과를 컨텍스트에 저장
                self.context[f"{step_id}.result"] = result.get("result", "")
                self.context[f"{step_id}.success"] = result.get("success", False)
                
                results.append({
                    "step_id": step_id,
                    "tool": tool_name,
                    "success": result.get("success", False),
                    "result": result
                })
                
                if result.get("success"):
                    print(f"[WorkflowEngine]    ✅ 성공")
                else:
                    print(f"[WorkflowEngine]    ❌ 실패: {result.get('error', 'Unknown error')}")
                    # 실패 시 워크플로우 중단 (선택적)
                    if action.get("stop_on_fail", True):
                        break
                        
            except Exception as e:
                error_msg = str(e)
                print(f"[WorkflowEngine]    ❌ 예외: {error_msg}")
                results.append({
                    "step_id": step_id,
                    "tool": tool_name,
                    "success": False,
                    "error": error_msg
                })
                break
        
        success_count = sum(1 for r in results if r.get("success"))
        print(f"\n[WorkflowEngine] === 워크플로우 완료 ===")
        print(f"[WorkflowEngine] 성공: {success_count}/{len(results)}")
        
        return {
            "success": all(r.get("success") for r in results),
            "results": results,
            "context": self.context
        }
    
    def _resolve_variables(self, args: dict) -> dict:
        """
        인자에서 {variable} 형태의 변수를 실제 값으로 치환
        
        예: {"content": "{step1.result}"} -> {"content": "실제 파일 내용"}
        """
        resolved = {}
        
        for key, value in args.items():
            if isinstance(value, str):
                # {variable} 패턴 찾기
                pattern = r'\{([^}]+)\}'
                matches = re.findall(pattern, value)
                
                resolved_value = value
                for match in matches:
                    if match in self.context:
                        context_value = self.context[match]
                        # 전체 값이 변수 하나면 타입 유지, 아니면 문자열로 치환
                        if value == f"{{{match}}}":
                            resolved_value = context_value
                        else:
                            resolved_value = resolved_value.replace(f"{{{match}}}", str(context_value))
                    else:
                        print(f"[WorkflowEngine]    ⚠️ 변수 '{match}' 를 찾을 수 없음")
                
                resolved[key] = resolved_value
            elif isinstance(value, dict):
                # 중첩 딕셔너리 처리
                resolved[key] = self._resolve_variables(value)
            else:
                resolved[key] = value
        
        return resolved
    
    def get_trigger_config(self) -> dict:
        """트리거 설정 반환"""
        if self.workflow:
            return self.workflow.get("trigger", {})
        return {}
    
    def get_action_count(self) -> int:
        """액션 개수 반환"""
        if self.workflow:
            return len(self.workflow.get("actions", []))
        return 0


def run_workflow_for_file(workflow_path: str, file_path: str, output_path: str = None) -> dict:
    """
    특정 파일에 대해 워크플로우 실행 (헬퍼 함수)
    
    Args:
        workflow_path: 워크플로우 JSON 경로
        file_path: 트리거된 파일 경로
        output_path: 결과물이 저장될 기본 폴더 경로
    
    Returns:
        워크플로우 실행 결과
    """
    engine = WorkflowEngine(workflow_path)
    
    # 트리거 컨텍스트 설정
    trigger_context = {
        "trigger.file_path": file_path,
        "trigger.file_name": os.path.basename(file_path),
        "trigger.file_dir": os.path.dirname(file_path),
        "trigger.output_path": output_path or os.path.dirname(file_path),
        "trigger.timestamp": datetime.now().isoformat()
    }
    
    return engine.execute(trigger_context)


# 테스트 코드
if __name__ == "__main__":
    import sys
    
    # 프로젝트 루트 설정
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sys.path.insert(0, PROJECT_ROOT)
    
    # 테스트 워크플로우 실행
    workflow_path = os.path.join(PROJECT_ROOT, "config", "workflow.json")
    test_file = os.path.join(PROJECT_ROOT, "config", "rules.json")  # 테스트용 파일
    
    if os.path.exists(workflow_path):
        result = run_workflow_for_file(workflow_path, test_file)
        print(f"\n최종 결과: {result['success']}")
    else:
        print(f"워크플로우 파일이 없습니다: {workflow_path}")
