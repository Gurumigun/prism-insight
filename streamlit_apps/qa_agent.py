"""
Claude Sonnet 4.5 기반 Q&A 에이전트

⚠️ 주의: 기존 코드를 수정하지 않는 새로운 모듈입니다.
"""

import os
from typing import List, Dict


class QAAgent:
    """Claude 기반 Q&A 에이전트"""

    def __init__(self):
        """초기화"""
        try:
            import anthropic
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")

            self.client = anthropic.Anthropic(api_key=api_key)
            self.model = "claude-sonnet-4-5-20250929"
            self.conversation_history: List[Dict] = []

        except ImportError:
            raise ImportError("anthropic library not installed. Run: pip install anthropic")

    async def ask(
        self,
        question: str,
        analysis_context: str
    ) -> str:
        """
        질문에 대한 답변 생성

        Args:
            question: 사용자 질문
            analysis_context: 분석 결과 (컨텍스트)

        Returns:
            AI 답변
        """

        # 시스템 프롬프트
        system_prompt = f"""당신은 주식 투자 전문가입니다.

다음은 AI가 분석한 주식 보고서입니다:

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{analysis_context[:10000]}  # 최대 10,000자로 제한
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

사용자의 질문에 대해 이 보고서를 기반으로 답변해주세요.

답변 가이드라인:
1. 간결하고 명확하게 작성 (300자 이내)
2. 근거를 명시
3. 구체적인 수치 포함
4. Markdown 포맷 사용
5. 투자 권유가 아닌 정보 제공임을 명시
"""

        # 대화 히스토리에 추가
        self.conversation_history.append({
            "role": "user",
            "content": question
        })

        try:
            # API 호출
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt,
                messages=self.conversation_history
            )

            answer = response.content[0].text

            # 답변을 히스토리에 추가
            self.conversation_history.append({
                "role": "assistant",
                "content": answer
            })

            return answer

        except Exception as e:
            error_msg = f"Claude API 호출 실패: {str(e)}"
            return error_msg

    def reset(self):
        """대화 히스토리 초기화"""
        self.conversation_history = []
