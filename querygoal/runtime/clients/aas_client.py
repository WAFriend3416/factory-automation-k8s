"""
AAS Server REST API Client
AAS 서버와의 통신을 담당하는 클라이언트
"""
import asyncio
import base64
import httpx
import logging
from typing import Dict, Any, List, Optional
from urllib.parse import urljoin

from ..exceptions import AASConnectionError

logger = logging.getLogger("querygoal.aas_client")


class AASClient:
    """AAS 서버 REST API 클라이언트"""

    def __init__(self, base_url: str = None, timeout: int = 30):
        # 설정에서 AAS 서버 URL 가져오기
        if base_url is None:
            from config import AAS_SERVER_URL
            base_url = AAS_SERVER_URL

        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = None

    async def __aenter__(self):
        await self._ensure_client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def _ensure_client(self):
        """HTTP 클라이언트 초기화"""
        if self.client is None:
            self.client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_keepalive_connections=10, max_connections=50)
            )

    def _encode_id(self, id_string: str) -> str:
        """AAS ID를 Base64 URL-safe 형태로 인코딩"""
        return base64.urlsafe_b64encode(id_string.encode()).decode().rstrip('=')

    async def list_shells(self) -> List[Dict[str, Any]]:
        """모든 AAS Shell 목록 조회"""

        await self._ensure_client()

        try:
            url = urljoin(self.base_url, "/shells")

            response = await self.client.get(url)
            response.raise_for_status()

            shells_data = response.json()

            # AAS 서버 응답 형식에 따라 조정
            if isinstance(shells_data, dict):
                return shells_data.get("result", shells_data.get("shells", []))
            elif isinstance(shells_data, list):
                return shells_data
            else:
                return []

        except httpx.HTTPStatusError as e:
            raise AASConnectionError(f"HTTP error while listing shells: {e.response.status_code}") from e
        except Exception as e:
            raise AASConnectionError(f"Failed to list AAS shells: {e}") from e

    async def get_shell(self, shell_id: str) -> Dict[str, Any]:
        """특정 Shell 정보 조회"""

        await self._ensure_client()

        try:
            # Shell ID 인코딩 (필요시)
            encoded_shell_id = shell_id  # 필요하면 URL 인코딩
            url = urljoin(self.base_url, f"/shells/{encoded_shell_id}")

            response = await self.client.get(url)
            response.raise_for_status()

            return response.json()

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AASConnectionError(f"Shell not found: {shell_id}") from e
            raise AASConnectionError(f"HTTP error while getting shell {shell_id}: {e.response.status_code}") from e
        except Exception as e:
            raise AASConnectionError(f"Failed to get shell {shell_id}: {e}") from e

    async def list_submodels(self, shell_id: str = None) -> List[Dict[str, Any]]:
        """Submodel 목록 조회"""

        await self._ensure_client()

        try:
            if shell_id:
                # 특정 Shell의 Submodel 목록
                url = urljoin(self.base_url, f"/shells/{shell_id}/submodels")
            else:
                # 전체 Submodel 목록
                url = urljoin(self.base_url, "/submodels")

            response = await self.client.get(url)
            response.raise_for_status()

            submodels_data = response.json()

            if isinstance(submodels_data, dict):
                return submodels_data.get("result", submodels_data.get("submodels", []))
            elif isinstance(submodels_data, list):
                return submodels_data
            else:
                return []

        except httpx.HTTPStatusError as e:
            raise AASConnectionError(f"HTTP error while listing submodels: {e.response.status_code}") from e
        except Exception as e:
            raise AASConnectionError(f"Failed to list submodels: {e}") from e

    async def get_submodel_property(self,
                                   submodel_id: str,
                                   property_path: str,
                                   shell_id: str = None) -> Any:
        """Submodel의 특정 Property 값 조회

        Note: shell_id는 호환성을 위해 남겨둠, 실제로는 사용하지 않음
        서브모델에 직접 접근하여 element 값을 가져옴
        """

        await self._ensure_client()

        try:
            # ID 인코딩
            encoded_submodel = self._encode_id(submodel_id)

            # 서브모델 직접 조회 (Shell을 거치지 않음)
            url = urljoin(self.base_url + "/", f"submodels/{encoded_submodel}")

            logger.debug(f"Requesting submodel: {url}")
            response = await self.client.get(url)
            response.raise_for_status()

            # 서브모델 데이터 파싱
            submodel_data = response.json()
            submodel_elements = submodel_data.get('submodelElements', [])

            # element_id(property_path)와 일치하는 엘리먼트 찾기
            for element in submodel_elements:
                if element.get('idShort') == property_path:
                    if element.get('modelType') == 'Property' and 'value' in element:
                        logger.debug(f"✅ Found element {property_path} with value: {element['value']}")
                        return element['value']
                    elif element.get('modelType') == 'SubmodelElementList':
                        # List 타입의 경우 value 배열 반환
                        values = element.get('value', [])
                        return [v.get('value') for v in values if 'value' in v]
                    else:
                        logger.warning(f"Element {property_path} is not a Property or has no value field")
                        return None

            logger.warning(f"Element {property_path} not found in submodel {submodel_id}")
            return None

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                raise AASConnectionError(
                    f"Property not found: {property_path} in submodel {submodel_id}"
                ) from e
            raise AASConnectionError(
                f"HTTP error while getting property {property_path}: {e.response.status_code}"
            ) from e
        except Exception as e:
            raise AASConnectionError(f"Failed to get property {property_path}: {e}") from e

    async def health_check(self) -> bool:
        """AAS 서버 연결 상태 확인"""

        await self._ensure_client()

        try:
            # 기본적인 엔드포인트 호출로 연결 확인
            test_endpoints = ["/health", "/shells", "/"]

            for endpoint in test_endpoints:
                try:
                    url = urljoin(self.base_url, endpoint)
                    response = await self.client.get(url)

                    if response.status_code < 500:  # 500대 에러가 아니면 연결은 됨
                        logger.info(f"✅ AAS server is accessible at {self.base_url}")
                        return True

                except httpx.RequestError:
                    continue

            return False

        except Exception as e:
            logger.error(f"AAS health check failed: {e}")
            return False