"""
Carte Blanche - Rule Engine
트리거-액션 매핑 및 규칙 관리
"""
import json
import os
from typing import List, Dict, Optional


class RuleEngine:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self.rules: List[Dict] = []
        self.load_rules()
    
    def load_rules(self) -> None:
        """설정 파일에서 규칙을 로드합니다."""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.rules = config.get('rules', [])
                print(f"[Engine] {len(self.rules)}개의 규칙 로드됨")
            else:
                print(f"[Engine] 설정 파일 없음: {self.config_path}")
                self.rules = []
        except Exception as e:
            print(f"[Engine] 규칙 로드 실패: {e}")
            self.rules = []
    
    def save_rules(self) -> bool:
        """규칙을 설정 파일에 저장합니다."""
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump({"rules": self.rules}, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"[Engine] 규칙 저장 실패: {e}")
            return False
    
    def get_all_rules(self) -> List[Dict]:
        """모든 규칙을 반환합니다."""
        return self.rules
    
    def get_rule(self, rule_id: str) -> Optional[Dict]:
        """특정 ID의 규칙을 반환합니다."""
        for rule in self.rules:
            if rule.get('id') == rule_id:
                return rule
        return None
    
    def add_rule(self, rule: Dict) -> bool:
        """새 규칙을 추가합니다."""
        if not rule.get('id'):
            rule['id'] = f"rule_{len(self.rules) + 1:03d}"
        self.rules.append(rule)
        return self.save_rules()
    
    def update_rule(self, rule_id: str, updated_rule: Dict) -> bool:
        """기존 규칙을 업데이트합니다."""
        for i, rule in enumerate(self.rules):
            if rule.get('id') == rule_id:
                updated_rule['id'] = rule_id
                self.rules[i] = updated_rule
                return self.save_rules()
        return False
    
    def delete_rule(self, rule_id: str) -> bool:
        """규칙을 삭제합니다."""
        for i, rule in enumerate(self.rules):
            if rule.get('id') == rule_id:
                self.rules.pop(i)
                return self.save_rules()
        return False
    
    def get_watched_paths(self) -> List[str]:
        """감시해야 할 모든 경로를 반환합니다."""
        paths = set()
        for rule in self.rules:
            if rule.get('enabled', True):
                trigger = rule.get('trigger', {})
                path = trigger.get('path')
                if path:
                    paths.add(path)
        return list(paths)
    
    def find_matching_rules(self, file_path: str, event_type: str = "file_created") -> List[Dict]:
        """
        파일 경로와 이벤트 타입에 매칭되는 규칙들을 찾습니다.
        """
        matching = []
        file_ext = os.path.splitext(file_path)[1].lower()
        file_dir = os.path.dirname(file_path).replace('\\', '/')
        
        for rule in self.rules:
            if not rule.get('enabled', True):
                continue
                
            trigger = rule.get('trigger', {})
            
            # 이벤트 타입 확인
            if trigger.get('type') != event_type:
                continue
            
            # 경로 확인
            rule_path = trigger.get('path', '').replace('\\', '/')
            if not file_dir.startswith(rule_path):
                continue
            
            # 확장자 확인
            extensions = trigger.get('extensions', [])
            if extensions and file_ext not in extensions:
                continue
            
            matching.append(rule)
        
        return matching
