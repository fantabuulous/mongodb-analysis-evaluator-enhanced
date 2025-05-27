"""
기본 사용 예제
"""
from mongodb_evaluation_system import quick_evaluate

def basic_example():
    """기본적인 평가 예제"""
    
    analysis_query = "사용자별 접속 패턴 분석"
    mongodb_queries = ["db.users.aggregate([{'$group': {'_id': '$user_id'}}])"]
    calculation_results = {"total_users": 100, "active_users": 75}
    
    metrics = quick_evaluate(
        analysis_query=analysis_query,
        mongodb_queries=mongodb_queries,
        calculation_results=calculation_results
    )
    
    print(f"평가 결과: {'PASS' if metrics.overall_pass else 'FAIL'}")
    print(f"정확도: {metrics.accuracy_rate:.2%}")

if __name__ == "__main__":
    basic_example()
