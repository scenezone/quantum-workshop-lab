import json
import math
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from app.config import get_settings
from app.content.challenges import BUILD_CHALLENGES, check_build_challenge
from app.content.curriculum import EXPERIMENTS
from app.errors import InvalidInputError
from app.main import app
from app.quantum.circuits import build_circuit, ideal_measured_probabilities
from app.quantum.labs import run_chsh, run_vqe
from app.quantum.qasm import import_qasm
from app.quantum.simulator import run_custom_simulation, run_simulation

R = 1 / math.sqrt(2)

# One known solution per build challenge.
SOLUTIONS = {
    "minus-state": (1, [{"name": "X", "qubits": [0]}, {"name": "H", "qubits": [0]}]),
    "flip-without-x": (
        1,
        [{"name": "H", "qubits": [0]}, {"name": "Z", "qubits": [0]}, {"name": "H", "qubits": [0]}],
    ),
    "biased-coin": (1, [{"name": "RY", "qubits": [0], "angle": math.pi / 3}]),
    "bell-phi-minus": (
        2,
        [
            {"name": "H", "qubits": [0]},
            {"name": "CX", "qubits": [0, 1]},
            {"name": "Z", "qubits": [0]},
        ],
    ),
    "bell-psi-plus": (
        2,
        [
            {"name": "H", "qubits": [0]},
            {"name": "CX", "qubits": [0, 1]},
            {"name": "X", "qubits": [1]},
        ],
    ),
    "ghz-three": (
        3,
        [
            {"name": "H", "qubits": [0]},
            {"name": "CX", "qubits": [0, 1]},
            {"name": "CX", "qubits": [1, 2]},
        ],
    ),
    "uniform-three": (3, [{"name": "H", "qubits": [q]} for q in range(3)]),
    "toffoli-and": (
        3,
        [
            {"name": "X", "qubits": [0]},
            {"name": "X", "qubits": [1]},
            {"name": "CCX", "qubits": [0, 1, 2]},
        ],
    ),
}


@pytest.fixture
def client(database):
    with (
        patch("app.database.mongodb.Mongo.connect"),
        patch("app.database.mongodb.Mongo.close"),
        TestClient(app) as test_client,
    ):
        yield test_client


@pytest.mark.parametrize("experiment_id", list(EXPERIMENTS))
def test_curriculum_ideal_probabilities_match_the_circuits(experiment_id):
    computed = ideal_measured_probabilities(build_circuit(experiment_id))
    expected = {k: v for k, v in EXPERIMENTS[experiment_id]["ideal_probabilities"].items() if v}
    assert computed.keys() == expected.keys()
    for outcome, probability in expected.items():
        assert computed[outcome] == pytest.approx(probability, abs=1e-9)


def test_bell_state_in_the_x_basis_stays_correlated():
    result = run_simulation("bell_entanglement", 400, "ideal", ["X", "X"])
    assert result["measurement_bases"] == ["X", "X"]
    assert set(result["counts"]) <= {"00", "11"}
    assert result["ideal_probabilities"] == pytest.approx({"00": 0.5, "11": 0.5})


def test_y_basis_measurement_of_plus_state_is_random():
    result = run_custom_simulation(1, [{"name": "H", "qubits": [0]}], 200, "ideal", ["Y"])
    assert result["ideal_probabilities"] == pytest.approx({"0": 0.5, "1": 0.5})


def test_basis_list_must_match_the_qubit_count(client):
    response = client.post(
        "/api/experiments/simulate",
        json={"experiment_id": "bell_entanglement", "shots": 10, "measurement_bases": ["X"]},
    )
    assert response.status_code == 400


def test_new_builder_gates_and_five_qubits(client):
    gates = [
        {"name": "SX", "qubits": [0]},
        {"name": "U", "qubits": [1], "angle": math.pi, "phi": 0, "lam": math.pi},
        {"name": "CP", "qubits": [0, 1], "angle": math.pi / 2},
        {"name": "CCX", "qubits": [0, 1, 4]},
    ]
    response = client.post(
        "/api/experiments/custom/simulate",
        json={"qubits": 5, "gates": gates, "shots": 64},
    )
    assert response.status_code == 200
    assert all(len(outcome) == 5 for outcome in response.json()["counts"])
    assert sum(response.json()["ideal_probabilities"].values()) == pytest.approx(1)


@pytest.mark.parametrize(
    "gate",
    [
        {"name": "U", "qubits": [0], "angle": 1.0},
        {"name": "CP", "qubits": [0, 1]},
        {"name": "H", "qubits": [0], "phi": 1.0},
        {"name": "CCX", "qubits": [0, 1]},
    ],
)
def test_gate_parameters_are_validated(client, gate):
    response = client.post(
        "/api/experiments/custom/simulate", json={"qubits": 3, "gates": [gate], "shots": 8}
    )
    assert response.status_code == 422


def test_custom_evolution_reports_entanglement_as_a_short_bloch_vector(client):
    response = client.post(
        "/api/experiments/custom/evolution",
        json={
            "qubits": 2,
            "gates": [{"name": "H", "qubits": [0]}, {"name": "CX", "qubits": [0, 1]}],
        },
    )
    steps = response.json()["steps"]
    assert [step["gate"] for step in steps] == ["Start", "H", "CX"]
    assert steps[1]["qubits"][0]["length"] == pytest.approx(1)
    assert steps[2]["qubits"][0]["length"] == pytest.approx(0, abs=1e-9)


def test_device_noise_profile_runs_without_ibm_credentials(client):
    response = client.post(
        "/api/experiments/simulate",
        json={"experiment_id": "bell_entanglement", "shots": 256, "noise_profile": "device_manila"},
    )
    data = response.json()
    assert response.status_code == 200
    assert "Manila" in data["backend_name"]
    assert sum(data["counts"].values()) == 256


@pytest.mark.parametrize("challenge", BUILD_CHALLENGES, ids=lambda item: item["challenge_id"])
def test_every_build_challenge_has_a_passing_solution(challenge):
    qubits, gates = SOLUTIONS[challenge["challenge_id"]]
    assert check_build_challenge(challenge["challenge_id"], qubits, gates)["passed"]


def test_phase_matters_for_state_challenges():
    # Φ+ has the same counts as Φ- but the wrong relative phase.
    result = check_build_challenge(
        "bell-phi-minus",
        2,
        [{"name": "H", "qubits": [0]}, {"name": "CX", "qubits": [0, 1]}],
    )
    assert not result["passed"]
    assert result["score"] == pytest.approx(0, abs=1e-9)


def test_challenge_rules_are_enforced(client):
    path = "/api/challenges/flip-without-x/check"
    disallowed = client.post(path, json={"qubits": 1, "gates": [{"name": "X", "qubits": [0]}]})
    assert disallowed.status_code == 422
    assert "not allowed" in disallowed.json()["detail"]
    wrong_size = client.post(path, json={"qubits": 2, "gates": []})
    assert wrong_size.status_code == 422
    listing = client.get("/api/challenges").json()
    assert '"target":' not in json.dumps(listing["challenges"])
    assert "bell-correlations" in listing["experiment_challenge_ids"]


def test_chsh_violates_the_classical_bound_without_noise():
    result = run_chsh(4000, "ideal")
    assert result["ideal_s_value"] == pytest.approx(2 * math.sqrt(2))
    assert result["s_value"] > 2.5
    assert len(result["settings"]) == 4


def test_chsh_rejects_unbounded_angles(client):
    response = client.post("/api/labs/chsh", json={"shots": 10, "alice": [0, 100], "bob": [0, 1]})
    assert response.status_code == 400


@pytest.mark.parametrize("hamiltonian", ["zx", "h2"])
def test_vqe_approaches_the_ground_energy(hamiltonian):
    result = run_vqe(hamiltonian, 40, 0.5, 4000, "ideal")
    assert result["trace"][-1]["exact_energy"] == pytest.approx(result["ground_energy"], abs=0.03)
    assert len(result["trace"]) == 41
    if hamiltonian == "zx":
        assert result["ground_energy"] == pytest.approx(-math.sqrt(2))
        assert len(result["landscape"]) == 61
    else:
        assert result["ground_energy"] == pytest.approx(-1.8572750302, abs=1e-6)


def test_qasm_import_maps_gates_and_normalizes_angles():
    circuit = import_qasm(
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[2];\ncreg c[2];\n'
        "h q[0];\ncx q[0],q[1];\nrz(7*pi/2) q[1];\np(pi/4) q[0];\nbarrier q;\n"
        "measure q -> c;\n"
    )
    assert circuit["qubits"] == 2
    assert [gate["name"] for gate in circuit["gates"]] == ["H", "CX", "RZ", "U"]
    assert circuit["gates"][2]["angle"] == pytest.approx(-math.pi / 2)
    assert circuit["gates"][3]["lam"] == pytest.approx(math.pi / 4)


@pytest.mark.parametrize(
    "source",
    [
        'OPENQASM 2.0;\ninclude "/etc/passwd";\nqreg q[1];',
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[6];\nh q[0];',
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\ncreg c[1];\nmeasure q -> c;\nh q[0];',
        'OPENQASM 2.0;\ninclude "qelib1.inc";\nqreg q[1];\nreset q[0];',
        "not a program",
    ],
)
def test_qasm_import_rejects_unsafe_or_unsupported_programs(source):
    with pytest.raises(InvalidInputError):
        import_qasm(source)


def test_rate_limit_responses_include_retry_after(client):
    for _ in range(5):
        client.post(
            "/api/feedback", json={"rating": 5, "clarity_rating": 5, "completed_workshop": True}
        )
    response = client.post(
        "/api/feedback", json={"rating": 5, "clarity_rating": 5, "completed_workshop": True}
    )
    assert response.status_code == 429
    assert int(response.headers["Retry-After"]) > 0


def test_frontend_catalog_is_generated_from_the_backend():
    from scripts.export_catalog import render

    path = Path(__file__).resolve().parents[2] / "frontend/src/types/catalog.generated.ts"
    assert path.read_text(encoding="utf-8") == render(), (
        "Run `python scripts/export_catalog.py` from backend/ to refresh the frontend catalog."
    )


def test_public_config_lists_noise_profiles(client):
    config = client.get("/api/config/public").json()
    assert {item["id"] for item in config["noise_profiles"]} >= {"ideal", "device_manila"}
    assert config["database_enabled"] is True
    assert config["live_ai_enabled"] is False


def test_settings_reject_short_admin_tokens(monkeypatch):
    from app.config import Settings

    with pytest.raises(ValueError):
        Settings(admin_token="short")
    assert Settings(admin_token="x" * 16).admin_enabled
    assert get_settings().admin_enabled is False
