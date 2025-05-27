# MongoDB Analysis Quality Evaluation System

**범용 MongoDB 분석 자동 평가 시스템** - Evidently AI 라이브러리 기반의 4개 핵심 지표 자동 산출 및 Pass/Fail 판정 시스템 + **LLM vs MongoDB 직접 실행 결과 비교**

## 🎯 핵심 기능

### ⚡ 4개 핵심 지표 자동 산출
1. **의미 오류율** - 논리적 모순, 불가능한 조건 자동 감지  
2. **실행 성공률** - MongoDB 쿼리 실행 안정성 측정  
3. **무응답률** - 빈 결과, NULL, 에러 등 무효 응답 비율  
4. **정답 일치율** - 일관성 및 정확도 자동 평가  

### 🆕 NEW: Side-by-Side 비교 테이블
- **LLM 계산 결과 vs MongoDB 직접 실행 결과** 실시간 비교  
- **차이율 자동 계산** 및 불일치 항목 상세 분석  
- **MCP(Everything) 계산기 연동 지원**

### 🌐 완전 범용적
- ✅ 사용자 분석, 매출 분석, KPI 분석 등 **모든 MongoDB 분석 타입 지원**  
- ✅ 컬렉션이나 도메인에 관계없이 **동일한 평가 프레임워크** 적용  
- ✅ **실시간 Pass/Fail 판정** 및 품질 보장  

## 🚀 초간단 사용법

```python
from mongodb_evaluation_system import quick_evaluate

llm_results = {
    "user_count": 3,
    "chat_count": 8,
    "operator_connection_rate": 33.33
}

mongodb_direct_results = {
    "user_count": 3,
    "chat_count": 7,
    "operator_connection_rate": 35.71
}

metrics = quick_evaluate(
    analysis_query="사용자별 접속 패턴 분석해줘",
    mongodb_queries=["db.logs.find({'type': 'login'})"],
    calculation_results=llm_results,
    direct_mongodb_results=mongodb_direct_results
)

print(f"결과: {'✅ 신뢰 가능' if metrics.overall_pass else '❌ 재검토 필요'}")
print(f"정확도: {metrics.accuracy_rate:.1%}")

if metrics.comparison_table is not None:
    print("\n📊 LLM vs MongoDB 직접 실행 비교:")
    print(metrics.comparison_table.to_string(index=False))
```

## 🔧 설치 및 설정

```bash
pip install evidently pandas numpy
```

## 🆕 주요 개선 사항

### Enhanced Version - LLM vs MongoDB 직접 실행 비교 기능 추가

#### 🔥 새로운 핵심 기능
- **Side-by-Side 비교 테이블** 자동 생성 - LLM 계산 결과와 MongoDB 직접 실행 결과 실시간 비교  
- **차이율 자동 계산** - 숫자 값의 절대 차이 및 백분율 차이 자동 산출  
- **불일치 항목 상세 분석** - 어떤 지표가 얼마나 차이나는지 구체적 분석  
- **MCP(Everything) 계산기 연동** 지원 - 외부 계산 도구와의 통합 평가  

#### 📊 향상된 평가 정확도
- **MongoDB 기반 정확도 계산** - 실제 데이터베이스 실행 결과를 기준으로 한 정확도 측정  
- **실시간 정확도 모니터링** - 계산 과정에서 즉시 품질 확인 가능  
- **품질 게이트 시스템** - 기준 미달 시 자동 경고 및 재분석 권장  

#### 🛠️ 새로운 메서드 및 기능
- `generate_comprehensive_report()` - 비교 테이블이 포함된 상세 평가 리포트 생성  
- `_create_comparison_table()` - LLM과 MongoDB 결과를 비교하는 pandas DataFrame 생성  
- `_calculate_mongodb_comparison_accuracy()` - MongoDB 직접 실행 결과 기반 정확도 계산  
- `_format_value()` - 다양한 데이터 타입의 값을 표시용으로 포맷팅  
- `_calculate_difference()` - 두 값 간의 차이를 절대값과 백분율로 계산  

#### 🔧 확장된 API
- **새로운 파라미터**: `direct_mongodb_results` - MongoDB에서 직접 실행한 결과 데이터  
- **새로운 반환값**: `comparison_table` - pandas DataFrame 형태의 비교 테이블  
- **향상된 `quick_evaluate()` 함수** - 한 번의 호출로 LLM과 MongoDB 결과 비교 평가  

#### 📈 사용 시나리오 확장
- **개발 단계**: LLM 모델의 MongoDB 쿼리 생성 정확도 검증  
- **프로덕션 모니터링**: 실시간 분석 결과 품질 보장  
- **성능 튜닝**: 계산 로직 최적화를 위한 차이 분석  
- **품질 보증**: 자동화된 분석 파이프라인의 신뢰성 확보  

#### 🎯 실용적 개선사항
- **시각적 피드백**: ✅/❌ 이모지를 통한 직관적인 일치/불일치 표시  
- **상세한 오차 정보**: 단순 불일치가 아닌 구체적인 차이값 제공  
- **유연한 임계값 설정**: 프로젝트별 요구사항에 맞는 엄격한 기준 적용 가능  
- **포괄적인 로깅**: 분석 과정의 모든 단계를 추적 가능  

#### 🔄 기존 기능과의 호환성
- **기존 API 완전 호환** - 기존 코드 수정 없이 새 기능 사용 가능  
- **점진적 도입 가능** - 선택적으로 비교 기능만 추가하여 사용  
- **기존 리포트 유지** - `generate_simple_report()`는 기존과 동일하게 동작  

---

이번 업데이트로 단순한 일관성 검사를 넘어서 **실제 데이터베이스 실행 결과와의 정확한 비교**가 가능해졌습니다.  
이는 LLM 기반 분석 시스템의 신뢰성을 크게 향상시키는 핵심 기능입니다.
