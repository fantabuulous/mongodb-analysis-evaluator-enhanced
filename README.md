# MongoDB Analysis Quality Evaluation System

**MongoDB 분석 자동 평가 시스템** - Evidently AI 라이브러리 기반의 4개 핵심 지표 자동 산출 및 Pass/Fail 판정 시스템 + **LLM vs MongoDB 직접 실행 결과 비교**

## 🎯 핵심 기능

### ⚡ 4개 핵심 지표 자동 산출
1. **의미 오류율** - 논리적 모순, 불가능한 조건 자동 감지
2. **실행 성공률** - MongoDB 쿼리 실행 안정성 측정  
3. **무응답률** - 빈 결과, NULL, 에러 등 무효 응답 비율
4. **정답 일치율** - 일관성 및 정확도 자동 평가

### 🆕 NEW: LLM vs MongoDB 직접 실행 비교
- ✅ **Side-by-Side 비교 테이블** 자동 생성
- ✅ **차이율 자동 계산** 및 불일치 항목 상세 분석
- ✅ **MongoDB 기반 정확도 계산** - 실제 DB 실행 결과 기준
- ✅ **MCP(Everything) 계산기 연동** 지원

### 🌐 완전 범용적
- ✅ 사용자 분석, 매출 분석, KPI 분석 등 **모든 MongoDB 분석 타입 지원**
- ✅ 컬렉션이나 도메인에 관계없이 **동일한 평가 프레임워크** 적용
- ✅ **실시간 Pass/Fail 판정** 및 품질 보장

## 🚀 초간단 사용법

### 한 줄로 평가 완료 (Enhanced)
```python
from mongodb_evaluation_system import quick_evaluate

# LLM이 계산한 결과
llm_results = {
    "user_count": 3,
    "chat_count": 8,
    "operator_connection_rate": 33.33
}

# MongoDB에서 직접 실행한 결과
mongodb_direct_results = {
    "user_count": 3,
    "chat_count": 7,
    "operator_connection_rate": 35.71
}

# 분석 후 즉시 품질 평가 + 비교 분석
metrics = quick_evaluate(
    analysis_query="사용자별 접속 패턴 분석해줘",
    mongodb_queries=["db.logs.find({'type': 'login'})"],
    calculation_results=llm_results,
    direct_mongodb_results=mongodb_direct_results  # 🆕 새로운 파라미터
)

print(f"결과: {'✅ 신뢰 가능' if metrics.overall_pass else '❌ 재검토 필요'}")
print(f"정확도: {metrics.accuracy_rate:.1%}, 성공률: {metrics.execution_success_rate:.1%}")

# 🆕 비교 테이블 출력
if metrics.comparison_table is not None:
    print("\n📊 LLM vs MongoDB 직접 실행 비교:")
    print(metrics.comparison_table.to_string(index=False))
```

### 상세 평가 및 리포트
```python
from mongodb_evaluation_system import UniversalMongoDBEvaluator, UniversalAnalysisResult

# 1. 분석 결과 준비 (LLM + MongoDB 직접 실행)
analysis_result = UniversalAnalysisResult(
    analysis_query="월별 매출과 성장률 계산",
    mongodb_queries=["db.orders.aggregate([...])"],
    calculation_results={"revenue": 125000, "growth_rate": 15.74},  # LLM 계산
    execution_logs=[{"status": "success"}],
    direct_mongodb_results={"revenue": 124850, "growth_rate": 15.68}  # 🆕 DB 직접 실행
)

# 2. 평가 실행 및 향상된 리포트 생성
evaluator = UniversalMongoDBEvaluator()
metrics = evaluator.evaluate(analysis_result)
report = evaluator.generate_comprehensive_report(metrics, analysis_result)  # 🆕 향상된 리포트

print(report)
```

## 📊 실제 사용 예제

### 다양한 분석 타입 지원
```python
# 사용자 행동 분석 with 비교
metrics = quick_evaluate(
    "사용자별 평균 세션 시간 분석",
    ["db.sessions.aggregate([{'$group': {'_id': '$user_id', 'avg_duration': {'$avg': '$duration'}}}])"],
    {"avg_session_duration": 185.5, "total_users": 1250},  # LLM 계산
    {"avg_session_duration": 184.8, "total_users": 1248}   # 🆕 MongoDB 직접 실행
)

# 매출 트렌드 분석 with 비교
metrics = quick_evaluate(
    "월별 매출과 전월 대비 성장률",
    ["db.orders.aggregate([{'$match': {'date': {'$gte': '2025-01'}}}])"],
    {"current_revenue": 125000, "growth_rate": 15.74},     # LLM 계산
    {"current_revenue": 124850, "growth_rate": 15.68}      # 🆕 MongoDB 직접 실행
)

# KPI 종합 분석 with 비교
metrics = quick_evaluate(
    "사용자 참여도와 전환율 분석", 
    ["db.events.aggregate([...])", "db.conversions.aggregate([...])"],
    {"engagement_score": 7.2, "conversion_rate": 3.45},   # LLM 계산
    {"engagement_score": 7.1, "conversion_rate": 3.52}    # 🆕 MongoDB 직접 실행
)

# 🆕 비교 결과 상세 분석
if metrics.comparison_table is not None:
    print("\n📈 차이 분석:")
    for _, row in metrics.comparison_table.iterrows():
        if row['일치'] == '❌':
            print(f"⚠️  {row['지표']}: LLM({row['LLM 값']}) vs MongoDB({row['MongoDB 값']}) - 차이: {row['차이']}")
```

## ⚙️ 커스텀 설정

### 엄격한 품질 기준 적용
```python
# 더 엄격한 임계값 설정 + MongoDB 비교 기준
strict_thresholds = {
    "semantic_error": 0.05,     # 5% 이하
    "execution_success": 0.95,  # 95% 이상 
    "empty_result": 0.1,        # 10% 이하
    "accuracy": 0.95,           # 95% 이상
    "mongodb_comparison": 0.98  # 🆕 MongoDB 대비 98% 이상 일치
}

metrics = quick_evaluate(
    analysis_query="질의",
    mongodb_queries=["쿼리들"], 
    calculation_results={"결과": 123},
    direct_mongodb_results={"결과": 122},  # 🆕 비교 기준
    custom_thresholds=strict_thresholds
)
```

### 실시간 품질 게이트
```python
def reliable_analysis_with_comparison(query):
    """품질 기준 통과할 때까지 자동 재분석 - MongoDB 비교 포함"""
    for attempt in range(3):
        # LLM 분석 실행
        llm_results = perform_llm_analysis(query)
        
        # MongoDB 직접 실행 🆕
        mongodb_results = perform_direct_mongodb_analysis(query)
        
        # 품질 평가 (LLM vs MongoDB 비교 포함)
        metrics = quick_evaluate(
            query, 
            llm_results.queries, 
            llm_results.data,
            mongodb_results.data  # 🆕 비교 데이터
        )
        
        if metrics.overall_pass:
            print(f"✅ 품질 보장 완료 - MongoDB 일치율: {metrics.mongodb_accuracy_rate:.1%}")
            return llm_results
        
        print(f"❌ 품질 미달, 재시도 {attempt + 1}/3")
        if metrics.comparison_table is not None:
            print("🔍 불일치 항목:", metrics.comparison_table[metrics.comparison_table['일치'] == '❌']['지표'].tolist())
    
    raise Exception("품질 기준을 만족하는 분석 실패")
```

## 🔧 설치 및 설정

### 필수 의존성
```bash
pip install evidently pandas numpy
```

### 사용 시작
```python
# 1. 모듈 임포트
from mongodb_evaluation_system import quick_evaluate

# 2. 즉시 평가 실행 (기본 + 비교)
metrics = quick_evaluate(
    "분석 질의", 
    ["MongoDB 쿼리들"], 
    {"LLM 계산 결과들"},
    {"MongoDB 직접 실행 결과들"}  # 🆕 추가
)

# 3. 품질 확인
print(f"품질: {'PASS' if metrics.overall_pass else 'FAIL'}")
print(f"MongoDB 일치율: {metrics.mongodb_accuracy_rate:.1%}")  # 🆕
```

## 📈 지원하는 분석 패턴

✅ **집계 분석**: 카운트, 합계, 평균 등  
✅ **비율 계산**: 전환율, 증가율, 점유율 등  
✅ **시계열 분석**: 트렌드, 패턴, 주기성 등  
✅ **사용자 분석**: 행동, 세분화, 코호트 등  
✅ **성능 분석**: 응답시간, 처리량, 오류율 등  
✅ **비즈니스 분석**: 매출, 수익, KPI 등  

## 🔍 자동 감지되는 품질 이슈

🔍 **의미 오류**: 논리적 모순, 불가능한 조건  
🔍 **실행 오류**: 문법 오류, 연결 실패, 권한 문제  
🔍 **무효 결과**: 빈 값, NULL, NaN, 에러 메시지  
🔍 **정확도 문제**: 예상 범위 초과, 일관성 부족  
🔍 **🆕 LLM-MongoDB 불일치**: 계산 결과 차이, 로직 오류  

## 🆕 Enhanced 버전 주요 개선사항

### 📊 LLM vs MongoDB 직접 실행 비교 기능
- **Side-by-Side 비교 테이블** 자동 생성
- **차이율 자동 계산** (절대값 + 백분율)
- **불일치 항목 상세 분석**
- **시각적 피드백** (✅/❌ 이모지)

### 🎯 향상된 평가 정확도
- **MongoDB 기반 정확도 계산** - 실제 DB 실행 결과 기준
- **실시간 정확도 모니터링**
- **품질 게이트 시스템** - 기준 미달 시 자동 경고

### 🛠️ 새로운 메서드 및 기능
- `generate_comprehensive_report()` - 비교 테이블 포함 상세 리포트
- `_create_comparison_table()` - pandas DataFrame 비교 테이블 생성
- `_calculate_mongodb_comparison_accuracy()` - MongoDB 기반 정확도
- `_calculate_difference()` - 두 값 간 차이 계산

### 🔄 확장된 API
- **새로운 파라미터**: `direct_mongodb_results`
- **새로운 반환값**: `comparison_table`, `mongodb_accuracy_rate`
- **향상된 `quick_evaluate()` 함수**


## 🤝 기여 및 라이선스

이 프로젝트는 **Evidently AI** 라이브러리를 기반으로 구축되었습니다.

### 참고한 Evidently 코드
- `evidently.metrics.base_metric.Metric` - 커스텀 메트릭 구현
- `evidently.tests.base_test.Test` - Pass/Fail 판정 시스템
- `evidently.test_suite.TestSuite` - 통합 평가 프레임워크

### 기여 방법
1. Fork this repository
2. Create your feature branch
3. Commit your changes 
4. Push to the branch
5. Create a Pull Request

---

**🚀 이제 LLM 분석 결과와 실제 MongoDB 실행 결과를 자동으로 비교하여 최고 수준의 품질 보장이 제공됩니다!** 

**Enhanced 버전의 핵심 가치**: 단순한 일관성 검사를 넘어서 **실제 데이터베이스 실행 결과와의 정확한 비교**로 LLM 기반 분석 시스템의 신뢰성을 크게 향상시킵니다.

문의사항이나 개선 제안이 있으시면 이슈를 생성해주세요.
