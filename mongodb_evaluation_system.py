"""
범용 MongoDB 분석 자동 평가 시스템
Evidently 라이브러리를 활용한 4개 핵심 지표 자동 산출 및 Pass/Fail 판정

참고한 Evidently 코드:
1. evidently.test_suite.TestSuite - 커스텀 테스트 실행 프레임워크
2. evidently.tests.base_test.Test - 커스텀 테스트 구현을 위한 베이스 클래스
3. evidently.metrics.base_metric.Metric - 커스텀 메트릭 구현을 위한 베이스 클래스
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Tuple
from dataclasses import dataclass
from datetime import datetime
import json
import traceback
import re


@dataclass
class UniversalAnalysisResult:
    """범용 분석 결과 구조"""
    analysis_query: str                    # 분석 질의
    mongodb_queries: List[str]             # 실행된 MongoDB 쿼리들
    calculation_results: Dict[str, Any]    # 계산 결과 (LLM 산출)
    execution_logs: List[Dict]             # 실행 로그
    direct_mongodb_results: Optional[Dict[str, Any]] = None  # MongoDB 직접 실행 결과
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()


@dataclass
class EvaluationMetrics:
    """4개 핵심 평가 지표"""
    semantic_error_rate: float      # 의미 오류 비율
    execution_success_rate: float   # 실행 성공률  
    empty_result_rate: float        # 무응답률
    accuracy_rate: float            # 정답 일치율
    overall_pass: bool              # 전체 Pass/Fail
    comparison_table: Optional[pd.DataFrame] = None  # 비교 테이블


@dataclass
class QueryComparisonResult:
    """쿼리 비교 결과"""
    query: str
    llm_result: Any
    mongodb_result: Any
    match: bool
    difference: Optional[str] = None


class UniversalMongoDBEvaluator:
    """
    범용 MongoDB 분석 평가기
    모든 종류의 MongoDB 분석에 적용 가능한 범용 평가 시스템
    """
    
    def __init__(self, thresholds: Optional[Dict[str, float]] = None):
        """
        Args:
            thresholds: 평가 임계값 설정
                - semantic_error: 의미 오류율 임계값 (기본 0.1)
                - execution_success: 실행 성공률 임계값 (기본 0.8)
                - empty_result: 무응답률 임계값 (기본 0.2)
                - accuracy: 정답 일치율 임계값 (기본 0.9)
        """
        self.thresholds = thresholds or {
            "semantic_error": 0.1,
            "execution_success": 0.8,
            "empty_result": 0.2,
            "accuracy": 0.9
        }
    
    def evaluate(self, analysis_result: UniversalAnalysisResult, 
                ground_truth: Optional[Dict[str, Any]] = None) -> EvaluationMetrics:
        """
        분석 결과 평가 실행
        
        Args:
            analysis_result: 분석 결과
            ground_truth: 정답 데이터 (선택적)
            
        Returns:
            EvaluationMetrics: 4개 핵심 지표 및 Pass/Fail 결과
        """
        
        # 비교 테이블 생성 (LLM vs MongoDB 직접 실행)
        comparison_table = self._create_comparison_table(analysis_result)
        
        # 1. 의미 오류율 계산
        semantic_error_rate = self._calculate_semantic_error_rate(analysis_result)
        
        # 2. 실행 성공률 계산
        execution_success_rate = self._calculate_execution_success_rate(analysis_result)
        
        # 3. 무응답률 계산
        empty_result_rate = self._calculate_empty_result_rate(analysis_result)
        
        # 4. 정답 일치율 계산
        accuracy_rate = self._calculate_accuracy_rate(analysis_result, ground_truth)
        
        # 5. 전체 Pass/Fail 판정
        overall_pass = self._determine_overall_pass(
            semantic_error_rate, execution_success_rate, 
            empty_result_rate, accuracy_rate
        )
        
        return EvaluationMetrics(
            semantic_error_rate=semantic_error_rate,
            execution_success_rate=execution_success_rate,
            empty_result_rate=empty_result_rate,
            accuracy_rate=accuracy_rate,
            overall_pass=overall_pass,
            comparison_table=comparison_table
        )
    
    def _create_comparison_table(self, analysis_result: UniversalAnalysisResult) -> pd.DataFrame:
        """LLM 계산 결과와 MongoDB 직접 실행 결과 비교 테이블 생성"""
        
        comparison_data = []
        
        # LLM 계산 결과와 MongoDB 직접 실행 결과 비교
        for metric_name, llm_value in analysis_result.calculation_results.items():
            mongodb_value = None
            match_status = "N/A"
            difference = ""
            
            # MongoDB 직접 실행 결과가 있는 경우
            if (analysis_result.direct_mongodb_results and 
                metric_name in analysis_result.direct_mongodb_results):
                
                mongodb_value = analysis_result.direct_mongodb_results[metric_name]
                
                # 값 비교
                if self._values_match(llm_value, mongodb_value):
                    match_status = "✅ 일치"
                    difference = "0"
                else:
                    match_status = "❌ 불일치"
                    difference = self._calculate_difference(llm_value, mongodb_value)
            
            comparison_data.append({
                "지표": metric_name,
                "LLM 계산 결과": self._format_value(llm_value),
                "MongoDB 직접 실행": self._format_value(mongodb_value),
                "일치 여부": match_status,
                "차이": difference
            })
        
        # MongoDB에만 있는 결과 추가
        if analysis_result.direct_mongodb_results:
            for metric_name, mongodb_value in analysis_result.direct_mongodb_results.items():
                if metric_name not in analysis_result.calculation_results:
                    comparison_data.append({
                        "지표": metric_name,
                        "LLM 계산 결과": "N/A",
                        "MongoDB 직접 실행": self._format_value(mongodb_value),
                        "일치 여부": "⚠️ LLM 누락",
                        "차이": "N/A"
                    })
        
        return pd.DataFrame(comparison_data)
    
    def _format_value(self, value: Any) -> str:
        """값을 표시용으로 포맷팅"""
        if value is None:
            return "N/A"
        elif isinstance(value, float):
            if value.is_integer():
                return str(int(value))
            else:
                return f"{value:.2f}"
        elif isinstance(value, (list, dict)):
            return f"{type(value).__name__}({len(value)})"
        else:
            return str(value)
    
    def _calculate_difference(self, llm_value: Any, mongodb_value: Any) -> str:
        """두 값의 차이 계산"""
        try:
            if isinstance(llm_value, (int, float)) and isinstance(mongodb_value, (int, float)):
                diff = abs(llm_value - mongodb_value)
                if mongodb_value != 0:
                    percentage = (diff / abs(mongodb_value)) * 100
                    return f"{diff:.2f} ({percentage:.1f}%)"
                else:
                    return f"{diff:.2f}"
            else:
                return "타입 불일치"
        except:
            return "계산 불가"
    
    def _calculate_semantic_error_rate(self, analysis_result: UniversalAnalysisResult) -> float:
        """의미 오류율 계산"""
        if not analysis_result.mongodb_queries:
            return 0.0
        
        semantic_errors = 0
        total_queries = len(analysis_result.mongodb_queries)
        
        for query in analysis_result.mongodb_queries:
            if self._has_semantic_error(query, analysis_result):
                semantic_errors += 1
        
        return semantic_errors / total_queries if total_queries > 0 else 0.0
    
    def _has_semantic_error(self, query: str, analysis_result: UniversalAnalysisResult) -> bool:
        """개별 쿼리의 의미 오류 검사"""
        
        # 논리적 모순 패턴 검사
        logical_error_patterns = [
            r"(\w+)\s*[!=<>]+\s*\1",           # 동일 필드 비교 (field != field)
            r"count.*==.*0.*AND.*exists",      # 존재하면서 개수가 0인 모순
            r">\s*9{8,}",                      # 비현실적인 큰 수
            r"\$match.*\{\s*\}",               # 빈 매치 조건
            r"\$group.*_id.*_id",              # 중복 그룹핑
        ]
        
        for pattern in logical_error_patterns:
            if re.search(pattern, query, re.IGNORECASE):
                return True
        
        # 실행 결과와 쿼리 의도 불일치 검사
        if self._check_result_query_mismatch(query, analysis_result):
            return True
        
        return False
    
    def _check_result_query_mismatch(self, query: str, analysis_result: UniversalAnalysisResult) -> bool:
        """쿼리 의도와 결과 불일치 검사"""
        
        # count 쿼리인데 결과가 음수
        if "count" in query.lower():
            for key, value in analysis_result.calculation_results.items():
                if isinstance(value, (int, float)) and value < 0:
                    return True
        
        # 비율 계산인데 100% 초과
        if any(word in analysis_result.analysis_query.lower() 
               for word in ["비율", "율", "percent", "rate"]):
            for key, value in analysis_result.calculation_results.items():
                if isinstance(value, (int, float)) and value > 100:
                    return True
        
        return False
    
    def _calculate_execution_success_rate(self, analysis_result: UniversalAnalysisResult) -> float:
        """실행 성공률 계산"""
        if not analysis_result.execution_logs:
            return 1.0  # 로그가 없으면 성공으로 간주
        
        successful_executions = 0
        total_executions = len(analysis_result.execution_logs)
        
        for log in analysis_result.execution_logs:
            # 실행 성공 여부 확인
            if log.get("status") == "success" or log.get("error") is None:
                successful_executions += 1
        
        return successful_executions / total_executions if total_executions > 0 else 1.0
    
    def _calculate_empty_result_rate(self, analysis_result: UniversalAnalysisResult) -> float:
        """무응답률 계산"""
        if not analysis_result.calculation_results:
            return 1.0  # 결과가 아예 없으면 100% 무응답
        
        empty_results = 0
        total_results = len(analysis_result.calculation_results)
        
        for key, value in analysis_result.calculation_results.items():
            if self._is_empty_or_invalid_result(value):
                empty_results += 1
        
        return empty_results / total_results if total_results > 0 else 1.0
    
    def _is_empty_or_invalid_result(self, value: Any) -> bool:
        """빈 결과 또는 무효 결과 검사"""
        
        # None 또는 빈 값
        if value is None:
            return True
        
        # 빈 컬렉션
        if isinstance(value, (list, dict)) and len(value) == 0:
            return True
        
        # 빈 문자열
        if isinstance(value, str) and value.strip() == "":
            return True
        
        # NaN 또는 무한대
        if isinstance(value, (int, float)):
            if np.isnan(value) or np.isinf(value):
                return True
        
        # 에러 메시지가 포함된 결과
        if isinstance(value, str) and any(word in value.lower() 
                                         for word in ["error", "exception", "failed", "null"]):
            return True
        
        return False
    
    def _calculate_accuracy_rate(self, analysis_result: UniversalAnalysisResult, 
                                ground_truth: Optional[Dict[str, Any]]) -> float:
        """정답 일치율 계산"""
        
        # MongoDB 직접 실행 결과가 있으면 이를 우선 사용
        if analysis_result.direct_mongodb_results:
            return self._calculate_mongodb_comparison_accuracy(analysis_result)
        
        if ground_truth is None:
            # Ground truth가 없으면 일관성 기반 정확도 계산
            return self._calculate_consistency_score(analysis_result)
        
        correct_results = 0
        total_comparisons = 0
        
        for key, calculated_value in analysis_result.calculation_results.items():
            if key in ground_truth:
                expected_value = ground_truth[key]
                
                if self._values_match(calculated_value, expected_value):
                    correct_results += 1
                total_comparisons += 1
        
        return correct_results / total_comparisons if total_comparisons > 0 else 1.0
    
    def _calculate_mongodb_comparison_accuracy(self, analysis_result: UniversalAnalysisResult) -> float:
        """MongoDB 직접 실행 결과와의 비교를 통한 정확도 계산"""
        correct_results = 0
        total_comparisons = 0
        
        for key, llm_value in analysis_result.calculation_results.items():
            if key in analysis_result.direct_mongodb_results:
                mongodb_value = analysis_result.direct_mongodb_results[key]
                
                if self._values_match(llm_value, mongodb_value):
                    correct_results += 1
                total_comparisons += 1
        
        return correct_results / total_comparisons if total_comparisons > 0 else 0.0
    
    def _values_match(self, calculated: Any, expected: Any, tolerance: float = 0.01) -> bool:
        """두 값의 일치 여부 확인 (허용 오차 포함)"""
        
        # 타입이 다르면 불일치
        if type(calculated) != type(expected):
            # 숫자 타입 간 비교는 허용
            if not (isinstance(calculated, (int, float)) and isinstance(expected, (int, float))):
                return False
        
        # 숫자 비교 (허용 오차 포함)
        if isinstance(calculated, (int, float)) and isinstance(expected, (int, float)):
            return abs(calculated - expected) <= tolerance
        
        # 문자열 비교
        if isinstance(calculated, str) and isinstance(expected, str):
            return calculated.strip().lower() == expected.strip().lower()
        
        # 리스트/딕셔너리 비교
        if isinstance(calculated, (list, dict)) and isinstance(expected, (list, dict)):
            return calculated == expected
        
        # 일반적인 동등성 비교
        return calculated == expected
    
    def _calculate_consistency_score(self, analysis_result: UniversalAnalysisResult) -> float:
        """Ground truth가 없을 때 일관성 기반 정확도 계산"""
        
        # 결과 값들의 일관성 검사
        consistency_score = 1.0
        
        # 수치 결과의 합리성 검사
        numeric_results = [v for v in analysis_result.calculation_results.values() 
                          if isinstance(v, (int, float))]
        
        if numeric_results:
            # 극값 검사 (너무 크거나 작은 값)
            for value in numeric_results:
                if value < 0 and "count" in str(analysis_result.calculation_results):
                    consistency_score -= 0.2  # 개수가 음수면 감점
                
                if value > 10000000:  # 천만 이상의 큰 값
                    consistency_score -= 0.1
        
        # 비율 결과의 합리성 검사 (0-100% 범위)
        for key, value in analysis_result.calculation_results.items():
            if any(word in key.lower() for word in ["rate", "ratio", "비율", "율"]):
                if isinstance(value, (int, float)) and (value < 0 or value > 100):
                    consistency_score -= 0.3
        
        return max(0.0, consistency_score)
    
    def _determine_overall_pass(self, semantic_error_rate: float, 
                               execution_success_rate: float,
                               empty_result_rate: float, 
                               accuracy_rate: float) -> bool:
        """전체 Pass/Fail 판정"""
        
        # 각 지표가 임계값을 만족하는지 확인
        semantic_pass = semantic_error_rate <= self.thresholds["semantic_error"]
        execution_pass = execution_success_rate >= self.thresholds["execution_success"]
        empty_pass = empty_result_rate <= self.thresholds["empty_result"]
        accuracy_pass = accuracy_rate >= self.thresholds["accuracy"]
        
        # 모든 지표가 통과해야 전체 통과
        return semantic_pass and execution_pass and empty_pass and accuracy_pass
    
    def generate_comprehensive_report(self, metrics: EvaluationMetrics, 
                                    analysis_result: UniversalAnalysisResult) -> str:
        """포괄적인 평가 리포트 생성 (비교 테이블 포함)"""
        
        status_emoji = "✅ PASS" if metrics.overall_pass else "❌ FAIL"
        
        report = f"""
# MongoDB 분석 평가 결과

## 전체 결과: {status_emoji}

### 분석 질의
```
{analysis_result.analysis_query}
```

### LLM vs MongoDB 직접 실행 비교
"""
        
        # 비교 테이블이 있는 경우 추가
        if metrics.comparison_table is not None and not metrics.comparison_table.empty:
            report += "\n" + metrics.comparison_table.to_string(index=False) + "\n\n"
        else:
            report += "비교 데이터가 없습니다.\n\n"
        
        report += f"""
### 4개 핵심 지표
| 지표 | 값 | 임계값 | 상태 |
|------|----|----|------|
| 의미 오류율 | {metrics.semantic_error_rate:.2%} | ≤{self.thresholds['semantic_error']:.2%} | {'✅' if metrics.semantic_error_rate <= self.thresholds['semantic_error'] else '❌'} |
| 실행 성공률 | {metrics.execution_success_rate:.2%} | ≥{self.thresholds['execution_success']:.2%} | {'✅' if metrics.execution_success_rate >= self.thresholds['execution_success'] else '❌'} |
| 무응답률 | {metrics.empty_result_rate:.2%} | ≤{self.thresholds['empty_result']:.2%} | {'✅' if metrics.empty_result_rate <= self.thresholds['empty_result'] else '❌'} |
| 정답 일치율 | {metrics.accuracy_rate:.2%} | ≥{self.thresholds['accuracy']:.2%} | {'✅' if metrics.accuracy_rate >= self.thresholds['accuracy'] else '❌'} |

### 실행된 MongoDB 쿼리들
"""
        
        for i, query in enumerate(analysis_result.mongodb_queries, 1):
            report += f"{i}. ```javascript\n{query}\n```\n\n"
        
        report += f"**평가 시간**: {analysis_result.timestamp}\n"
        
        return report

    def generate_simple_report(self, metrics: EvaluationMetrics, 
                              analysis_result: UniversalAnalysisResult) -> str:
        """간단한 평가 리포트 생성 (기존 버전 유지)"""
        
        status_emoji = "✅ PASS" if metrics.overall_pass else "❌ FAIL"
        
        report = f"""
# MongoDB 분석 평가 결과

## 전체 결과: {status_emoji}

### 분석 질의
```
{analysis_result.analysis_query}
```

### 4개 핵심 지표
| 지표 | 값 | 임계값 | 상태 |
|------|----|----|------|
| 의미 오류율 | {metrics.semantic_error_rate:.2%} | ≤{self.thresholds['semantic_error']:.2%} | {'✅' if metrics.semantic_error_rate <= self.thresholds['semantic_error'] else '❌'} |
| 실행 성공률 | {metrics.execution_success_rate:.2%} | ≥{self.thresholds['execution_success']:.2%} | {'✅' if metrics.execution_success_rate >= self.thresholds['execution_success'] else '❌'} |
| 무응답률 | {metrics.empty_result_rate:.2%} | ≤{self.thresholds['empty_result']:.2%} | {'✅' if metrics.empty_result_rate <= self.thresholds['empty_result'] else '❌'} |
| 정답 일치율 | {metrics.accuracy_rate:.2%} | ≥{self.thresholds['accuracy']:.2%} | {'✅' if metrics.accuracy_rate >= self.thresholds['accuracy'] else '❌'} |

### 계산 결과
"""
        
        for key, value in analysis_result.calculation_results.items():
            report += f"- **{key}**: {value}\n"
        
        report += f"\n**평가 시간**: {analysis_result.timestamp}\n"
        
        return report


# 간편 사용을 위한 헬퍼 함수
def quick_evaluate(analysis_query: str, 
                  mongodb_queries: List[str],
                  calculation_results: Dict[str, Any],
                  execution_logs: List[Dict] = None,
                  direct_mongodb_results: Dict[str, Any] = None,
                  ground_truth: Dict[str, Any] = None,
                  custom_thresholds: Dict[str, float] = None) -> EvaluationMetrics:
    """
    빠른 평가 실행을 위한 헬퍼 함수
    
    Args:
        analysis_query: 분석 질의
        mongodb_queries: 실행된 MongoDB 쿼리 리스트
        calculation_results: 계산 결과 딕셔너리 (LLM 산출)
        execution_logs: 실행 로그 (선택적)
        direct_mongodb_results: MongoDB 직접 실행 결과 (선택적)
        ground_truth: 정답 데이터 (선택적)
        custom_thresholds: 커스텀 임계값 (선택적)
    
    Returns:
        EvaluationMetrics: 평가 결과
    """
    
    # 분석 결과 객체 생성
    analysis_result = UniversalAnalysisResult(
        analysis_query=analysis_query,
        mongodb_queries=mongodb_queries,
        calculation_results=calculation_results,
        execution_logs=execution_logs or [],
        direct_mongodb_results=direct_mongodb_results
    )
    
    # 평가기 생성 및 실행
    evaluator = UniversalMongoDBEvaluator(thresholds=custom_thresholds)
    metrics = evaluator.evaluate(analysis_result, ground_truth)
    
    return metrics


# 사용 예제
def example_usage():
    """확장된 사용 예제 (비교 테이블 포함)"""
    
    # 1. 분석 결과 준비
    analysis_query = "care_313 컬렉션에서 사용자 수, 챗 수, 운영자 연결 비율을 분석해줘"
    
    mongodb_queries = [
        "db.care_313.find({'message': 'Received retrieval request'})",
        "db.care_313.aggregate([{'$group': {'_id': '$user_id'}}])",
        "db.care_313.find({'content': {'$regex': '운영자 연결'}})"
    ]
    
    # LLM이 계산한 결과
    calculation_results = {
        "user_count": 3,
        "chat_count": 8,
        "operator_connection_rate": 33.33
    }
    
    # MongoDB에서 직접 실행한 결과 (실제 값)
    direct_mongodb_results = {
        "user_count": 3,      # 일치
        "chat_count": 7,      # 불일치 (LLM: 8, 실제: 7)
        "operator_connection_rate": 35.71  # 불일치 (LLM: 33.33%, 실제: 35.71%)
    }
    
    execution_logs = [
        {"status": "success", "query_index": 0, "execution_time": 0.1},
        {"status": "success", "query_index": 1, "execution_time": 0.2},
        {"status": "success", "query_index": 2, "execution_time": 0.1}
    ]
    
    # 2. 빠른 평가 실행 (비교 데이터 포함)
    metrics = quick_evaluate(
        analysis_query=analysis_query,
        mongodb_queries=mongodb_queries,
        calculation_results=calculation_results,
        execution_logs=execution_logs,
        direct_mongodb_results=direct_mongodb_results
    )
    
    # 3. 결과 확인
    print(f"전체 결과: {'PASS' if metrics.overall_pass else 'FAIL'}")
    print(f"의미 오류율: {metrics.semantic_error_rate:.2%}")
    print(f"실행 성공률: {metrics.execution_success_rate:.2%}")
    print(f"무응답률: {metrics.empty_result_rate:.2%}")
    print(f"정답 일치율: {metrics.accuracy_rate:.2%}")
    
    # 4. 비교 테이블 출력
    if metrics.comparison_table is not None:
        print("\n=== LLM vs MongoDB 직접 실행 비교 ===")
        print(metrics.comparison_table.to_string(index=False))
    
    # 5. 포괄적인 리포트 생성
    analysis_result = UniversalAnalysisResult(
        analysis_query=analysis_query,
        mongodb_queries=mongodb_queries,
        calculation_results=calculation_results,
        execution_logs=execution_logs,
        direct_mongodb_results=direct_mongodb_results
    )
    
    evaluator = UniversalMongoDBEvaluator()
    comprehensive_report = evaluator.generate_comprehensive_report(metrics, analysis_result)
    print("\n" + "="*60)
    print("COMPREHENSIVE REPORT")
    print("="*60)
    print(comprehensive_report)
    
    return metrics


def example_with_mcp_integration():
    """MCP(everything) 계산기 연동 예제"""
    
    # 실제 사용 시나리오: LLM이 쿼리를 생성하고 MCP로 계산, MongoDB에서 직접 실행하여 비교
    
    analysis_query = "사용자별 평균 세션 시간과 총 접속 횟수를 분석해주세요"
    
    # LLM이 생성한 MongoDB 쿼리들
    mongodb_queries = [
        """db.sessions.aggregate([
            {$group: {
                _id: "$user_id",
                avg_session_time: {$avg: "$duration"},
                total_sessions: {$sum: 1}
            }}
        ])""",
        """db.sessions.aggregate([
            {$group: {
                _id: null,
                overall_avg_time: {$avg: "$duration"},
                total_users: {$addToSet: "$user_id"}
            }},
            {$project: {
                overall_avg_time: 1,
                user_count: {$size: "$total_users"}
            }}
        ])"""
    ]
    
    # LLM + MCP(everything)로 계산한 결과
    llm_mcp_results = {
        "avg_session_time": 25.4,  # 분
        "total_sessions": 156,
        "unique_users": 42,
        "avg_sessions_per_user": 3.71
    }
    
    # MongoDB에서 직접 실행한 실제 결과
    mongodb_direct_results = {
        "avg_session_time": 24.8,  #
        "avg_session_time": 24.8,  # 실제 값 (LLM보다 0.6분 낮음)
        "total_sessions": 158,     # 실제 값 (LLM보다 2개 많음) 
        "unique_users": 42,        # 정확히 일치
        "avg_sessions_per_user": 3.76  # 실제 값 (LLM보다 0.05 높음)
    }
    
    execution_logs = [
        {"status": "success", "query_index": 0, "execution_time": 0.15, "tool": "mcp_everything"},
        {"status": "success", "query_index": 1, "execution_time": 0.12, "tool": "mcp_everything"},
        {"status": "success", "query_index": 0, "execution_time": 0.08, "tool": "mongodb_direct"},
        {"status": "success", "query_index": 1, "execution_time": 0.09, "tool": "mongodb_direct"}
    ]
    
    # 평가 실행
    metrics = quick_evaluate(
        analysis_query=analysis_query,
        mongodb_queries=mongodb_queries,
        calculation_results=llm_mcp_results,
        execution_logs=execution_logs,
        direct_mongodb_results=mongodb_direct_results,
        custom_thresholds={
            "semantic_error": 0.05,    # 더 엄격한 임계값
            "execution_success": 0.95,
            "empty_result": 0.1,
            "accuracy": 0.85
        }
    )
    
    # 결과 분석
    print("\n" + "="*50)
    print("MCP INTEGRATION EXAMPLE RESULTS")
    print("="*50)
    
    print(f"\n전체 평가: {'✅ PASS' if metrics.overall_pass else '❌ FAIL'}")
    
    # 비교 테이블 출력
    if metrics.comparison_table is not None:
        print("\n📊 LLM+MCP vs MongoDB 직접 실행 비교:")
        print("-" * 70)
        print(metrics.comparison_table.to_string(index=False))
        
        # 일치/불일치 분석
        matches = len(metrics.comparison_table[metrics.comparison_table['일치 여부'] == '✅ 일치'])
        total = len(metrics.comparison_table)
        mismatch_rate = (total - matches) / total * 100 if total > 0 else 0
        
        print(f"\n📈 정확도 분석:")
        print(f"   - 일치: {matches}/{total} ({(matches/total*100):.1f}%)")
        print(f"   - 불일치율: {mismatch_rate:.1f}%")
        
        # 불일치 항목 상세 분석
        mismatches = metrics.comparison_table[metrics.comparison_table['일치 여부'] == '❌ 불일치']
        if not mismatches.empty:
            print(f"\n⚠️  불일치 항목 상세:")
            for _, row in mismatches.iterrows():
                print(f"   - {row['지표']}: LLM={row['LLM 계산 결과']} vs MongoDB={row['MongoDB 직접 실행']} (차이: {row['차이']})")
    
    return metrics


def quality_assured_analysis_example():
    """품질 보장 분석 예제"""
    
    def mock_execute_llm_analysis(query):
        """LLM 분석 실행 모의 함수"""
        class MockResult:
            def __init__(self):
                self.queries = [
                    "db.users.aggregate([{$group: {_id: '$status', count: {$sum: 1}}}])",
                    "db.users.find({active: true}).count()"
                ]
                self.data = {
                    "total_users": 1250,
                    "active_users": 980,
                    "activation_rate": 78.4
                }
        return MockResult()
    
    def mock_execute_mongodb_direct(queries):
        """MongoDB 직접 실행 모의 함수"""
        return {
            "total_users": 1247,      # 3명 차이
            "active_users": 982,      # 2명 차이  
            "activation_rate": 78.7   # 0.3% 차이
        }
    
    def quality_assured_analysis(query):
        """LLM 계산과 MongoDB 직접 실행을 비교하여 품질 보장"""
        
        # 1. LLM으로 분석 실행
        llm_results = mock_execute_llm_analysis(query)
        
        # 2. MongoDB에서 동일 쿼리 직접 실행
        mongodb_results = mock_execute_mongodb_direct(llm_results.queries)
        
        # 3. 품질 평가 (비교 포함)
        metrics = quick_evaluate(
            analysis_query=query,
            mongodb_queries=llm_results.queries,
            calculation_results=llm_results.data,
            direct_mongodb_results=mongodb_results,
            custom_thresholds={
                "semantic_error": 0.05,
                "execution_success": 0.95,
                "empty_result": 0.05,
                "accuracy": 0.90
            }
        )
        
        # 4. 품질 게이트 체크
        print(f"\n🔍 품질 검증 결과:")
        print(f"   - 전체 평가: {'✅ PASS' if metrics.overall_pass else '❌ FAIL'}")
        print(f"   - 정확도: {metrics.accuracy_rate:.1%}")
        
        if not metrics.overall_pass:
            print("\n❌ 품질 기준 미달:")
            print(f"   - 의미 오류율: {metrics.semantic_error_rate:.1%}")
            print(f"   - 실행 성공률: {metrics.execution_success_rate:.1%}")
            print(f"   - 무응답률: {metrics.empty_result_rate:.1%}")
            print(f"   - 정확도: {metrics.accuracy_rate:.1%}")
            
            if metrics.comparison_table is not None:
                print(f"\n   📊 불일치 항목:")
                mismatches = metrics.comparison_table[
                    metrics.comparison_table['일치 여부'] == '❌ 불일치'
                ]
                for _, row in mismatches.iterrows():
                    print(f"      {row['지표']}: 차이 {row['차이']}")
            
            print("\n⚠️  분석 결과 재검토 필요")
            return None
        
        print("✅ 품질 기준 통과 - 신뢰할 수 있는 결과입니다")
        return llm_results  # 품질 보장된 결과만 반환
    
    # 예제 실행
    query = "사용자 활성화 현황 분석"
    result = quality_assured_analysis(query)
    
    if result:
        print(f"\n📈 최종 분석 결과:")
        for key, value in result.data.items():
            print(f"   - {key}: {value}")


if __name__ == "__main__":
    print("=== 기본 사용 예제 ===")
    basic_metrics = example_usage()
    
    print("\n\n=== MCP 연동 예제 ===")
    mcp_metrics = example_with_mcp_integration()
    
    print("\n\n=== 품질 보장 분석 예제 ===")
    quality_assured_analysis_example()
