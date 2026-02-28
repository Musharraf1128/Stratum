from stratum.core.execution_engine import ExecutionEngine
from stratum.core.workflow import WorkflowGraph
from stratum.storage.run_store import RunStore


class ReplayEngine:
    def __init__(self, workflow: WorkflowGraph, run_store: RunStore):
        self.workflow = workflow
        self.run_store = run_store
        self.execution_engine = ExecutionEngine(workflow)

    def replay(self, original_run_id: str) -> str:
        original_run = self.run_store.get_run(original_run_id)
        if not original_run:
            raise ValueError(f"Run '{original_run_id}' not found")

        new_run = self.execution_engine.execute(original_run.input_data)
        self.run_store.save_run(new_run)

        return new_run.run_id
