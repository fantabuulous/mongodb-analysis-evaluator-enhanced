"""
MCP 계산기 연동 예제
"""
from mongodb_evaluation_system import quick_evaluate

def mcp_integration_example():
    """MCP와 MongoDB 직접 실행 결과 비교 예제"""
    
    # LLM + MCP 계산 결과
    mcp_results = {
        "avg_session_time": 25.4,
        "total_sessions": 156,
        "unique_users": 42
    }
    
    # MongoDB 직접 실행 결과
    mongodb_results = {
        "avg_session_time": 24.8,
        "total_sessions": 158,
        "unique_users": 42
    }
    
    metrics = quick_evaluate(
        analysis_query="세션 분석",
        mongodb_queries=["db.sessions.aggregate([...])"],
        calculation_results=mcp_results,
        direct_mongodb_results=mongodb_results
    )
    
    print("비교 테이블:")
    print(metrics.comparison_table.to_string(index=False))

if __name__ == "__main__":
    mcp_integration_example()
