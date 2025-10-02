"""
Runtime Execution Exceptions
Runtime 실행 중 발생하는 예외들
"""


class RuntimeExecutionError(Exception):
    """Runtime 실행 실패"""
    pass


class StageExecutionError(RuntimeExecutionError):
    """Stage 실행 실패"""
    pass


class StageGateFailureError(RuntimeExecutionError):
    """Stage-Gate 검증 실패"""
    pass


class AASConnectionError(RuntimeExecutionError):
    """AAS 서버 연결 실패"""
    pass


class SimulationExecutionError(RuntimeExecutionError):
    """시뮬레이션 실행 실패"""
    pass


class ManifestParsingError(RuntimeExecutionError):
    """메니페스트 파싱 실패"""
    pass


class WorkDirectoryError(RuntimeExecutionError):
    """작업 디렉터리 오류"""
    pass