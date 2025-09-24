#!/usr/bin/env python3
"""
단일 요소(jobs_data) 테스트 스크립트
수정된 DataOrchestrator API 호출 방식 검증
"""

import sys
import json
import logging
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.append(str(Path(__file__).parent))

from execution_engine.aasx_data_orchestrator import AASXDataOrchestrator

def test_single_element():
    """jobs_data 단일 요소 테스트"""
    
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    logger = logging.getLogger(__name__)
    
    try:
        # DataOrchestrator 인스턴스 생성
        logger.info("🚀 Creating AASXDataOrchestrator instance...")
        orchestrator = AASXDataOrchestrator()
        
        # AASX 서버 연결 테스트
        logger.info("🔍 Testing AASX server connection...")
        test_results = orchestrator.test_aasx_connection()
        logger.info(f"Connection test results: {json.dumps(test_results, indent=2)}")
        
        if not test_results.get("server_accessible"):
            logger.error("❌ AASX server is not accessible")
            return False
            
        # jobs_data 단일 요소 조회 테스트
        logger.info("📋 Testing jobs_data element extraction...")
        
        shell_id = "urn:factory:simulation:main"
        submodel_id = "urn:factory:submodel:simulation_data" 
        element_id = "jobs_data"
        
        # raw 데이터 조회
        raw_value = orchestrator._get_submodel_element_value(shell_id, submodel_id, element_id)
        
        if raw_value is None:
            logger.error("❌ Failed to get jobs_data raw value")
            return False
            
        logger.info(f"✅ Raw value extracted (length: {len(raw_value)} chars)")
        logger.info(f"Raw value preview: {raw_value[:100]}...")
        
        # JSON 파싱 테스트
        try:
            jobs_json = json.loads(raw_value)
            logger.info(f"✅ JSON parsing successful - found {len(jobs_json)} jobs")
            
            # 첫 번째 job 정보 출력
            if jobs_json:
                first_job = jobs_json[0]
                logger.info(f"First job: {json.dumps(first_job, indent=2)}")
                
        except json.JSONDecodeError as e:
            logger.error(f"❌ JSON parsing failed: {e}")
            return False
            
        # 테스트 결과 파일 생성
        output_dir = Path("temp/single_test")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        test_file = output_dir / "jobs_test.json"
        with open(test_file, 'w', encoding='utf-8') as f:
            json.dump({"jobs": jobs_json}, f, indent=2, ensure_ascii=False)
            
        logger.info(f"✅ Test file created: {test_file}")
        logger.info(f"✅ Single element test completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Single element test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_single_element()
    if success:
        print("\n🎉 Single element test PASSED!")
        exit(0)
    else:
        print("\n💥 Single element test FAILED!")
        exit(1)