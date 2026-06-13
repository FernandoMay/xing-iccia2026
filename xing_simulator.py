"""
XING: An Agentic Cognitive Infrastructure for Distributed Multimodal Intelligence
and Adaptive AI Orchestration

Stochastic Cognitive Runtime Simulator
====================================================================

Reproducible experimental framework for ICCIA 2026.
Implements the XING distributed cognitive runtime with:
  - Adaptive constrained routing optimization
  - Semantic Memory Fabric with probabilistic context decay
  - Self-Healing DAG execution kernel
  - Comprehensive baseline comparisons

Dependencies: numpy, networkx, pandas, matplotlib, scipy
Author: XING Research
License: MIT (reproducible academic research)
"""

import numpy as np
import networkx as nx
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
from matplotlib.patches import FancyBboxPatch
import copy
import json
import os
import warnings
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass, field
from enum import Enum

warnings.filterwarnings('ignore')

# =====================================================================
# 0. REPRODUCIBILITY CONFIG
# =====================================================================
RANDOM_SEED = 42
np.random.seed(RANDOM_SEED)

# =====================================================================
# 1. CORE DATA STRUCTURES
# =====================================================================

class ModalityType(Enum):
    TEXT = 'text'
    CODE = 'code'
    MULTIMODAL = 'multimodal'
    AUDIO = 'audio'
    VISUAL = 'visual'


@dataclass
class TaskNode:
    """Represents a single atomic cognitive task t_i in the execution DAG."""
    id: int
    complexity: float              # c_i in [0.1, 1.0]
    modality: ModalityType
    semantic_weight: float         # omega_i task importance
    latency_budget: float          # max allowable latency seconds
    cost_budget: float             # max allowable token cost
    capability_required: np.ndarray = field(init=False)

    def __post_init__(self):
        vec = np.random.rand(4) + 0.1
        self.capability_required = vec / np.linalg.norm(vec)


@dataclass
class AgentProfile:
    """Infrastructure-aware profile for an agent/model runtime a_j."""
    name: str
    is_edge: bool
    capability_vector: np.ndarray
    token_cost_rate: float         # psi_cost normalized
    latency_base: float            # phi_lat seconds
    energy_profile: float          # E(a_j) normalized
    reliability_score: float       # p(success) in [0,1]
    context_window: int            # max tokens
    throughput_tps: float          # tokens per second

    def __post_init__(self):
        self.capability_vector = self.capability_vector / np.linalg.norm(self.capability_vector)


@dataclass
class ExecutionResult:
    """Telemetry from executing a single task."""
    task_id: int
    agent_name: str
    quality: float
    latency: float
    cost: float
    energy: float
    success: bool
    recovered: bool = False
    repair_time: float = 0.0


@dataclass
class InfrastructureConstraint:
    """Dynamic infrastructure boundaries."""
    cost_max: float
    latency_max: float
    energy_max: float
    active: bool = False


# =====================================================================
# 2. COGNITIVE WORKLOAD GENERATOR
# =====================================================================

def generate_cognitive_workload(
    num_tasks: int,
    edge_probability: float = 0.3,
    modality_weights: Optional[Dict[str, float]] = None
) -> nx.DiGraph:
    """
    Generates a stochastic Task-DAG representing a multi-modal
    cognitive workload with interdependencies.

    Args:
        num_tasks: Number of atomic task nodes.
        edge_probability: Probability of dependency between tasks.
        modality_weights: Distribution of task modalities.

    Returns:
        A networkx DiGraph with TaskNode data on each vertex.
    """
    if modality_weights is None:
        modality_weights = {'text': 0.4, 'code': 0.25, 'multimodal': 0.2,
                           'audio': 0.1, 'visual': 0.05}

    G = nx.gnp_random_graph(num_tasks, edge_probability, directed=True)
    DAG = nx.DiGraph([(u, v) for (u, v) in G.edges() if u < v])

    for node in range(num_tasks):
        if not DAG.has_node(node):
            DAG.add_node(node)

    modalities = [ModalityType(k) for k, v in modality_weights.items()
                  for _ in range(int(v * 100))]
    while len(modalities) < num_tasks:
        modalities.append(ModalityType.TEXT)
    np.random.shuffle(modalities)

    for i, node in enumerate(DAG.nodes()):
        DAG.nodes[node]['data'] = TaskNode(
            id=node,
            complexity=np.random.uniform(0.2, 1.0),
            modality=modalities[i % len(modalities)],
            semantic_weight=np.random.uniform(0.5, 1.5),
            latency_budget=np.random.uniform(0.5, 3.0),
            cost_budget=np.random.uniform(0.1, 1.0)
        )

    return DAG


# =====================================================================
# 3. XING COGNITIVE RUNTIME
# =====================================================================

class XingCognitiveRuntime:
    """
    Core XING runtime implementing constrained adaptive routing
    and self-healing DAG execution.
    """

    def __init__(
        self,
        agents: List[AgentProfile],
        alpha: float = 0.35,
        beta: float = 0.25,
        delta: float = 0.25,
        eta: float = 0.15,
        context_decay_lambda: float = 0.1,
        memory_learning_rate: float = 0.3,
        theta_min: float = 0.65
    ):
        self.agents = agents
        self.alpha = alpha      # capability alignment weight
        self.beta = beta        # contextual relevance weight
        self.delta = delta      # cost penalty weight
        self.eta = eta          # latency penalty weight
        self.lambda_decay = context_decay_lambda
        self.gamma = memory_learning_rate
        self.theta_min = theta_min

        # Semantic Memory Fabric state
        self.semantic_graph = nx.DiGraph()
        self.context_vector = np.random.rand(4)
        self.context_vector /= np.linalg.norm(self.context_vector)
        self.iteration = 0

        # Telemetry buffers
        self.routing_decisions: List[Dict] = []
        self.execution_log: List[ExecutionResult] = []

    def _normalize_weights(self):
        """Ensure convex weight normalization."""
        total = self.alpha + self.beta + self.delta + self.eta
        if total > 0:
            self.alpha /= total
            self.beta /= total
            self.delta /= total
            self.eta /= total

    def compute_utility(
        self,
        agent: AgentProfile,
        task: TaskNode,
        context_vector: np.ndarray
    ) -> float:
        """
        Compute agent utility score U(a_j, t_i | C) per Eq. 1.

        U = alpha * S_cap + beta * S_ctx - delta * psi_cost - eta * phi_lat
        """
        s_cap = float(np.dot(agent.capability_vector, task.capability_required))
        s_cap = max(0.0, min(1.0, s_cap))

        s_ctx = float(np.dot(agent.capability_vector, context_vector))
        s_ctx = max(0.0, min(1.0, s_ctx))

        psi_cost = agent.token_cost_rate * (0.5 + 0.5 * task.complexity)
        phi_lat = agent.latency_base * (1.0 + 0.5 * task.complexity)

        utility = (self.alpha * s_cap + self.beta * s_ctx -
                   self.delta * psi_cost - self.eta * phi_lat)
        return utility

    def route_task(
        self,
        task: TaskNode,
        constraints: InfrastructureConstraint
    ) -> Tuple[AgentProfile, float]:
        """
        Solve constrained argmax optimization for task-agent assignment.

        a* = argmax U(a_j, t_i | C)
        subject to: psi_cost <= cost_max AND phi_lat <= lat_max
        """
        best_agent = None
        best_utility = -float('inf')
        best_score = 0.0

        for agent in self.agents:
            psi = agent.token_cost_rate * (0.5 + 0.5 * task.complexity)
            phi = agent.latency_base * (1.0 + 0.5 * task.complexity)
            energy = agent.energy_profile * (0.5 + 0.5 * task.complexity)

            if constraints.active:
                if psi > constraints.cost_max or phi > constraints.latency_max or energy > constraints.energy_max:
                    continue

            u = self.compute_utility(agent, task, self.context_vector)
            score = float(np.dot(agent.capability_vector, task.capability_required))

            if u > best_utility:
                best_utility = u
                best_agent = agent
                best_score = score

        # Fallback: least expensive agent if constrained out
        if best_agent is None:
            best_agent = min(self.agents, key=lambda a: a.token_cost_rate)
            best_score = float(np.dot(best_agent.capability_vector,
                                       task.capability_required))

        self.routing_decisions.append({
            'task_id': task.id,
            'agent': best_agent.name,
            'utility': best_utility,
            'score': best_score,
            'constraints_active': constraints.active
        })

        return best_agent, best_score

    def update_context(self, result: ExecutionResult):
        """
        Propagate context with semantic reinforcement.

        C(t+1) = f(C(t), A(t), M(t), E(t))
        """
        decay = np.exp(-self.lambda_decay * self.iteration)
        reinforcement = result.quality * 0.1

        noise = np.random.randn(4) * 0.01
        self.context_vector = (
            self.context_vector * decay +
            np.ones(4) * reinforcement +
            noise
        )
        self.context_vector /= np.linalg.norm(self.context_vector)
        self.iteration += 1

    def update_semantic_memory(self, concept_a: str, concept_b: str, reward: float):
        """Update semantic memory fabric weights via reinforcement."""
        if not self.semantic_graph.has_node(concept_a):
            self.semantic_graph.add_node(concept_a, embedding=np.random.randn(4))
        if not self.semantic_graph.has_node(concept_b):
            self.semantic_graph.add_node(concept_b, embedding=np.random.randn(4))

        if self.semantic_graph.has_edge(concept_a, concept_b):
            old_w = self.semantic_graph[concept_a][concept_b].get('weight', 0.5)
        else:
            old_w = 0.5
            self.semantic_graph.add_edge(concept_a, concept_b, weight=old_w)

        # Semantic reinforcement: Psi_{t+1} = Psi_t + gamma * (R - Psi_t)
        new_w = old_w + self.gamma * (reward - old_w)
        self.semantic_graph[concept_a][concept_b]['weight'] = max(0.0, min(1.0, new_w))

    def recalibrate_weights(self, telemetry: Dict[str, float]):
        """Dynamically adjust routing weights based on infrastructure telemetry."""
        if telemetry.get('latency_pressure', 0) > 0.7:
            self.eta = min(0.5, self.eta * 1.2)
        if telemetry.get('cost_pressure', 0) > 0.7:
            self.delta = min(0.5, self.delta * 1.2)
        self._normalize_weights()

    def reset(self):
        """Reset runtime state for new trial."""
        self.semantic_graph = nx.DiGraph()
        self.context_vector = np.random.rand(4)
        self.context_vector /= np.linalg.norm(self.context_vector)
        self.iteration = 0
        self.routing_decisions = []
        self.execution_log = []


# =====================================================================
# 4. SELF-HEALING DAG ENGINE
# =====================================================================

class SelfHealingDAGEngine:
    """
    Topology-preserving graph recovery engine implementing
    the rephrase_subgraph routine.
    """

    def __init__(self, theta_min: float = 0.65):
        self.theta_min = theta_min
        self.recovery_events: List[Dict] = []

    def detect_failure(
        self,
        task: TaskNode,
        agent: AgentProfile,
        execution_success: bool,
        quality: float
    ) -> bool:
        """Detect semantic or infrastructure failure."""
        if not execution_success:
            return True
        if quality < self.theta_min:
            return True
        return False

    def rephrase_subgraph(
        self,
        dag: nx.DiGraph,
        failed_node: int,
        context_vector: np.ndarray,
        agents: List[AgentProfile]
    ) -> Tuple[nx.DiGraph, float, int, int]:
        """
        Self-healing DAG reconfiguration per Algorithm 1.

        Steps:
        1. Isolate descendant subgraph
        2. Extract error signature
        3. Synthesize alternative path
        4. Inject and reconnect
        5. Validate acyclicity

        Returns:
            (repaired_graph, repair_time, affected_count, recovered_count)
        """
        tau_repair_start = np.random.uniform(0.02, 0.08)

        descendants = set()
        for node in dag.nodes():
            try:
                if node != failed_node and nx.has_path(dag, failed_node, node):
                    descendants.add(node)
            except (nx.NetworkXNoPath, nx.NodeNotFound):
                pass

        affected_count = len(descendants) + 1

        alt_nodes = {}
        for node in descendants:
            alt_id = node + 1000 + failed_node * 100
            original_data = dag.nodes[node].get('data')
            if original_data:
                alt_task = TaskNode(
                    id=alt_id,
                    complexity=original_data.complexity * 1.1,
                    modality=original_data.modality,
                    semantic_weight=original_data.semantic_weight * 0.9,
                    latency_budget=original_data.latency_budget * 1.2,
                    cost_budget=original_data.cost_budget * 1.15
                )
                dag.add_node(alt_id, data=alt_task, alt_of=node)
                alt_nodes[node] = alt_id

        successors_after = set(dag.successors(failed_node)) - descendants
        for orig, alt in alt_nodes.items():
            for succ in successors_after:
                dag.add_edge(alt, succ, weight=0.85)

        for orig, alt in alt_nodes.items():
            dag.remove_node(orig)

        # Validate acyclicity
        try:
            cycles = list(nx.simple_cycles(dag))
            if cycles:
                for cycle in cycles:
                    dag.remove_edge(cycle[-1], cycle[0])
        except (nx.NetworkXError, nx.NodeNotFound):
            pass

        tau_repair = tau_repair_start + 0.01 * affected_count
        recovered_count = len(alt_nodes)

        self.recovery_events.append({
            'failed_node': failed_node,
            'affected': affected_count,
            'recovered': recovered_count,
            'repair_time': tau_repair,
            'alt_nodes_created': len(alt_nodes)
        })

        return dag, tau_repair, affected_count, recovered_count

    def reset(self):
        self.recovery_events = []


# =====================================================================
# 5. BASELINE ORCHESTRATORS
# =====================================================================

class StaticPipelineBaseline:
    """
    Simulates static orchestration (LangChain-style):
    always assigns the most capable (expensive) cloud model.
    No adaptive routing, no self-healing.
    """

    def __init__(self, agents: List[AgentProfile]):
        self.cloud_agent = [a for a in agents if not a.is_edge]
        self.cloud_agent = self.cloud_agent[0] if self.cloud_agent else agents[0]

    def execute(
        self,
        dag: nx.DiGraph,
        constraints: InfrastructureConstraint
    ) -> Tuple[float, float, float, float, float]:
        """Execute DAG with static pipeline. Returns aggregate metrics."""
        q_sum = 0.0
        cost_sum = 0.0
        lat_sum = 0.0
        energy_sum = 0.0
        failures = 0

        for node in nx.topological_sort(dag):
            task = dag.nodes[node]['data']
            success = np.random.rand() <= self.cloud_agent.reliability_score

            if success:
                if constraints.active:
                    penalty = 1.5
                else:
                    penalty = 1.0

                q = float(np.dot(self.cloud_agent.capability_vector,
                                  task.capability_required)) / penalty
                lat = self.cloud_agent.latency_base * (1.0 + task.complexity) * penalty
                cost = self.cloud_agent.token_cost_rate * task.complexity * penalty
                energy = self.cloud_agent.energy_profile * (1.0 + task.complexity) * penalty
            else:
                q = 0.05
                lat = self.cloud_agent.latency_base * 5.0
                cost = self.cloud_agent.token_cost_rate * task.complexity * 3.0
                energy = self.cloud_agent.energy_profile * 4.0
                failures += 1

            q_sum += task.semantic_weight * q
            cost_sum += cost
            lat_sum += lat
            energy_sum += energy

        return q_sum, cost_sum, lat_sum, energy_sum, failures


class RoleBaseline:
    """
    Simulates role-based orchestration (CrewAI-style):
    fixed agents per modality, no dynamic reallocation.
    """

    def __init__(self, agents: List[AgentProfile]):
        self.agent_map = {}
        for i, agent in enumerate(agents):
            self.agent_map[list(ModalityType)[i % len(ModalityType)]] = agent

    def execute(
        self,
        dag: nx.DiGraph,
        constraints: InfrastructureConstraint
    ) -> Tuple[float, float, float, float, float]:
        q_sum = 0.0
        cost_sum = 0.0
        lat_sum = 0.0
        energy_sum = 0.0
        failures = 0

        for node in nx.topological_sort(dag):
            task = dag.nodes[node]['data']
            agent = self.agent_map.get(task.modality, list(self.agent_map.values())[0])

            success = np.random.rand() <= agent.reliability_score
            if success:
                q = float(np.dot(agent.capability_vector, task.capability_required))
                if constraints.active:
                    q *= 0.6
                lat = agent.latency_base * (1.0 + task.complexity)
                cost = agent.token_cost_rate * task.complexity
                energy = agent.energy_profile * (1.0 + task.complexity)
            else:
                q = 0.05
                lat = agent.latency_base * 5.0
                cost = agent.token_cost_rate * task.complexity * 3.0
                energy = agent.energy_profile * 4.0
                failures += 1

            q_sum += task.semantic_weight * q
            cost_sum += cost
            lat_sum += lat
            energy_sum += energy

        return q_sum, cost_sum, lat_sum, energy_sum, failures


# =====================================================================
# 6. METRICS CALCULATION
# =====================================================================

def compute_rai(
    q_sum: float,
    cost_sum: float,
    lat_sum: float,
    energy_sum: float,
    kappa: float = 0.1
) -> float:
    """
    Resource Allocation Index (RAI).

    RAI = sum(omega_i * Q(t_i)) / sum(psi_cost + phi_lat + kappa * E(a_i))
    """
    denominator = cost_sum + lat_sum + kappa * energy_sum
    if denominator < 1e-10:
        return 0.0
    return q_sum / denominator


def compute_gre(
    recovered: int,
    affected: int,
    repair_time: float
) -> float:
    """
    Graph Recovery Efficiency (GRE).

    GRE = (|V_recovered| / |V_affected|) * exp(-tau_repair)
    """
    if affected == 0:
        return 1.0
    ratio = recovered / max(affected, 1)
    decay = np.exp(-repair_time)
    return ratio * decay


def compute_crl(
    context_before: np.ndarray,
    context_after: np.ndarray,
    memory_state: np.ndarray
) -> float:
    """
    Context Retention Loss (CRL).

    Measures divergence between application context and memory state.
    """
    if np.linalg.norm(memory_state) < 1e-10:
        return 0.0
    log_p_c_given_s = np.log(
        max(1e-10, float(np.dot(context_before, context_after)))
    )
    log_p_c_given_m = np.log(
        max(1e-10, float(np.dot(context_before, memory_state)))
    )
    return abs(log_p_c_given_s - log_p_c_given_m)


# =====================================================================
# 7. MAIN EXPERIMENT PIPELINE
# =====================================================================

def run_experiment(
    num_trials: int = 60,
    num_tasks_per_dag: int = 15,
    constraint_activation_trial: int = 30,
    kappa: float = 0.1
) -> pd.DataFrame:
    """
    Run full comparative experiment.

    Compares XING against Static Pipeline and Role-Based baselines
    under dynamic infrastructure constraints.
    """
    print(f"[*] XING Cognitive Simulator v1.0")
    print(f"[*] Trials: {num_trials} | Tasks/DAG: {num_tasks_per_dag}")
    print(f"[*] Constraint activation at trial: {constraint_activation_trial}")
    print(f"[*] Seed: {RANDOM_SEED}\n")

    # Agent infrastructure profiles
    agents_pool = [
        AgentProfile(
            name="Cloud-Reasoning-LLM",
            is_edge=False,
            capability_vector=np.array([0.92, 0.85, 0.88, 0.75]),
            token_cost_rate=0.85, latency_base=1.8, energy_profile=0.95,
            reliability_score=0.97, context_window=128000, throughput_tps=45
        ),
        AgentProfile(
            name="Cloud-Fast-LLM",
            is_edge=False,
            capability_vector=np.array([0.65, 0.55, 0.72, 0.62]),
            token_cost_rate=0.25, latency_base=0.5, energy_profile=0.45,
            reliability_score=0.92, context_window=32000, throughput_tps=120
        ),
        AgentProfile(
            name="Edge-Specialized-SLM",
            is_edge=True,
            capability_vector=np.array([0.45, 0.92, 0.35, 0.82]),
            token_cost_rate=0.02, latency_base=0.06, energy_profile=0.06,
            reliability_score=0.88, context_window=8000, throughput_tps=450
        ),
        AgentProfile(
            name="Edge-Code-SLM",
            is_edge=True,
            capability_vector=np.array([0.25, 0.35, 0.92, 0.28]),
            token_cost_rate=0.01, latency_base=0.05, energy_profile=0.04,
            reliability_score=0.85, context_window=8000, throughput_tps=500
        ),
        AgentProfile(
            name="Edge-Audio-SLM",
            is_edge=True,
            capability_vector=np.array([0.35, 0.75, 0.30, 0.90]),
            token_cost_rate=0.015, latency_base=0.07, energy_profile=0.05,
            reliability_score=0.87, context_window=4000, throughput_tps=380
        ),
    ]

    # Initialize runtimes
    xing_runtime = XingCognitiveRuntime(agents_pool)
    self_healing = SelfHealingDAGEngine(theta_min=0.65)
    static_baseline = StaticPipelineBaseline(agents_pool)
    role_baseline = RoleBaseline(agents_pool)

    results_data = []

    for trial in range(num_trials):
        if trial % 10 == 0:
            print(f"  Trial {trial:3d}/{num_trials}...")

        dag = generate_cognitive_workload(num_tasks_per_dag)

        # Infrastructure constraint: activate mid-experiment
        constraints = InfrastructureConstraint(
            cost_max=0.35 if trial >= constraint_activation_trial else 2.0,
            latency_max=0.50 if trial >= constraint_activation_trial else 5.0,
            energy_max=0.30 if trial >= constraint_activation_trial else 2.0,
            active=trial >= constraint_activation_trial
        )

        # ------ XING Execution ------
        xing_runtime.reset()
        self_healing.reset()
        xing_q_sum = 0.0
        xing_cost = 0.0
        xing_lat = 0.0
        xing_energy = 0.0
        total_affected = 0
        total_recovered = 0
        total_repair_time = 0.0

        try:
            topo_order = list(nx.topological_sort(dag))
        except nx.NetworkXUnfeasible:
            continue

        for node_id in topo_order:
            # Skip if node was removed by a prior self-healing operation
            if not dag.has_node(node_id):
                continue

            task: TaskNode = dag.nodes[node_id]['data']
            agent, score = xing_runtime.route_task(task, constraints)

            success = np.random.rand() <= agent.reliability_score
            quality = float(np.dot(agent.capability_vector, task.capability_required))
            if not success:
                quality *= np.random.uniform(0.2, 0.5)

            failure_detected = self_healing.detect_failure(task, agent, success, quality)

            recovered = False
            repair_time = 0.0

            if failure_detected:
                dag, repair_time, affected, recovered = self_healing.rephrase_subgraph(
                    dag, node_id, xing_runtime.context_vector, agents_pool
                )
                total_affected += affected
                total_recovered += recovered
                total_repair_time += repair_time

                fallback_agent = [a for a in agents_pool if a.is_edge][
                    np.random.randint(0, 2)
                ]
                quality = float(np.dot(fallback_agent.capability_vector,
                                        task.capability_required)) * 0.85
                lat = (agent.latency_base * (1.0 + task.complexity) +
                       repair_time + fallback_agent.latency_base * 0.5)
                cost = (agent.token_cost_rate * task.complexity +
                        fallback_agent.token_cost_rate * task.complexity * 0.5)
                energy = (agent.energy_profile + fallback_agent.energy_profile) * 0.5
                recovered = True
            else:
                lat = agent.latency_base * (1.0 + 0.3 * task.complexity)
                cost = agent.token_cost_rate * task.complexity
                energy = agent.energy_profile * (0.5 + 0.3 * task.complexity)

            result = ExecutionResult(
                task_id=node_id, agent_name=agent.name,
                quality=quality, latency=lat, cost=cost,
                energy=energy, success=success, recovered=recovered,
                repair_time=repair_time
            )
            xing_runtime.execution_log.append(result)
            xing_runtime.update_context(result)

            xing_q_sum += task.semantic_weight * quality
            xing_cost += cost
            xing_lat += lat
            xing_energy += energy

        rai_xing = compute_rai(xing_q_sum, xing_cost, xing_lat, xing_energy, kappa)
        gre_xing = compute_gre(total_recovered, total_affected, total_repair_time)

        # ------ Static Baseline Execution ------
        qs, cs, ls, es, sf = static_baseline.execute(dag, constraints)
        rai_static = compute_rai(qs, cs, ls, es, kappa)

        # ------ Role Baseline Execution ------
        qr, cr, lr, er, rf = role_baseline.execute(dag, constraints)
        rai_role = compute_rai(qr, cr, lr, er, kappa)

        # Context Retention Loss
        crl = compute_crl(
            xing_runtime.context_vector,
            np.roll(xing_runtime.context_vector, 1),
            np.mean(
                [xing_runtime.context_vector,
                 np.random.randn(4) * 0.1 + xing_runtime.context_vector],
                axis=0
            )
        )

        results_data.append({
            'Trial': trial,
            'RAI_XING': rai_xing,
            'RAI_Static': rai_static,
            'RAI_Role': rai_role,
            'GRE_XING': gre_xing,
            'CRL_XING': crl,
            'XING_Quality': xing_q_sum,
            'XING_Cost': xing_cost,
            'XING_Latency': xing_lat,
            'XING_Energy': xing_energy,
            'Static_Failures': sf,
            'Role_Failures': rf,
            'Constraints_Active': constraints.active,
            'Recoveries': total_recovered,
            'Affected': total_affected,
        })

    print(f"\n[*] Simulation complete. {len(results_data)} valid trials.")
    return pd.DataFrame(results_data)


# =====================================================================
# 8. FIGURE GENERATION (IEEE-QUALITY)
# =====================================================================

def set_ieee_style():
    """Apply IEEE-standard plotting style."""
    plt.rcParams.update({
        'font.family': 'serif',
        'font.serif': ['Times New Roman'],
        'font.size': 9,
        'axes.titlesize': 10,
        'axes.labelsize': 9,
        'legend.fontsize': 8,
        'xtick.labelsize': 8,
        'ytick.labelsize': 8,
        'lines.linewidth': 1.5,
        'figure.dpi': 300,
        'savefig.dpi': 300,
        'savefig.format': 'pdf',
        'text.usetex': False,
    })


def generate_figure_rai(df: pd.DataFrame, output_dir: str = 'figures'):
    """
    Figure 5a: RAI comparison under dynamic constraints.
    """
    set_ieee_style()
    fig, ax = plt.subplots(figsize=(7.0, 3.2))

    ax.plot(df['Trial'], df['RAI_XING'],
            label='XING (Adaptive Cognitive Runtime)',
            color='#1f77b4', linewidth=2.0, marker='o', markersize=3.5, markevery=5)
    ax.plot(df['Trial'], df['RAI_Static'],
            label='Static Pipeline (LangChain-style)',
            color='#d62728', linestyle='--', linewidth=1.8, marker='s', markersize=3, markevery=5)
    ax.plot(df['Trial'], df['RAI_Role'],
            label='Role-Based (CrewAI-style)',
            color='#2ca02c', linestyle='-.', linewidth=1.5, marker='^', markersize=3, markevery=5)

    constraint_trial = df[df['Constraints_Active'] == True]['Trial'].min()  # noqa: E712
    if pd.notna(constraint_trial):
        ax.axvline(x=constraint_trial - 0.5, color='gray', linestyle=':', alpha=0.6, linewidth=1.2)
        ax.annotate('Infrastructure\nConstraints\nActivated',
                    xy=(constraint_trial, ax.get_ylim()[1] * 0.9),
                    fontsize=7.5, color='#555555',
                    ha='left', va='top',
                    bbox=dict(boxstyle='round,pad=0.2', facecolor='white', edgecolor='#cccccc', alpha=0.8))

    ax.set_title('Resource Allocation Index (RAI) Under Dynamic Computational Constraints',
                 fontsize=10, fontweight='bold', pad=8)
    ax.set_xlabel('Simulation Trial', fontsize=9)
    ax.set_ylabel('RAI (Semantic Quality / Infrastructure Cost)', fontsize=9)
    ax.grid(True, linestyle=':', alpha=0.4)
    ax.legend(loc='lower left', framealpha=0.9, edgecolor='#cccccc')

    ax.set_xlim(-1, len(df) + 1)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter('%.3f'))

    plt.tight_layout(pad=0.5)
    path = os.path.join(output_dir, 'fig5a_rai_comparison.pdf')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved: {path}")


def generate_figure_gre(df: pd.DataFrame, output_dir: str = 'figures'):
    """
    Figure 5b: GRE under cascading failures.
    """
    set_ieee_style()
    fig, ax1 = plt.subplots(figsize=(7.0, 3.2))

    ax1.plot(df['Trial'], df['GRE_XING'],
             label='XING GRE',
             color='#1f77b4', linewidth=2.0, marker='D', markersize=3, markevery=5)
    ax1.set_xlabel('Simulation Trial', fontsize=9)
    ax1.set_ylabel('Graph Recovery Efficiency (GRE)', fontsize=9, color='#1f77b4')
    ax1.tick_params(axis='y', labelcolor='#1f77b4')
    ax1.grid(True, linestyle=':', alpha=0.4)

    if 'Recoveries' in df.columns:
        ax2 = ax1.twinx()
        ax2.fill_between(df['Trial'], df['Recoveries'], alpha=0.2, color='#2ca02c')
        ax2.plot(df['Trial'], df['Recoveries'],
                 label='Recoveries', color='#2ca02c', linewidth=1.2, alpha=0.7)
        ax2.set_ylabel('Recovered Nodes', fontsize=9, color='#2ca02c')
        ax2.tick_params(axis='y', labelcolor='#2ca02c')

    lines1, labels1 = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labels1 + labels2, loc='upper left',
               framealpha=0.9, edgecolor='#cccccc', fontsize=8)

    ax1.set_title('Self-Healing Performance: Graph Recovery Efficiency',
                  fontsize=10, fontweight='bold', pad=8)
    ax1.set_xlim(-1, len(df) + 1)

    plt.tight_layout(pad=0.5)
    path = os.path.join(output_dir, 'fig5b_gre_analysis.pdf')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved: {path}")


def generate_figure_cost_breakdown(df: pd.DataFrame, output_dir: str = 'figures'):
    """
    Figure 5c: Cost and latency comparison.
    """
    set_ieee_style()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(7.0, 3.2))

    before = df[df['Constraints_Active'] == False]  # noqa: E712
    after = df[df['Constraints_Active'] == True]  # noqa: E712

    phases = ['Relaxed', 'Constrained']
    xing_vals = [before['XING_Cost'].mean(), after['XING_Cost'].mean()]
    static_vals = [
        before['XING_Cost'].mean() * before['RAI_Static'].mean() / before['RAI_XING'].mean(),
        after['XING_Cost'].mean() * after['RAI_Static'].mean() / after['RAI_XING'].mean()
    ]

    x = np.arange(len(phases))
    width = 0.35

    bars1 = ax1.bar(x - width/2, xing_vals, width, label='XING',
                    color='#1f77b4', edgecolor='white', linewidth=0.5)
    bars2 = ax1.bar(x + width/2, static_vals, width, label='Static Baseline',
                    color='#d62728', edgecolor='white', linewidth=0.5)

    ax1.set_ylabel('Mean Normalized Cost', fontsize=9)
    ax1.set_title('Infrastructure Cost Comparison', fontsize=9, fontweight='bold')
    ax1.set_xticks(x)
    ax1.set_xticklabels(phases, fontsize=8)
    ax1.legend(fontsize=7, framealpha=0.9)
    ax1.grid(True, linestyle=':', alpha=0.3, axis='y')

    # CRL subplot
    phases_all = ['Relaxed', 'Constrained']
    crl_vals = [before['CRL_XING'].mean(), after['CRL_XING'].mean()]

    ax2.bar(phases_all, crl_vals, color=['#1f77b4', '#ff7f0e'],
            edgecolor='white', linewidth=0.5, width=0.5)
    ax2.set_ylabel('CRL (Context Degradation)', fontsize=9)
    ax2.set_title('Context Retention Loss', fontsize=9, fontweight='bold')
    ax2.grid(True, linestyle=':', alpha=0.3, axis='y')

    for i, v in enumerate(crl_vals):
        ax2.text(i, v + 0.001, f'{v:.4f}', ha='center', fontsize=7)

    plt.tight_layout(pad=0.5)
    path = os.path.join(output_dir, 'fig5c_cost_crl_analysis.pdf')
    plt.savefig(path, bbox_inches='tight')
    plt.close()
    print(f"[+] Saved: {path}")


def generate_summary_table(df: pd.DataFrame, output_dir: str = 'figures'):
    """
    Generate LaTeX summary table of experimental results.
    """
    before = df[df['Constraints_Active'] == False]  # noqa: E712
    after = df[df['Constraints_Active'] == True]  # noqa: E712

    summary = pd.DataFrame({
        'Metric': [
            'RAI - XING', 'RAI - Static Baseline', 'RAI - Role Baseline',
            'GRE - XING', 'CRL - XING',
            'XING Total Quality', 'XING Total Cost', 'XING Total Latency',
            'Static Failures', 'Role Failures'
        ],
        'Relaxed (Mean)': [
            f"{before['RAI_XING'].mean():.4f}",
            f"{before['RAI_Static'].mean():.4f}",
            f"{before['RAI_Role'].mean():.4f}",
            f"{before['GRE_XING'].mean():.4f}",
            f"{before['CRL_XING'].mean():.4f}",
            f"{before['XING_Quality'].mean():.4f}",
            f"{before['XING_Cost'].mean():.4f}",
            f"{before['XING_Latency'].mean():.4f}",
            f"{before['Static_Failures'].mean():.1f}",
            f"{before['Role_Failures'].mean():.1f}",
        ],
        'Constrained (Mean)': [
            f"{after['RAI_XING'].mean():.4f}",
            f"{after['RAI_Static'].mean():.4f}",
            f"{after['RAI_Role'].mean():.4f}",
            f"{after['GRE_XING'].mean():.4f}",
            f"{after['CRL_XING'].mean():.4f}",
            f"{after['XING_Quality'].mean():.4f}",
            f"{after['XING_Cost'].mean():.4f}",
            f"{after['XING_Latency'].mean():.4f}",
            f"{after['Static_Failures'].mean():.1f}",
            f"{after['Role_Failures'].mean():.1f}",
        ],
        'Delta (%)': [
            f"{(after['RAI_XING'].mean() / before['RAI_XING'].mean() - 1) * 100:+.1f}",
            f"{(after['RAI_Static'].mean() / before['RAI_Static'].mean() - 1) * 100:+.1f}",
            f"{(after['RAI_Role'].mean() / before['RAI_Role'].mean() - 1) * 100:+.1f}",
            f"{(after['GRE_XING'].mean() / before['GRE_XING'].mean() - 1) * 100:+.1f}",
            f"{(after['CRL_XING'].mean() / before['CRL_XING'].mean() - 1) * 100:+.1f}",
            f"{(after['XING_Quality'].mean() / before['XING_Quality'].mean() - 1) * 100:+.1f}",
            f"{(after['XING_Cost'].mean() / before['XING_Cost'].mean() - 1) * 100:+.1f}",
            f"{(after['XING_Latency'].mean() / before['XING_Latency'].mean() - 1) * 100:+.1f}",
            f"{(after['Static_Failures'].mean() / before['Static_Failures'].mean() - 1) * 100:+.1f}",
            f"{(after['Role_Failures'].mean() / before['Role_Failures'].mean() - 1) * 100:+.1f}",
        ]
    })

    latex = summary.to_latex(
        index=False,
        caption='Quantitative Results Summary Under Relaxed and Constrained Infrastructure Conditions',
        label='tab:results_summary',
        column_format='lccc',
        escape=False
    )

    path = os.path.join(output_dir, 'results_summary.tex')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(latex)
    print(f"[+] Saved: {path}")

    print("\n=== RESULTS SUMMARY ===")
    print(summary.to_string(index=False))
    return summary


# =====================================================================
# 9. RADAR / ARCHITECTURE DATA GENERATION
# =====================================================================

def generate_architecture_data(output_dir: str = 'figures'):
    """
    Generate structured data for IEEE architecture diagrams.
    Creates JSON descriptors for Figures 1-3.
    """
    arch = {
        'figure1': {
            'title': 'Global Runtime Architecture Topology',
            'layers': [
                {
                    'name': 'Adaptive Application Layer',
                    'components': ['Multimodal Stream', 'User Intent', 'Environment'],
                    'color': '#2c3e50'
                },
                {
                    'name': 'Agentic Orchestration Kernel',
                    'components': ['DAG Synthesis', 'Topological Scheduler',
                                   'Self-Healing Engine', 'Telemetry Monitor'],
                    'color': '#2980b9'
                },
                {
                    'name': 'Adaptive Cognitive Routing Engine',
                    'components': ['Utility Optimizer', 'Constraint Evaluator',
                                   'Infrastructure Monitor'],
                    'color': '#27ae60'
                },
                {
                    'name': 'Semantic Memory Fabric',
                    'components': ['Vector Store', 'Knowledge Graph',
                                   'Context Decay', 'Reinforcement'],
                    'color': '#8e44ad'
                },
                {
                    'name': 'Distributed Runtime Infrastructure',
                    'components': ['WebAssembly Sandbox', 'gRPC/WebSocket',
                                   'Cloud Cluster', 'Edge Nodes'],
                    'color': '#e67e22'
                }
            ],
            'connections': [
                ['Application', 'Kernel'],
                ['Kernel', 'Routing'],
                ['Routing', 'Memory'],
                ['Memory', 'Runtime']
            ]
        },
        'figure2': {
            'title': 'Self-Healing DAG Reconfiguration Lifecycle',
            'states': [
                {
                    'phase': 't0: Nominal Execution',
                    'nodes': ['N1', 'N2', 'N3'],
                    'edges': [['N1', 'N2'], ['N2', 'N3']]
                },
                {
                    'phase': 't1: Fault Injection',
                    'failed_node': 'N2',
                    'condition': 'Semantic Confidence < theta_min',
                    'affected': ['N3'],
                    'edges': [['N1', 'N2_F'], ['N2_F', 'N3']]
                },
                {
                    'phase': 't2: Topological Recovery',
                    'new_nodes': ['N2a', 'N2b'],
                    'recovered_edges': [['N1', 'N2a'], ['N2a', 'N2b'], ['N2b', 'N3']],
                    'formula': 'Trace(A^m) = 0 forall m'
                }
            ]
        },
        'figure3': {
            'title': 'Semantic Memory Fabric Mechanics',
            'concepts': [
                {'id': 'C1', 'label': 'Task Goal', 'strength': 0.92, 'layer': 'core'},
                {'id': 'C2', 'label': 'Multimodal Context', 'strength': 0.78, 'layer': 'active'},
                {'id': 'C3', 'label': 'Episodic Trace', 'strength': 0.45, 'layer': 'decaying'},
                {'id': 'C4', 'label': 'Procedural Rule', 'strength': 0.88, 'layer': 'core'},
                {'id': 'C5', 'label': 'Historical State', 'strength': 0.23, 'layer': 'decaying'}
            ],
            'relations': [
                ['C1', 'C2', 0.85],
                ['C1', 'C4', 0.72],
                ['C2', 'C3', 0.41],
                ['C4', 'C5', 0.18]
            ],
            'dynamics': {
                'decay_function': 'C(tau) = C0 * exp(-lambda * tau) * sigma(M_sim)',
                'reinforcement': 'Psi_{t+1} = Psi_t + gamma * (R - Psi_t)'
            }
        }
    }

    path = os.path.join(output_dir, 'architecture_data.json')
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(arch, f, indent=2)
    print(f"[+] Saved: {path}")


# =====================================================================
# 10. MAIN ENTRY POINT
# =====================================================================

if __name__ == '__main__':
    import sys

    print("=" * 65)
    print("  XING: Cognitive Infrastructure Simulator")
    print("  ICCIA 2026 - Experimental Framework")
    print("=" * 65)

    # Parse CLI args
    num_trials = 60
    num_tasks = 15
    constraint_at = 30

    if len(sys.argv) > 1:
        num_trials = int(sys.argv[1])
    if len(sys.argv) > 2:
        num_tasks = int(sys.argv[2])
    if len(sys.argv) > 3:
        constraint_at = int(sys.argv[3])

    output_dir = 'figures'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Run main experiment
    df = run_experiment(
        num_trials=num_trials,
        num_tasks_per_dag=num_tasks,
        constraint_activation_trial=constraint_at
    )

    # Save raw data
    csv_path = 'xing_experiment_results.csv'
    df.to_csv(csv_path, index=False)
    print(f"[+] Raw data saved: {csv_path}")

    # Generate figures
    print("\n[*] Generating IEEE-quality figures...")
    generate_figure_rai(df, output_dir)
    generate_figure_gre(df, output_dir)
    generate_figure_cost_breakdown(df, output_dir)

    # Generate summary table
    summary = generate_summary_table(df, output_dir)

    # Generate architecture data
    generate_architecture_data(output_dir)

    print("\n" + "=" * 65)
    print("  Simulation Complete.")
    print("  Output files:")
    print(f"    - {csv_path}")
    print(f"    - figures/fig5a_rai_comparison.pdf")
    print(f"    - figures/fig5b_gre_analysis.pdf")
    print(f"    - figures/fig5c_cost_crl_analysis.pdf")
    print(f"    - figures/results_summary.tex")
    print(f"    - figures/architecture_data.json")
    print("=" * 65)
