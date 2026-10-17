from app.quantum.simulator import run_simulation


def test_simulator_returns_valid_counts():
    result = run_simulation("superposition", 1000)
    assert result["backend"] == "aer_simulator"
    assert sum(result["counts"].values()) == 1000
    assert set(result["counts"]) <= {"0", "1"}
    assert abs(sum(result["observed_probabilities"].values()) - 1) < 1e-9


def test_bell_simulator_counts_are_correlated():
    result = run_simulation("bell_entanglement", 1000)
    assert sum(result["counts"].values()) == 1000
    assert set(result["counts"]) <= {"00", "01", "10", "11"}
    assert result["counts"]["00"] + result["counts"]["11"] > 950