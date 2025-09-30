"""
Work Directory Manager
Goal별 독립적인 작업 디렉터리 관리
"""
import logging
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional

from ..exceptions import WorkDirectoryError

logger = logging.getLogger("querygoal.work_directory")


class WorkDirectoryManager:
    """작업 디렉터리 관리자"""

    def __init__(self, base_directory: Optional[Path] = None):
        """
        Args:
            base_directory: 작업 디렉터리의 기본 경로 (None이면 temp/runtime_executions 사용)
        """
        if base_directory is None:
            # 프로젝트 루트의 temp/runtime_executions 사용
            from pathlib import Path
            project_root = Path(__file__).parent.parent.parent.parent
            self.base_directory = project_root / "temp" / "runtime_executions"
        else:
            self.base_directory = Path(base_directory)

        # 기본 디렉터리 생성
        self.base_directory.mkdir(parents=True, exist_ok=True)
        logger.info(f"Work directory base: {self.base_directory}")

    def create_work_directory(self, goal_id: str) -> Path:
        """
        Goal별 작업 디렉터리 생성

        Args:
            goal_id: QueryGoal의 goalId

        Returns:
            생성된 작업 디렉터리 경로
        """
        try:
            # 타임스탬프 추가로 중복 방지
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            work_dir_name = f"{goal_id}_{timestamp}"
            work_directory = self.base_directory / work_dir_name

            # 디렉터리 생성
            work_directory.mkdir(parents=True, exist_ok=True)

            # 하위 디렉터리 구조 생성
            (work_directory / "inputs").mkdir(exist_ok=True)
            (work_directory / "outputs").mkdir(exist_ok=True)
            (work_directory / "logs").mkdir(exist_ok=True)
            (work_directory / "temp").mkdir(exist_ok=True)

            logger.info(f"Created work directory: {work_directory}")
            return work_directory

        except Exception as e:
            raise WorkDirectoryError(f"Failed to create work directory for {goal_id}: {e}") from e

    def cleanup_work_directory(self, work_directory: Path, force: bool = False):
        """
        작업 디렉터리 정리

        Args:
            work_directory: 정리할 작업 디렉터리 경로
            force: True일 경우 강제 삭제, False일 경우 오래된 것만 삭제
        """
        try:
            if not work_directory.exists():
                logger.warning(f"Work directory does not exist: {work_directory}")
                return

            if force:
                # 강제 삭제
                shutil.rmtree(work_directory)
                logger.info(f"Removed work directory: {work_directory}")
            else:
                # 오래된 임시 파일만 정리
                temp_dir = work_directory / "temp"
                if temp_dir.exists():
                    for file in temp_dir.glob("*"):
                        file.unlink()
                    logger.debug(f"Cleaned temp files in: {work_directory}")

        except Exception as e:
            logger.warning(f"Failed to cleanup work directory {work_directory}: {e}")

    def get_existing_work_directories(self, goal_id: Optional[str] = None) -> list[Path]:
        """
        기존 작업 디렉터리 목록 조회

        Args:
            goal_id: 특정 Goal ID로 필터링 (None이면 전체)

        Returns:
            작업 디렉터리 경로 리스트
        """
        try:
            if goal_id:
                # 특정 Goal ID로 시작하는 디렉터리만
                pattern = f"{goal_id}_*"
                return sorted(self.base_directory.glob(pattern), reverse=True)
            else:
                # 모든 작업 디렉터리
                return sorted([d for d in self.base_directory.iterdir() if d.is_dir()], reverse=True)

        except Exception as e:
            logger.warning(f"Failed to list work directories: {e}")
            return []