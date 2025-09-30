"""
AAS Server REST API Client
AAS 서버와의 통신을 담당하는 클라이언트
"""
import asyncio
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
        """Submodel의 특정 Property 값 조회"""

        await self._ensure_client()

        try:
            # Property 경로 구성
            if shell_id:
                url = urljoin(
                    self.base_url,
                    f"/shells/{shell_id}/submodels/{submodel_id}/submodel-elements/{property_path}/value"
                )
            else:
                url = urljoin(
                    self.base_url,
                    f"/submodels/{submodel_id}/submodel-elements/{property_path}/value"
                )

            response = await self.client.get(url)
            response.raise_for_status()

            # Content-Type에 따라 응답 처리
            content_type = response.headers.get("content-type", "")

            if "application/json" in content_type:
                return response.json()
            else:
                return response.text

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