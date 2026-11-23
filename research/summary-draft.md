# Week 1 summary (draft)

Setup: 10 circuits, `FakeSherbrooke` noise model on Qiskit Aer, 4000 shots, optimization levels 0-3, no mitigation. Real hardware use nahi kiya. Script: `research/baseline.py`, full data: `research/results/baseline.csv`.

## Kya samjha

**Mitigation techniques**
- **DD**: idle qubits par pulse sequences chalata hai, decoherence kam karta hai. Idle time zyada ho tab kaam aata hai.
- **Twirling**: coherent noise ko random Pauli noise mein convert karta hai, taaki ZNE/PEC jaise methods ka noise model sahi baithe.
- **TREX**: sirf readout error theek karta hai. Shallow circuits (jahan zyada error measurement se aata hai) ke liye sasta aur achha.
- **ZNE**: noise ko 1x/3x/5x amplify karke zero noise tak extrapolate karta hai. Deeper circuits ke liye, jahan gate error dominate karta hai. Cost: zyada circuits, aur answer thoda biased ho sakta hai.
- **PEC**: noise model seekh ke usse cancel karta hai, answer unbiased aata hai, lekin sampling cost exponentially badhti hai. Sirf chhote circuits ke liye practical.

**Transpiler levels (baseline se)**

| Opt level | Total 2q gates | Total depth | Mean TVD |
|---|---|---|---|
| 0 | 152 | 1148 | 0.158 |
| 1 | 116 | 458 | 0.100 |
| 2 | 96 | 449 | 0.076 |
| 3 | 96 | 449 | 0.076 |

- Level 0 se 2 tak 2-qubit gates 37% kam hue, depth 61% kam hui, aur error (TVD) aadha ho gaya.
- In 10 chhote circuits par level 2 aur 3 ka result bilkul same aaya. Level 3 ke extra passes ko yahan kuch aur optimize karne ko nahi mila.
- Error sabse zyada **2-qubit gate count** ke saath badhta hai: Bell (1 gate) ka TVD 0.015 hai, QFT-4 (18 gates) ka 0.160, aur Grover-3 (37 gates) ka 0.225.
- Sirf depth kam karna kaafi nahi hai. GHZ-5 par level 1 ki depth 17 thi aur TVD 0.112, jabki level 2 ki depth 28 thi lekin TVD 0.070. Level 2 ne behtar qubits/layout chune.
- Routing overhead: heavy-hex par triangle nahi hota, isliye QAOA-3 ke 6 logical CX hardware par 9 ho gaye, aur Grover-3 ke 24 se 37. Level 0 par BV-4 ko 18 gates lage, jabki level 1+ par sirf 3, kyunki level 0 layout optimize nahi karta.

**Kis circuit par kaunsi mitigation (hypothesis, abhi test nahi kiya)**
- Shallow (≤4 two-qubit gates): Bell, GHZ-3/5, Grover-2, BV-4. Inke liye TREX sabse pehle try karna chahiye.
- Deep: QFT-4, Grover-3. Inke liye ZNE, twirling ke saath.

## Kya unclear hai

1. Runtime ke resilience options local fake backend par kaam nahi karte. Maine test karke confirm kiya: `FakeSherbrooke` par EstimatorV2 ke saath `resilience_level` 0, 1 aur 2 teeno ka answer same aaya (⟨ZZ⟩ = 0.8135), aur Qiskit khud warning deta hai: "The resilience_level option has no effect in local testing mode." Toh simulator par mitigation khud implement karni padegi (readout mitigation, ZNE via gate folding) ya `mitiq` use karna padega. Kya simulator phase mein yahi "default mitigation" baseline maana jaaye?
2. TREX/ZNE/PEC **Estimator** ke options hain, yaani ye expectation values (jaise ⟨ZZ⟩) ko mitigate karte hain, counts ko nahi. Sampler mein sirf DD aur twirling milte hain. Kya hamari layer ka metric expectation values hona chahiye? Agar haan, toh har circuit ke liye ek observable chunna padega, jaise Bell ke liye ⟨ZZ⟩ aur GHZ ke liye parity.
3. Error metric kaunsa use karein? Broad distributions par TVD aur Hellinger fidelity alag kahani batate hain: QAOA-4 ka TVD 0.095 hai, lekin Hellinger fidelity 0.983.
4. Fake backend ka noise ek purana calibration snapshot hai. Real device par noise time ke saath badalta hai, toh ye baseline hardware ko kitna accurately represent karta hai?
5. Abhi har circuit ek hi transpiler seed se chala hai. Kya multiple seeds par variance bhi measure karna chahiye?

## Baseline table (v1, optimization level 2)

TVD: 0 = perfect, 1 = bilkul galat. Shot-noise floor matlab 4000 shots ki wajah se aane wala unavoidable error.

| Circuit | Qubits | 2q gates | Depth | TVD | Hellinger F | Shot-noise floor |
|---|---|---|---|---|---|---|
| Bell | 2 | 1 | 6 | 0.015 | 0.985 | 0.006 |
| GHZ-3 | 3 | 2 | 8 | 0.030 | 0.970 | 0.006 |
| GHZ-5 | 5 | 4 | 28 | 0.070 | 0.930 | 0.006 |
| Grover-2 | 2 | 2 | 11 | 0.024 | 0.977 | 0.000 |
| Grover-3 | 3 | 37 | 179 | 0.225 | 0.899 | 0.005 |
| QFT-3 | 3 | 9 | 39 | 0.067 | 0.933 | 0.000 |
| QFT-4 | 4 | 18 | 72 | 0.160 | 0.840 | 0.000 |
| BV-4 | 5 | 3 | 14 | 0.049 | 0.951 | 0.000 |
| QAOA-3 | 3 | 9 | 43 | 0.028 | 0.994 | 0.015 |
| QAOA-4 | 4 | 11 | 49 | 0.095 | 0.983 | 0.020 |

Saare optimization levels ka data: `research/results/baseline.md`.
