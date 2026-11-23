"""Smoke test: mitiq ZNE (scale factors 1, 3, 5, Richardson) on compiled circuits.

Not a baseline. It only checks that mitiq works with this Qiskit version and the fake backends,
and that noise scaling really multiplies the two-qubit gate count by 1, 3 and 5.

Known issue (found 19 Nov 2026): on FakeSherbrooke (ECR gates) mitiq's gate folding scales the
two-qubit gate count by 1, 5, 9 instead of 1, 3, 5, so Richardson extrapolation overshoots
(results above 1 for a probability). Most likely cause: mitiq converts circuits through
OpenQASM 2, where ECR is not a standard gate, so each folded ECR comes back as two ECRs.
FakeKingston (CZ, a standard gate) scales correctly. Superseded by folding.py, which folds
natively in Qiskit; mitiq is now used only for the extrapolation (mitigation.py). Kept as a
record of the negative result.

    .venv/Scripts/python zne_smoke.py
"""

import warnings

from mitiq import zne
from mitiq.zne.scaling import fold_gates_at_random
from qiskit import transpile
from qiskit_aer import AerSimulator
from qiskit_ibm_runtime.fake_provider import FakeKingston, FakeSherbrooke

from baseline import benchmarks, with_measurements

warnings.filterwarnings("ignore")

SHOTS = 4000
SCALE_FACTORS = [1, 3, 5]
CASES = (("QFT-4", "1011"), ("Grover-3", "101"))  # circuit, correct answer


def main() -> None:
    for backend in (FakeSherbrooke(), FakeKingston()):
        simulator = AerSimulator.from_backend(backend)
        for name, target in CASES:
            bench = next(b for b in benchmarks() if b.name == name)
            compiled = transpile(with_measurements(bench), backend, optimization_level=2, seed_transpiler=1)
            shots_each = SHOTS // len(SCALE_FACTORS)  # equal-budget rule: split shots across factors
            gate_counts: list[int] = []

            def executor(circuit) -> float:
                # Folding adds inverses (such as sxdg) that are not native: translate only, no optimization,
                # so the transpiler cannot cancel the inserted G·G† pairs.
                isa = transpile(
                    circuit, backend, optimization_level=0, layout_method="trivial", routing_method="none"
                )
                gate_counts.append(sum(1 for i in isa.data if i.operation.num_qubits == 2))
                counts = simulator.run(isa, shots=shots_each, seed_simulator=1234).result().get_counts()
                return counts.get(target, 0) / shots_each

            raw = executor(compiled)
            gate_counts.clear()
            mitigated = zne.execute_with_zne(
                compiled,
                executor,
                factory=zne.inference.RichardsonFactory(scale_factors=SCALE_FACTORS),
                scale_noise=lambda c, s: fold_gates_at_random(c, s, seed=7),
            )
            ratios = [round(n / gate_counts[0], 1) for n in gate_counts]
            print(
                f"{backend.name:15} {name:8} P(correct): raw={raw:.3f}  ZNE={mitigated:.3f}  exact=1.000  "
                f"2q gates {gate_counts} = x{ratios} (expected x{SCALE_FACTORS})"
            )


if __name__ == "__main__":
    main()
