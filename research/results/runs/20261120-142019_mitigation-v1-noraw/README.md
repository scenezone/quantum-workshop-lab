# Legacy run: mitigation v1 (20 Nov 2026, started 14:20)

First mitigation baseline on FakeKingston: none vs readout vs ZNE (Richardson), 10 core circuits,
12,000 shots per method, 10 repeats, each repeat simulated separately (seeds 10000 + 1000*r + offsets).

Raw counts were NOT saved for this run (the run-record system did not exist yet), so its numbers
cannot be re-analyzed. It is kept as a record. Superseded by later runs in results/runs/ that save
counts.json. Method details: see mitigation.py as of that date (folding.py native folding,
tensored readout correction with 20% calibration shots, Richardson extrapolation via mitiq 1.1.0).
