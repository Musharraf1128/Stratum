from __future__ import annotations

from typing import Optional

from stratum.core.execution_engine import ExecutionEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.run_store import RunStore


class ReplayEngine:
    def __init__(
        self,
        workflow: WorkflowGraph,
        run_store: RunStore,
        api_key: Optional[str] = None,
        provider: str = "openai",
        model: Optional[str] = None,
    ):
        self.workflow = workflow
        self.run_store = run_store
        self.api_key = api_key
        self.execution_engine = ExecutionEngine(workflow, api_key=api_key, provider=provider, model=model)

    def replay(self, original_run_id: str, api_key: Optional[str] = None) -> str:
        original_run = self.run_store.get_run(original_run_id)
        if not original_run:
            raise ValueError(f"Run '{original_run_id}' not found")

        # Use provided key, or fall back to engine-level key
        if api_key:
            self.execution_engine.api_key = api_key

        new_run = self.execution_engine.execute(original_run.input_data)
        self.run_store.save_run(new_run)

        return new_run.run_id
