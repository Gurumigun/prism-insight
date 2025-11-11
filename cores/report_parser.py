"""
보고서 파싱 모듈
생성된 마크다운 보고서에서 핵심 투자 정보를 추출합니다.
"""

import re
import json
from typing import Dict, List, Optional, Any
from pathlib import Path


class ReportParser:
    """보고서 파싱 클래스"""

    def __init__(self, report_content: str):
        """
        Args:
            report_content: 마크다운 형식의 보고서 전문
        """
        self.content = report_content
        self.lines = report_content.split('\n')

    def extract_investment_opinion(self) -> Optional[str]:
        """투자 의견 추출 (매수/중립/보유/매도)"""
        patterns = [
            r'투자\s*의견[:\s]*[*]*([가-힣\s]+)[*]*',
            r'투자\s*등급[:\s]*[*]*([가-힣\s]+)[*]*',
            r'투자\s*전략[:\s]*[*]*([가-힣]+)',
            r'종합\s*의견[:\s]*[*]*([가-힣]+)',
            r'(매수|적극\s*매수|중립|보유|매도|비중\s*확대|비중\s*축소)'
        ]

        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                opinion = match.group(1).strip()
                # 정규화
                if '매수' in opinion or '확대' in opinion:
                    return '매수'
                elif '매도' in opinion or '축소' in opinion:
                    return '매도'
                elif '중립' in opinion or '보유' in opinion:
                    return '중립'

        return '분석중'

    def extract_target_price(self) -> Optional[str]:
        """목표주가 추출"""
        patterns = [
            r'목표[주]*가[:\s]*[*]*([0-9,]+)\s*원',
            r'목표[주]*가[:\s]*[*]*([0-9,]+)',
            r'적정[주]*가[:\s]*[*]*([0-9,]+)',
            r'타겟[주]*가[:\s]*[*]*([0-9,]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                price = match.group(1).replace(',', '')
                return f"{int(price):,}원"

        return None

    def extract_current_price(self) -> Optional[str]:
        """현재가 추출"""
        patterns = [
            r'현재[주]*가[:\s]*[*]*([0-9,]+)\s*원',
            r'종가[:\s]*[*]*([0-9,]+)\s*원',
            r'주가[:\s]*[*]*([0-9,]+)\s*원'
        ]

        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                price = match.group(1).replace(',', '')
                return f"{int(price):,}원"

        return None

    def extract_buy_zones(self) -> List[Dict[str, str]]:
        """매수 가격대 추출"""
        buy_zones = []
        patterns = [
            r'매수[가격]*[대구간]*[:\s]*[*]*([0-9,~\-\s]+)\s*원',
            r'([0-9,]+)\s*[-~]\s*([0-9,]+)\s*원\s*구간',
            r'진입[가격]*[:\s]*[*]*([0-9,~\-\s]+)',
        ]

        for pattern in patterns:
            matches = re.finditer(pattern, self.content, re.IGNORECASE)
            for match in matches:
                zone_text = match.group(1)
                # ~ 또는 - 로 구간 나누기
                if '~' in zone_text or '-' in zone_text:
                    parts = re.split(r'[~\-]', zone_text)
                    if len(parts) == 2:
                        low = parts[0].strip().replace(',', '')
                        high = parts[1].strip().replace(',', '')
                        if low.isdigit() and high.isdigit():
                            buy_zones.append({
                                'low': f"{int(low):,}원",
                                'high': f"{int(high):,}원"
                            })

        # 중복 제거
        unique_zones = []
        seen = set()
        for zone in buy_zones:
            key = f"{zone['low']}-{zone['high']}"
            if key not in seen:
                seen.add(key)
                unique_zones.append(zone)

        return unique_zones[:3]  # 최대 3개

    def extract_stop_loss(self) -> Optional[str]:
        """손절가 추출"""
        patterns = [
            r'손절[가격]*[:\s]*[*]*([0-9,]+)\s*원',
            r'손실[제한]*[가격]*[:\s]*[*]*([0-9,]+)',
            r'스톱[로스]*[:\s]*[*]*([0-9,]+)'
        ]

        for pattern in patterns:
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                price = match.group(1).replace(',', '')
                return f"{int(price):,}원"

        return None

    def extract_risk_level(self) -> str:
        """리스크 레벨 추출"""
        # 키워드 기반 리스크 평가
        high_risk_keywords = ['높은 리스크', '고위험', '변동성 확대', '불확실성 증가']
        medium_risk_keywords = ['중간 리스크', '보통 수준', '적정 리스크']
        low_risk_keywords = ['낮은 리스크', '안정적', '저위험']

        content_lower = self.content.lower()

        for keyword in high_risk_keywords:
            if keyword in content_lower:
                return '높음'

        for keyword in medium_risk_keywords:
            if keyword in content_lower:
                return '중간'

        for keyword in low_risk_keywords:
            if keyword in content_lower:
                return '낮음'

        # 리스크 섹션에서 평가
        risk_section = self._extract_section('리스크')
        if risk_section:
            risk_items = len(re.findall(r'[-*]\s', risk_section))
            if risk_items >= 5:
                return '높음'
            elif risk_items >= 3:
                return '중간'
            else:
                return '낮음'

        return '중간'

    def extract_key_points(self) -> List[str]:
        """핵심 투자 포인트 추출"""
        key_points = []

        # 핵심 투자 포인트 섹션 찾기
        in_key_section = False
        for line in self.lines:
            if '핵심' in line and ('투자' in line or '포인트' in line):
                in_key_section = True
                continue

            if in_key_section:
                # 새로운 섹션 시작시 종료
                if line.startswith('#'):
                    break

                # 불릿 포인트 추출
                match = re.match(r'^[-*]\s+(.+)$', line.strip())
                if match:
                    point = match.group(1).strip()
                    if len(point) > 10:  # 최소 길이 필터
                        key_points.append(point)

        return key_points[:5]  # 최대 5개

    def extract_scenarios(self) -> Dict[str, Dict[str, Any]]:
        """투자 시나리오 추출 (단기/중기/장기)"""
        scenarios = {}

        # 시나리오 섹션 찾기
        scenario_types = ['단기', '중기', '장기']

        for scenario_type in scenario_types:
            scenario_data = {
                'optimistic': None,
                'base': None,
                'pessimistic': None
            }

            # 각 시나리오 타입별 패턴 찾기
            pattern = f'{scenario_type}.*?시나리오'
            section_start = re.search(pattern, self.content, re.IGNORECASE)

            if section_start:
                # 해당 섹션 추출 (다음 섹션 전까지)
                start_pos = section_start.end()
                end_pos = self.content.find('\n##', start_pos)
                if end_pos == -1:
                    end_pos = len(self.content)

                section_text = self.content[start_pos:end_pos]

                # 낙관/기본/비관 시나리오 추출
                optimistic_match = re.search(r'낙관[적]*[:\s]*[*]*([0-9,]+)\s*원', section_text)
                base_match = re.search(r'기본[:\s]*[*]*([0-9,]+)\s*원', section_text)
                pessimistic_match = re.search(r'비관[적]*[:\s]*[*]*([0-9,]+)\s*원', section_text)

                if optimistic_match:
                    scenario_data['optimistic'] = f"{int(optimistic_match.group(1).replace(',', '')):,}원"
                if base_match:
                    scenario_data['base'] = f"{int(base_match.group(1).replace(',', '')):,}원"
                if pessimistic_match:
                    scenario_data['pessimistic'] = f"{int(pessimistic_match.group(1).replace(',', '')):,}원"

                scenarios[scenario_type] = scenario_data

        return scenarios

    def extract_technical_indicators(self) -> Dict[str, str]:
        """주요 기술적 지표 추출"""
        indicators = {}

        patterns = {
            'rsi': r'RSI[:\s]*[*]*([0-9.]+)',
            'macd': r'MACD[:\s]*[*]*([가-힣\s]+)',
            'moving_average': r'이동평균[:\s]*[*]*([가-힣\s]+)',
            'volume': r'거래량[:\s]*[*]*([가-힣\s0-9%]+)'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                indicators[key] = match.group(1).strip()

        return indicators

    def extract_financial_metrics(self) -> Dict[str, str]:
        """재무 지표 추출"""
        metrics = {}

        patterns = {
            'per': r'PER[:\s]*[*]*([0-9.]+)',
            'pbr': r'PBR[:\s]*[*]*([0-9.]+)',
            'roe': r'ROE[:\s]*[*]*([0-9.]+)%?',
            'debt_ratio': r'부채비율[:\s]*[*]*([0-9.]+)%?'
        }

        for key, pattern in patterns.items():
            match = re.search(pattern, self.content, re.IGNORECASE)
            if match:
                metrics[key] = match.group(1).strip()

        return metrics

    def _extract_section(self, section_name: str) -> str:
        """특정 섹션 내용 추출"""
        pattern = f'##\\s*{section_name}'
        match = re.search(pattern, self.content, re.IGNORECASE)

        if match:
            start_pos = match.end()
            # 다음 섹션 전까지
            end_pos = self.content.find('\n##', start_pos)
            if end_pos == -1:
                end_pos = len(self.content)

            return self.content[start_pos:end_pos]

        return ''

    def generate_summary(self) -> Dict[str, Any]:
        """전체 요약 정보 생성"""
        summary = {
            'investment_opinion': self.extract_investment_opinion(),
            'target_price': self.extract_target_price(),
            'current_price': self.extract_current_price(),
            'buy_zones': self.extract_buy_zones(),
            'stop_loss': self.extract_stop_loss(),
            'risk_level': self.extract_risk_level(),
            'key_points': self.extract_key_points(),
            'scenarios': self.extract_scenarios(),
            'technical_indicators': self.extract_technical_indicators(),
            'financial_metrics': self.extract_financial_metrics()
        }

        return summary


def parse_report_file(report_path: str) -> Dict[str, Any]:
    """
    보고서 파일에서 요약 정보 추출

    Args:
        report_path: 보고서 파일 경로

    Returns:
        요약 정보 딕셔너리
    """
    report_file = Path(report_path)

    if not report_file.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")

    with open(report_file, 'r', encoding='utf-8') as f:
        content = f.read()

    parser = ReportParser(content)
    summary = parser.generate_summary()

    return summary


def save_summary_json(summary: Dict[str, Any], output_path: str):
    """
    요약 정보를 JSON 파일로 저장

    Args:
        summary: 요약 정보 딕셔너리
        output_path: 저장할 JSON 파일 경로
    """
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


if __name__ == '__main__':
    # 테스트 코드
    import sys

    if len(sys.argv) > 1:
        report_path = sys.argv[1]
        try:
            summary = parse_report_file(report_path)
            print(json.dumps(summary, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        print("Usage: python report_parser.py <report_file_path>")
        sys.exit(1)
