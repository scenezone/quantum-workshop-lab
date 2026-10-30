import math

import pytest
from qiskit.quantum_info import Statevector

from app.ai.assistant_service import guide_reply
from app.ai.knowledge_base import build_context
from app.content.curriculum import EXPERIMENTS, LESSONS, ExperimentId
from app.database.models import HardwareRequest, SimulateRequest
from app.quantum.circuits import build_circuit
from app.quantum.simulator import run_simulation


def probabilities(circuit):
    no_measure = circuit.remove_final_measurements(inplace=False)
    return Statevector.from_instruction(no_measure).probabilities_dict()


def test_superposition_probabilities():
    probs = probabilities(build_circuit("superposition"))
    assert math.isclose(probs["0"], 0.5, abs_tol=1e-9)
    assert math.isclose(probs["1"], 0.5, abs_tol=1e-9)


def test_bell_state_probabilities():
    probs = probabilities(build_circuit("bell_entanglement"))
    assert math.isclose(probs["00"], 0.5, abs_tol=1e-9)
    assert math.isclose(probs["11"], 0.5, abs_tol=1e-9)
    assert probs.get("01", 0) == 0
    assert probs.get("10", 0) == 0


def test_interference_probabilities():
    probs = probabilities(build_circuit("interference"))
    assert math.isclose(probs["0"], 1.0, abs_tol=1e-9)
    assert probs.get("1", 0) == 0


@pytest.mark.parametrize("experiment_id", list(EXPERIMENTS))
def test_circuit_measurements_match_documented_distribution(experiment_id):
    circuit = build_circuit(experiment_id)
    state = Statevector.from_instruction(circuit.remove_final_measurements(inplace=False))
    # Measurements may read only a subset, or map q2 to c0.
    mapping = {
        circuit.find_bit(classical).index: circuit.find_bit(qubit).index
        for instruction in circuit.data
        if instruction.operation.name == "measure"
        for qubit, classical in zip(instruction.qubits, instruction.clbits)
    }
    observed = state.probabilities_dict(
        qargs=[mapping[index] for index in range(circuit.num_clbits)]
    )
    ideal = EXPERIMENTS[experiment_id]["ideal_probabilities"]
    for outcome in set(observed) | set(ideal):
        assert observed.get(outcome, 0) == pytest.approx(ideal.get(outcome, 0), abs=1e-10)
    assert sum(ideal.values()) == pytest.approx(1)


@pytest.mark.parametrize("experiment_id", list(EXPERIMENTS))
def test_all_approved_experiments_validate_and_run(experiment_id):
    assert SimulateRequest(experiment_id=experiment_id).experiment_id == experiment_id
    assert (
        HardwareRequest(
            experiment_id=experiment_id, idempotency_key="valid-submission-key"
        ).experiment_id
        == experiment_id
    )
    result = run_simulation(experiment_id, 128)
    allowed = {key for key, value in result["ideal_probabilities"].items() if value > 0}
    assert sum(result["counts"].values()) == 128
    assert set(result["counts"]) <= allowed
    assert sum(row["probability"] for row in result["amplitudes"]) == pytest.approx(1)


def test_qft_encodes_relative_phase_despite_uniform_probabilities():
    state = Statevector.from_instruction(
        build_circuit("qft_phase").remove_final_measurements(inplace=False)
    )
    assert list(state.data) == pytest.approx([0.5, 0.5j, -0.5, -0.5j])
    result = run_simulation("qft_phase", 128)
    assert [row["probability"] for row in result["amplitudes"]] == pytest.approx([0.25] * 4)


def test_catalog_links_and_prerequisites_are_consistent():
    assert set(EXPERIMENTS) == {item.value for item in ExperimentId}
    lessons = {item["lesson_id"]: item for item in LESSONS}
    assert len(lessons) == len(LESSONS)
    for lesson in LESSONS:
        assert set(lesson["related_experiments"]) <= set(EXPERIMENTS)
        for prerequisite in lesson["prerequisites"]:
            assert lessons[prerequisite]["order"] < lesson["order"]
    for experiment in EXPERIMENTS.values():
        assert experiment["lesson_id"] in lessons
        assert experiment["next_experiment"] in EXPERIMENTS


def test_advanced_assistant_retrieval_and_offline_guide(database):
    context = build_context(None, None, None, "Explain Grover amplitude amplification")
    assert "Grover" in context and "diffusion" in context.lower()
    guide = guide_reply("How does interference help Grover search?", None, None, None)
    assert "Grover" in guide and "marked" in guide
