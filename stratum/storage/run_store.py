from abc import ABC, abstractmethod
from typing import Optional

from stratum.core.models import ExecutionRun


class RunStore(ABC):
    @abstractmethod
    def save_run(self, run: ExecutionRun) -> None:
        pass

    @abstractmethod
    def get_run(self, run_id: str) -> Optional[ExecutionRun]:
        pass

    @abstractmethod
    def list_runs(self) -> list[ExecutionRun]:
        pass

    @abstractmethod
    def delete_run(self, run_id: str) -> bool:
        pass
