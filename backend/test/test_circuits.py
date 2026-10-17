import math

from qiskit.quantum_info import Statevector

from app.quantum.circuits import build_circuit


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