# path_resolver.py
"""
환경별 경로 해결 유틸리티
Kubernetes와 로컬 환경에서 동적으로 적절한 작업 경로를 제공
"""
import os
import tempfile
from pathlib import Path
from typing import Optional

class PathResolver:
    """환경별 작업 경로를 동적으로 해결하는 클래스"""
    
    @staticmethod
    def is_kubernetes_environment() -> bool:
        """Kubernetes 환경인지 감지"""
        indicators = [
            os.path.exists('/var/run/secrets/kubernetes.io'),  # K8s service account
            os.environ.get('KUBERNETES_SERVICE_HOST'),         # K8s API server
            os.path.exists('/etc/podinfo'),                    # Pod metadata
            os.environ.get('POD_NAME'),                        # Pod name env var
        ]
        return any(indicators)
    
    @staticmethod
    def get_work_directory(preferred_path: Optional[str] = None) -> Path:
        """
        환경에 적합한 작업 디렉토리 반환
        
        Args:
            preferred_path: 선호하는 경로 (주로 K8s PVC 경로)
            
        Returns:
            사용 가능한 작업 디렉토리 경로
        """
        # 1. 환경 감지
        is_k8s = PathResolver.is_kubernetes_environment()
        
        # 2. Kubernetes 환경에서 PVC 경로 시도
        if is_k8s and preferred_path:
            pvc_path = Path(preferred_path)
            if PathResolver._is_writable(pvc_path):
                print(f"✅ Using Kubernetes PVC path: {pvc_path}")
                return pvc_path
        
        # 3. 로컬 환경 또는 PVC 실패시 임시 디렉토리 사용
        temp_base = Path(tempfile.gettempdir()) / "factory_automation"
        if PathResolver._ensure_directory(temp_base):
            print(f"📁 Using local temp directory: {temp_base}")
            return temp_base
            
        # 4. 최후 수단: 현재 디렉토리
        current_work = Path.cwd() / "work"
        if PathResolver._ensure_directory(current_work):
            print(f"⚠️ Using current directory work folder: {current_work}")
            return current_work
            
        raise RuntimeError("Could not find any writable directory for work files")
    
    @staticmethod
    def _is_writable(path: Path) -> bool:
        """디렉토리가 쓰기 가능한지 확인"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            test_file = path / ".write_test"
            test_file.write_text("test")
            test_file.unlink()
            return True
        except (OSError, PermissionError):
            return False
    
    @staticmethod 
    def _ensure_directory(path: Path) -> bool:
        """디렉토리 생성 및 확인"""
        try:
            path.mkdir(parents=True, exist_ok=True)
            return path.exists() and path.is_dir()
        except (OSError, PermissionError):
            return False

# 편의 함수들
def get_simulation_work_dir() -> Path:
    """시뮬레이션 작업용 디렉토리 반환"""
    return PathResolver.get_work_directory("/data")

def get_temp_work_dir() -> Path:
    """임시 작업용 디렉토리 반환"""
    return PathResolver.get_work_directory()