from __future__ import annotations

import networkx as nx


class WorkflowGraph:
    def __init__(self, name: str = "workflow"):
        self.name = name
        self.graph = nx.DiGraph()

    def add_agent(self, agent_name: str) -> WorkflowGraph:
        if agent_name not in self.graph:
            self.graph.add_node(agent_name)
        return self

    def connect(self, from_agent: str, to_agent: str) -> WorkflowGraph:
        if from_agent not in self.graph:
            raise ValueError(
                f"Agent '{from_agent}' not found in workflow. Add it first with add_agent()."
            )
        if to_agent not in self.graph:
            raise ValueError(
                f"Agent '{to_agent}' not found in workflow. Add it first with add_agent()."
            )

        self.graph.add_edge(from_agent, to_agent)

        if not nx.is_directed_acyclic_graph(self.graph):
            self.graph.remove_edge(from_agent, to_agent)
            raise ValueError(
                f"Adding edge from '{from_agent}' to '{to_agent}' would create a cycle"
            )

        return self

    def get_execution_order(self) -> list[str]:
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError(
                "Workflow contains cycles - cannot determine execution order"
            )
        return list(nx.topological_sort(self.graph))

    def get_dependencies(self, agent_name: str) -> list[str]:
        if agent_name not in self.graph:
            return []
        return list(self.graph.predecessors(agent_name))

    def get_dependents(self, agent_name: str) -> list[str]:
        if agent_name not in self.graph:
            return []
        return list(self.graph.successors(agent_name))

    def get_nodes(self) -> list[str]:
        return list(self.graph.nodes())

    def get_edges(self) -> list[tuple[str, str]]:
        return list(self.graph.edges())

    def validate(self) -> bool:
        if not nx.is_directed_acyclic_graph(self.graph):
            raise ValueError("Workflow contains cycles")
        return True
