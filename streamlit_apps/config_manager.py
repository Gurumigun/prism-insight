"""
모델 설정 관리 모듈
"""
import json
import os
from typing import Dict, Any
from pathlib import Path


class ConfigManager:
    """모델 설정을 관리하는 클래스"""

    DEFAULT_CONFIG = {
        "gpt_model": "gpt-4o",  # gpt-4o, gpt-4.1, gpt-5
        "claude_model": "claude-sonnet-4-5-20250929",  # Claude 모델
        "openai_api_key": "",  # 환경변수에서 읽음
        "anthropic_api_key": "",  # 환경변수에서 읽음
    }

    def __init__(self, config_path: str = "streamlit_apps/config.json"):
        """
        Args:
            config_path: 설정 파일 경로
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()

    def _load_config(self) -> Dict[str, Any]:
        """설정 파일 로드"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                # 기본값과 병합
                return {**self.DEFAULT_CONFIG, **config}
            except Exception as e:
                print(f"설정 파일 로드 실패: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            return self.DEFAULT_CONFIG.copy()

    def save_config(self) -> bool:
        """설정 파일 저장"""
        try:
            # 디렉토리 생성
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"설정 파일 저장 실패: {e}")
            return False

    def get(self, key: str, default: Any = None) -> Any:
        """설정 값 가져오기"""
        return self.config.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """설정 값 변경"""
        self.config[key] = value

    def get_gpt_model(self) -> str:
        """GPT 모델 가져오기"""
        return self.config.get("gpt_model", "gpt-4o")

    def set_gpt_model(self, model: str) -> None:
        """GPT 모델 설정"""
        self.config["gpt_model"] = model

    def get_claude_model(self) -> str:
        """Claude 모델 가져오기"""
        return self.config.get("claude_model", "claude-sonnet-4-5-20250929")

    def set_claude_model(self, model: str) -> None:
        """Claude 모델 설정"""
        self.config["claude_model"] = model

    def get_all(self) -> Dict[str, Any]:
        """전체 설정 가져오기"""
        return self.config.copy()

    def reset_to_default(self) -> None:
        """기본값으로 초기화"""
        self.config = self.DEFAULT_CONFIG.copy()
