"""
Template Loader Module
QueryGoal 템플릿을 로드하고 복제/초기화하는 모듈
"""
import json
import copy
import os
from datetime import datetime
import random
import string
from typing import Dict, Any, Optional
from pathlib import Path


class TemplateLoader:
    """QueryGoal 템플릿 로드 및 초기화"""

    def __init__(self, template_dir: Optional[str] = None):
        """
        Args:
            template_dir: 템플릿 디렉토리 경로
        """
        if template_dir is None:
            # 기본 경로 설정
            current_file = Path(__file__)
            self.template_dir = current_file.parent.parent / "templates"
        else:
            self.template_dir = Path(template_dir)

        self.templates = {}
        self._load_templates()

    def _load_templates(self):
        """템플릿 파일들을 메모리에 로드"""
        template_files = self.template_dir.glob("*.json")

        for template_file in template_files:
            template_name = template_file.stem
            try:
                with open(template_file, 'r', encoding='utf-8') as f:
                    self.templates[template_name] = json.load(f)
                    print(f"Loaded template: {template_name}")
            except Exception as e:
                print(f"Error loading template {template_file}: {e}")

    def get_template(self, template_name: str = "base_querygoal") -> Dict[str, Any]:
        """
        템플릿 가져오기

        Args:
            template_name: 템플릿 이름 (기본값: base_querygoal)

        Returns:
            템플릿 딕셔너리의 딥카피
        """
        if template_name not in self.templates:
            # 템플릿이 없으면 다시 로드 시도
            self._load_templates()

        if template_name not in self.templates:
            raise ValueError(f"Template '{template_name}' not found")

        return copy.deepcopy(self.templates[template_name])

    def generate_goal_id(self) -> str:
        """
        고유한 Goal ID 생성

        Returns:
            goal_YYYYMMDD_HHMMSS_XXXXX 형식의 ID
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        random_suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=5))
        return f"goal_{timestamp}_{random_suffix}"

    def create_querygoal(self,
                         goal_type: str,
                         category: str,
                         requires_model: bool = False,
                         pipeline_stages: Optional[list] = None) -> Dict[str, Any]:
        """
        새로운 QueryGoal 인스턴스 생성

        Args:
            goal_type: Goal 타입 (예: "goal1_query_cooling_failure")
            category: 카테고리 (예: "diagnostics", "prediction")
            requires_model: 모델 필요 여부
            pipeline_stages: 파이프라인 단계 리스트

        Returns:
            초기화된 QueryGoal 딕셔너리
        """
        # 기본 템플릿 로드
        querygoal = self.get_template("base_querygoal")

        # QueryGoal 객체 참조
        qg = querygoal["QueryGoal"]

        # 기본 필드 설정
        qg["goalId"] = self.generate_goal_id()
        qg["goalType"] = goal_type

        # 메타데이터 설정
        qg["metadata"]["category"] = category
        qg["metadata"]["requiresModel"] = requires_model

        # 파이프라인 스테이지 설정
        if pipeline_stages:
            qg["metadata"]["pipelineStages"] = pipeline_stages
        else:
            # 기본 스테이지 설정
            if requires_model:
                qg["metadata"]["pipelineStages"] = ["swrlSelection", "yamlBinding", "simulation"]
            else:
                qg["metadata"]["pipelineStages"] = ["aasQuery", "dataFiltering"]

        # 타임스탬프 추가
        qg["metadata"]["notes"] = f"Created at {datetime.now().isoformat()}"

        return querygoal

    def clone_and_update(self,
                         template: Dict[str, Any],
                         updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        템플릿을 복제하고 업데이트

        Args:
            template: 원본 템플릿
            updates: 업데이트할 값들

        Returns:
            업데이트된 템플릿
        """
        cloned = copy.deepcopy(template)

        # QueryGoal 객체에 업데이트 적용
        qg = cloned["QueryGoal"]

        for key, value in updates.items():
            if key in qg:
                if isinstance(qg[key], dict) and isinstance(value, dict):
                    # 딕셔너리는 재귀적으로 업데이트
                    qg[key].update(value)
                else:
                    qg[key] = value
            elif key == "metadata" and isinstance(value, dict):
                # 메타데이터는 특별 처리
                qg["metadata"].update(value)

        return cloned

    def save_querygoal(self, querygoal: Dict[str, Any], output_path: str):
        """
        QueryGoal을 파일로 저장

        Args:
            querygoal: QueryGoal 딕셔너리
            output_path: 저장할 파일 경로
        """
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(querygoal, f, indent=2, ensure_ascii=False)

        print(f"QueryGoal saved to: {output_path}")