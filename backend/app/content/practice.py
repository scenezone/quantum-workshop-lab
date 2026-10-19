"""Topic practice. Answer keys stay on the server until a learner checks an attempt."""

from fastapi import HTTPException

from app.errors import NotFoundError


# MCQ tuples: prompt, four options, correct option index, explanation.
# Written tuples: prompt, sample answer, self-review points.
PRACTICE = {
    "intro-quantum": {
        "mcq": [
            ("Which statement correctly describes a qubit?", ["It always holds two readable classical bits.", "It has two basis states and can be in a superposition.", "It can be measured without changing its state in every case.", "It replaces the need for classical computation."], 1, "A qubit has basis states |0⟩ and |1⟩. Its normalized amplitudes determine measurement probabilities; one measurement does not reveal both amplitudes."),
            ("What does one computational-basis measurement of a qubit produce?", ["Both amplitudes exactly", "Every possible answer", "One classical outcome, 0 or 1", "A complete Bloch sphere"], 2, "A single measurement yields a classical outcome. Many identically prepared runs are needed to estimate probabilities."),
            ("Why can quantum computing help with some problems?", ["Algorithms can arrange interference and other quantum effects to make useful outcomes more likely.", "Every quantum algorithm solves every problem faster.", "All candidate solutions can be read simultaneously.", "Quantum computers do not need algorithms."], 0, "An advantage depends on the problem and algorithm. Superposition alone does not give access to every answer."),
            ("Which is a basis state of a single qubit?", ["A list of all integers", "A classical database", "An arbitrary unnormalized vector", "$|1\\rangle$"], 3, "The computational basis of a qubit is |0⟩ and |1⟩. Valid pure states are normalized linear combinations of these basis states."),
        ],
        "written": [
            ("Explain the difference between a classical bit and a qubit in your own words.", "A classical bit has a definite value 0 or 1. A pure qubit can have normalized complex amplitudes for |0⟩ and |1⟩. Measuring in this basis gives one classical outcome, with probabilities set by the squared amplitude magnitudes.", ["Two computational basis states", "Normalized amplitudes and superposition", "One outcome per measurement"]),
            ("Why is it misleading to say that a quantum computer simply reads every possible answer at once?", "Although a state can have amplitudes for many basis states, measurement yields a sampled outcome. A useful quantum algorithm must arrange interference so the desired information can be extracted efficiently.", ["Measurement does not reveal all amplitudes", "Interference must be designed by the algorithm", "Advantages depend on the task"]),
        ],
    },
    "superposition": {
        "mcq": [
            ("After H acts on |0⟩, what are the ideal computational-basis probabilities?", ["100% 0", "25% 0 and 75% 1", "50% 0 and 50% 1", "100% 1"], 2, "H|0⟩ = (|0⟩ + |1⟩)/√2. Each squared amplitude magnitude is 1/2."),
            ("Starting in |0⟩, what does H followed by H ideally produce?", ["|0⟩", "|1⟩", "An irreversible mixed state", "Two independent classical bits"], 0, "H² = I. Interference returns the qubit to its original state."),
            ("Which best describes 1,024 measurements of an equal superposition?", ["Exactly 512 of each outcome is guaranteed.", "All results must be 0.", "The outcomes alternate deterministically.", "Counts fluctuate around 512 of each outcome."], 3, "Each independent shot is sampled with probability 1/2, so finite counts need not be exactly equal."),
            ("What is the state H|1⟩?", ["|0⟩", "$(|0\\rangle-|1\\rangle)/\\sqrt{2}$", "$(|0\\rangle+|1\\rangle)/2$", "|1⟩"], 1, "H|1⟩ is the minus state. Its Z-basis probabilities match the plus state, but its relative phase differs."),
        ],
        "written": [
            ("Explain why two Hadamard gates return |0⟩ to |0⟩ instead of causing two random changes.", "H is a coherent unitary operation, not a random coin flip. The first H creates superposition; the second makes the |1⟩ amplitudes cancel and the |0⟩ amplitudes reinforce. Algebraically, H² = I.", ["Gates act on amplitudes coherently", "Destructive and constructive interference", "H² = I"]),
            ("You measure 530 zeros and 494 ones in 1,024 ideal shots. Does this alone show a faulty simulator? Explain.", "No. The ideal probabilities are 1/2 and 1/2, but finite sampling fluctuates. These counts alone do not establish a fault. Repeated runs and statistical uncertainty help assess whether a deviation is unusual.", ["Probabilities differ from finite counts", "Sampling fluctuations", "More evidence is needed to diagnose an error"]),
        ],
    },
    "entanglement": {
        "mcq": [
            ("Which outcomes occur for the ideal Bell state (|00⟩ + |11⟩)/√2 in the Z basis?", ["01 and 10 only", "All four outcomes equally", "00 only", "00 and 11 with equal probability"], 3, "Only 00 and 11 have nonzero amplitudes in this Bell state."),
            ("Which sequence prepares the lab's Bell state from |00⟩?", ["Measure both qubits, then X", "H on q0, then CX with q0 controlling q1", "X on both qubits", "H on each qubit without a connecting gate"], 1, "The initial H creates superposition on the control. CX correlates the target with its two branches."),
            ("If q0 is measured as 1 in this ideal Bell state, what will a Z measurement of q1 give?", ["0 with certainty", "Any integer", "1 with certainty", "No classical outcome"], 2, "The ideal joint state contains only 00 and 11, so the Z-basis results agree."),
            ("Do matching Z-basis outcomes alone prove a coherent Bell state?", ["No; a classical mixture can have the same Z-basis correlations.", "Yes, any matching outcomes prove entanglement.", "Yes, if the shot count is even.", "No Bell state ever has matching outcomes."], 0, "Distinguishing a coherent Bell state from a classical mixture requires additional measurement settings, not just correlated counts in one basis."),
        ],
        "written": [
            ("Describe how H and CX create the Bell state, including why the target becomes correlated with the control.", "H on q0 creates two coherent branches. CX flips q1 only in the branch where q0 is 1, yielding (|00⟩ + |11⟩)/√2. Measurements in the Z basis therefore agree, while each individual result is random.", ["Superposition on the control", "Conditional flip of the target", "Correlated joint outcomes"]),
            ("Why are Z-basis Bell correlations insufficient on their own to demonstrate coherence?", "The incoherent mixture of 00 and 11 has the same Z probabilities as the plus Bell state. Complementary-basis measurements, such as X correlations together with Z correlations, supply information about coherence that Z counts lack.", ["A mixture can reproduce the Z histogram", "Coherence concerns relative phase", "Additional measurement bases are needed"]),
        ],
    },
    "gates": {
        "mcq": [
            ("Which gate maps |0⟩ to |1⟩?", ["X", "Z", "Identity", "Measurement in every case"], 0, "X exchanges the computational basis states: X|0⟩ = |1⟩ and X|1⟩ = |0⟩."),
            ("What does Z do to the plus state?", ["It measures the qubit.", "It creates a second qubit.", "It changes the relative phase, producing the minus state.", "It always changes a Z measurement to 1."], 2, "Z preserves |0⟩ and changes the sign of |1⟩. This changes |+⟩ to |−⟩ without changing the immediate Z probabilities."),
            ("When does CX flip its target qubit in the computational basis?", ["Whenever the target is 0", "Whenever either qubit is measured", "Only when the control is 0", "When the control is 1"], 3, "CX is controlled-X: it applies X to the target conditional on the control being 1."),
            ("How is gate order read in the workshop circuit diagrams?", ["From bottom to top", "From left to right along each wire", "From right to left", "All gates happen in an arbitrary order"], 1, "Wires identify qubits and the horizontal direction shows the sequence of circuit operations."),
        ],
        "written": [
            ("Compare what X and Z do to a qubit. Why can Z matter even if a Z-basis histogram stays the same?", "X exchanges the |0⟩ and |1⟩ amplitudes. Z changes the sign of the |1⟩ amplitude, altering relative phase. An immediate Z measurement may show no change, but later interference, such as an H gate, can reveal the phase change.", ["X exchanges basis components", "Z changes relative phase", "Later gates can turn phase into observable probabilities"]),
            ("Starting from |00⟩, compare X on q0 followed by CX(0,1) with H on q0 followed by CX(0,1).", "X then CX gives the definite basis state |11⟩. H then CX gives the entangled superposition (|00⟩ + |11⟩)/√2. The control's initial coherence is what enables the second circuit to create the Bell state.", ["X prepares a definite control value", "H prepares a superposition", "CX has different effects on these inputs"]),
        ],
    },
    "hardware-noise": {
        "mcq": [
            ("Why can real hardware show 01 in the Bell experiment?", ["The ideal Bell state requires it.", "Qiskit randomly changes the intended algorithm.", "Gate or readout errors can create outcomes absent from the ideal distribution.", "Entanglement always produces every outcome."], 2, "Noise can alter the prepared state or the recorded measurement, creating deviations from ideal probabilities."),
            ("What is decoherence?", ["A guaranteed speedup", "A way to increase shots", "A perfect unitary gate", "Loss of quantum information through interaction with the environment"], 3, "Unwanted environmental interaction can destroy coherence and change the state over time."),
            ("What does increasing the number of shots primarily reduce?", ["Every gate error", "Statistical uncertainty in estimated probabilities", "The need for error correction", "The circuit depth"], 1, "More samples improve probability estimates, but do not remove systematic gate or readout errors."),
            ("What is a readout error?", ["Recording a different classical result from the actual measured basis outcome", "Using a Hadamard gate", "Having an odd number of shots", "Choosing a larger circuit diagram"], 0, "Readout errors occur when the measurement apparatus reports the wrong classical value."),
        ],
        "written": [
            ("Explain the difference between finite-shot fluctuations and hardware noise.", "Finite-shot fluctuations arise from sampling a probability distribution a limited number of times, even on an ideal simulator. Hardware noise can also change the distribution through imperfect gates, decoherence, or readout. More shots improve sampling precision without eliminating those device errors.", ["Sampling exists in ideal experiments", "Noise can change the underlying distribution", "More shots do not fix systematic errors"]),
            ("An ideal Bell circuit shows only 00 and 11, while hardware also shows 01 and 10. How would you interpret this?", "The extra outcomes are consistent with hardware imperfections. Compare the observed frequencies and their sampling uncertainty with the ideal distribution, and consider gate, readout, and coherence errors. The counts alone do not identify one unique physical error source.", ["Compare observed and ideal distributions", "Account for uncertainty", "Do not infer a unique cause from the histogram alone"]),
        ],
    },
    "complex-amplitudes": {
        "mcq": [
            ("For α = √3/2 and β = i/2, what is P(1)?", ["1/4", "1/2", "3/4", "i/2"], 0, "The Born rule uses the squared magnitude: |i/2|² = 1/4."),
            ("Which normalization condition defines a pure single-qubit state?", ["α + β = 1 in every case", "|α| + |β| = 2", "$|\\alpha|^2+|\\beta|^2=1$", "α = β in every case"], 2, "Squared amplitude magnitudes sum to one because the total measurement probability is one."),
            ("Can multiplying all amplitudes by the same phase change measurement probabilities?", ["Yes, it always swaps 0 and 1.", "No; a global phase is unobservable.", "Yes, it changes the normalization.", "Only if the shot count is large."], 1, "A common phase factor has unit magnitude and cancels from observable probabilities and relative phases."),
            ("How can you distinguish |+⟩ from |−⟩ using the available gates and Z measurement?", ["Measure Z repeatedly without other gates.", "Increase only the shot count.", "Apply X and always measure 0.", "Apply H, then measure Z."], 3, "H maps |+⟩ to |0⟩ and |−⟩ to |1⟩, converting the relative phase into distinct outcomes."),
        ],
        "written": [
            ("Explain why a 50/50 Z-basis histogram does not completely determine a qubit state.", "Many states have equal amplitude magnitudes but different relative phases, such as |+⟩ and |−⟩. Z counts reveal magnitudes, not that phase. Other measurement settings are needed to distinguish such states.", ["Equal magnitudes can hide different phases", "Give two example states", "Use complementary measurement bases"]),
            ("For (√3|0⟩ + i|1⟩)/2, calculate both Z-basis probabilities and explain the role of i.", "P(0) = 3/4 and P(1) = 1/4, so the state is normalized. The factor i sets a relative phase of π/2 between the components. It does not make P(1) imaginary; interference in another basis can reveal that phase.", ["Squared magnitudes give 3/4 and 1/4", "Probabilities sum to one", "Relative phase differs from probability"]),
        ],
    },
    "phase-kickback": {
        "mcq": [
            ("Which eigenvalue satisfies X|−⟩ = λ|−⟩?", ["0", "+1", "i", "−1"], 3, "X exchanges the two basis components of |−⟩ and produces an overall minus sign."),
            ("In the kickback lab, what is the ideal measured control output after the final H?", ["0", "1", "00 and 11 equally", "The unmeasured target value"], 1, "The controlled-X applies a relative minus sign to the control's 1 branch, turning |+⟩ into |−⟩. H then maps it to |1⟩."),
            ("What happens when the target eigenstate is |+⟩ instead?", ["Its X eigenvalue +1 gives no relative phase, so the control returns to 0.", "The control still always returns to 1.", "The target is destroyed.", "The oracle stops being unitary."], 0, "Controlled-X leaves a |+⟩ target unchanged with eigenvalue +1. No relative minus sign is acquired."),
            ("In controlled-U kickback, which component acquires the eigenphase?", ["Only an external classical bit", "Every amplitude receives an observable global phase", "The control's 1 branch relative to its 0 branch", "Only a new qubit outside the circuit"], 2, "For an eigenstate target, controlled-U preserves that target while multiplying the control's 1 branch by its eigenvalue."),
        ],
        "written": [
            ("Explain how a target's eigenvalue becomes a relative phase on a control qubit.", "An eigenstate |u⟩ obeys U|u⟩ = e^{iφ}|u⟩. Controlled-U applies that factor only when the control is 1. Thus α|0⟩ + β|1⟩ becomes α|0⟩ + e^{iφ}β|1⟩, while the target remains |u⟩.", ["The target must be an eigenstate for this form", "Only the control-1 branch receives the factor", "The resulting phase is relative"]),
            ("Compare the lab with a |−⟩ target and a |+⟩ target, including the final measured control.", "For |−⟩, X has eigenvalue −1, so a |+⟩ control becomes |−⟩ and the final H produces 1. For |+⟩, the eigenvalue is +1; the control stays |+⟩ and the final H produces 0. Both predictions assume ideal operations.", ["Eigenvalues −1 and +1", "Relative phase versus no phase change", "Final control outcomes 1 and 0"]),
        ],
    },
    "multipartite-entanglement": {
        "mcq": [
            ("What are the ideal Z-basis outcomes for the plus GHZ state?", ["All eight equally", "001 and 110 only", "000 and 111 with equal probability", "000 only"], 2, "The GHZ state contains equal amplitudes for 000 and 111, with all other amplitudes zero."),
            ("What can reproduce the same Z-basis GHZ histogram without coherence?", ["A 50/50 classical mixture of 000 and 111", "The uniform superposition of all eight states", "Only a pure GHZ state", "A definite 001 state"], 0, "The incoherent mixture has identical Z probabilities but lacks the GHZ state's off-diagonal coherence terms."),
            ("How can the lab's Z measurements be changed to measure X on each qubit?", ["Apply only Z gates.", "Apply H to each qubit before measuring Z.", "Remove every measurement.", "Measure just one classical bit."], 1, "H rotates an X-basis measurement into the computational-basis measurement available in the circuit."),
            ("What is ⟨X⊗X⊗X⟩ for the ideal plus GHZ state?", ["−1", "1/2", "0", "+1"], 3, "XXX exchanges 000 and 111, so the plus GHZ state is its +1 eigenstate. The corresponding incoherent mixture has expectation zero."),
        ],
        "written": [
            ("Why does seeing only 000 and 111 not certify coherent GHZ entanglement?", "Those counts establish correlations in the Z basis, but a classical mixture of 000 and 111 gives the same histogram. A complementary test probes coherence; for example, ideal XXX expectation is +1 for the plus GHZ state and zero for that mixture.", ["Explain the indistinguishable Z histograms", "Identify missing coherence information", "Describe a complementary measurement"]),
            ("Describe how to prepare the three-qubit GHZ state and what its individual and joint measurements show.", "Starting in |000⟩, apply H to q0, CX(0,1), and CX(0,2). The result is (|000⟩ + |111⟩)/√2. Each individual Z outcome is random, while the three joint Z outcomes always agree in the ideal case.", ["One H and two controlled-X gates", "Correct GHZ superposition", "Random marginals and correlated joint results"]),
        ],
    },
    "deutsch-jozsa": {
        "mcq": [
            ("What promise is required by the Deutsch–Jozsa decision problem?", ["The function is either constant or balanced.", "The function is always linear.", "The function has only one marked input.", "Every function value must be supplied as a measurement."], 0, "The algorithm distinguishes constant functions from balanced ones under that promise; it does not solve arbitrary truth-table classification."),
            ("For the lab's f(x0,x1) = x0, what is the ideal displayed c1c0 result?", ["00", "10", "11", "01"], 3, "The oracle contributes a sign determined by x0. Final interference sets measured q0 to 1 and q1 to 0, displayed as 01."),
            ("Under the promise, what does an all-zero input-register outcome identify ideally?", ["A balanced function", "A constant function", "Every value of f", "A failed measurement"], 1, "The all-zero amplitude has magnitude one for constant functions and vanishes for balanced functions."),
            ("Does a nonzero input-register outcome reveal the complete truth table?", ["Yes, every output bit contains half the table.", "Yes, for every possible function.", "No; it identifies the promised balanced case, not every function value.", "No; it means the function is constant."], 2, "The algorithm solves the constant-versus-balanced decision problem. It does not read out all values of f."),
        ],
        "written": [
            ("Explain why the all-zero amplitude cancels for a balanced function.", "After the phase oracle, each input x has a factor (−1)^{f(x)}. The final Hadamards give all-zero amplitude 2^{-n} times the sum of those signs. For a balanced function, half are +1 and half are −1, so the sum is zero.", ["Phase encoding of function values", "Sum of signs for the zero outcome", "Cancellation uses the balanced promise"]),
            ("Why is the lab's oracle balanced, and why is its result displayed as 01?", "The function f(x0,x1) = x0 equals 1 on half the inputs. Kickback followed by the final Hadamards produces q0 = 1 and q1 = 0. Since q0 maps to c0 and Qiskit displays c1c0, the string is 01. The output ancilla is not measured.", ["Half the input values map to 1", "Identify the input-qubit outcomes", "Explain classical-bit display order"]),
        ],
    },
    "grover-search": {
        "mcq": [
            ("How many Grover iterations ideally find the lab's single marked item among four states?", ["Zero", "One", "Four", "Infinitely many"], 1, "For N = 4 with one marked state, one oracle-plus-diffusion iteration gives success probability one."),
            ("What does the lab's phase oracle do to the marked amplitude?", ["It measures the marked state.", "It sets every amplitude to zero.", "It changes its sign.", "It clones the marked state."], 2, "The phase oracle multiplies the marked basis amplitude by −1; diffusion then turns this phase distinction into amplitude amplification."),
            ("Should Grover iterations be repeated indefinitely?", ["No; the success probability oscillates and can decrease after the optimum.", "Yes; each iteration always improves success.", "Yes; one million iterations guarantees a noiseless device.", "No; Grover permits no iteration at all."], 0, "Grover iterations rotate amplitudes. Continuing beyond the best iteration count can rotate away from the marked subspace."),
            ("What is the ideal oracle-query scaling for general unstructured search with one marked item?", ["O(N²)", "O(2ᴺ)", "O(1) for every N", "O(√N)"], 3, "The quadratic query advantage counts oracle calls. It does not make oracle construction or data access free."),
        ],
        "written": [
            ("Trace one ideal Grover iteration for the four-state lab that marks 11.", "The initial amplitudes are (1/2, 1/2, 1/2, 1/2). The phase oracle changes them to (1/2, 1/2, 1/2, −1/2), whose mean is 1/4. Reflection about that mean gives (0, 0, 0, 1), up to a common global phase, so 11 is measured with certainty.", ["Uniform initial amplitudes", "Sign flip of the marked component", "Diffusion and final success probability"]),
            ("Explain the difference between a Grover oracle-query advantage and a claim that every database search becomes free or instantaneous.", "Grover reduces ideal oracle-query complexity to O(√N) for one marked item, but the oracle must still be implemented and data access may cost resources. Circuit depth, noise, and state preparation also matter. A query bound alone does not describe total practical runtime.", ["Quadratic oracle-query scaling", "Oracle and data-access costs", "Separate theoretical and implementation costs"]),
        ],
    },
    "quantum-fourier-transform": {
        "mcq": [
            ("What are the lab's ideal Z-basis probabilities after QFT on |01⟩?", ["100% 01", "50% 00 and 50% 11", "100% 11", "25% for each of 00, 01, 10, and 11"], 3, "The QFT amplitudes have different phases but equal magnitude 1/2, so every squared magnitude is 1/4."),
            ("Where does the input-dependent information appear in this QFT output?", ["Only in the number of shots", "In relative phases between amplitudes", "In an extra hidden classical register", "It is necessarily destroyed"], 1, "A Z histogram cannot show these phases, but later coherent interference can use them."),
            ("What does applying the ideal inverse QFT immediately after this QFT produce?", ["A random state with no relation to the input", "Only |00⟩", "The original input |01⟩", "A copy of all four amplitudes in classical memory"], 2, "QFT is unitary. Its inverse undoes the transformation and recovers the prepared basis state."),
            ("Which amplitude list matches QFT₄|1⟩ in the lesson's output order?", ["(1/2, i/2, −1/2, −i/2)", "(1, 0, 0, 0)", "(1/4, 1/4, 1/4, 1/4)", "(1/2, 1/2, 1/2, 1/2)"], 0, "The Fourier phases are exp(2πiy/4), multiplied by 1/2 for y = 0, 1, 2, 3."),
        ],
        "written": [
            ("Why can the QFT histogram look uniform even though its output contains information about the input?", "The Fourier output for a basis input has equal amplitude magnitudes and input-dependent phases. Z measurement records only squared magnitudes, so it hides those phases. An appropriate inverse or later interference can make the phase information observable.", ["Equal magnitudes", "Input-dependent relative phases", "Interference can reveal phase information"]),
            ("Describe how to construct the inverse of a QFT circuit and what it should do in the lab.", "Reverse the order of all gates and replace each gate by its inverse. Hadamard and SWAP are self-inverse; controlled-phase angles change sign. Applied to the lab's QFT output, this returns the state to |01⟩ ideally.", ["Reverse gate order", "Invert gates and phase angles", "Recover the prepared input"]),
        ],
    },
    "quantum-teleportation": {
        "mcq": [
            ("What resources does standard single-qubit teleportation use?", ["A shared Bell pair and two classical bits", "No shared entanglement or communication", "Two identical copies of the unknown input", "A faster-than-light classical signal"], 0, "Teleportation uses shared entanglement, local operations, two measurement bits, and conditional corrections."),
            ("What does the lab ideally measure after H on the corrected |+⟩ receiver?", ["1 with certainty", "00 and 11 equally", "0 with certainty", "No classical output"], 2, "The final H maps the expected receiver state |+⟩ to |0⟩ before the Z measurement."),
            ("Which limitation applies to this workshop's teleportation circuit?", ["It proves arbitrary-state fidelity with one Z measurement.", "Its coherent correction gates require quantum connectivity.", "It sends information faster than light.", "It creates a spare copy of an unknown input."], 1, "The lab defers measurement and uses controlled quantum corrections. It is not a demonstration of separated parties using only classical feed-forward."),
            ("Why is H applied before measuring the receiver?", ["To copy the receiver", "To remove all possible hardware noise", "To measure every amplitude at once", "To make the X-basis distinction between |+⟩ and |−⟩ observable using Z measurement"], 3, "H maps the X eigenstates to distinct computational-basis states. Their direct Z histograms would otherwise both be 50/50."),
        ],
        "written": [
            ("Explain why teleportation neither copies an unknown state nor permits faster-than-light communication.", "The sender's operations and measurements consume the original unknown state. The receiver requires the classical measurement outcomes to apply the appropriate corrections. Shared entanglement alone cannot communicate a controllable message faster than those classical bits.", ["The original state is not retained as a copy", "Conditional corrections need classical outcomes", "Entanglement alone cannot signal"]),
            ("What does the lab verify, and what would be needed to make a stronger fidelity claim?", "It verifies a known |+⟩ input through one X-basis check, implemented by H then Z measurement on the receiver. This does not establish arbitrary-state teleportation fidelity. Testing additional input states and measurement bases, with an appropriate characterization protocol, would give stronger evidence.", ["Known input and one measurement basis", "Coherent corrections versus classical feed-forward", "Broader characterization for stronger claims"]),
        ],
    },
    "quantum-error-correction": {
        "mcq": [
            ("Which error does the three-qubit repetition code protect against in its intended setting?", ["Any error on any number of qubits", "All phase errors without additional encoding", "One bit-flip error on a physical qubit", "Every measurement error in every circuit"], 2, "The bit-flip repetition code corrects a single X error, not arbitrary phase errors or multiple flips."),
            ("What information should an error syndrome reveal?", ["The complete unknown logical amplitudes", "Which recoverable error occurred, without revealing the logical state", "A classical copy of the unknown qubit", "Every future hardware error"], 1, "Parity checks distinguish error patterns while preserving the encoded logical information."),
            ("What is the ideal final measured q0 value in the fixed recovery lab?", ["0", "Both 0 and 1 in a guaranteed alternating pattern", "The syndrome bit 11 as a single output bit", "1"], 3, "The lab starts with logical 1, injects an X error on q0, and applies decode-and-recover operations to restore that value."),
            ("Does encoding α|0⟩ + β|1⟩ as α|000⟩ + β|111⟩ make three independent copies?", ["No; it is an entangled encoding, not independent clones.", "Yes, each physical qubit becomes the full unknown state.", "Yes, if α and β are real.", "Only the middle qubit is cloned."], 0, "The encoded amplitudes describe a joint state. Individual physical qubits are not independent copies of the unknown logical qubit."),
        ],
        "written": [
            ("Explain why syndrome extraction can detect errors without measuring away the unknown logical amplitudes.", "Parity checks ask whether physical qubits agree, rather than whether the logical state is 0 or 1. Their outcomes identify a correctable error pattern while preserving the superposition within the logical code space. A suitable recovery then reverses that error.", ["Parity information rather than logical value", "Preserve the encoded superposition", "Use the syndrome to choose a recovery"]),
            ("What are two important limits of the workshop's bit-flip correction demonstration?", "It corrects one deliberately chosen X error under ideal recovery gates; it does not correct arbitrary phase errors or two simultaneous bit flips. It is a coherent decode-and-recover example, not a full fault-tolerant cycle with repeated noisy syndrome extraction. Recovery gates can also introduce noise.", ["Limited error model", "Multiple errors can cause failure", "Recovery is not automatically fault tolerant"]),
        ],
    },
    "variational-methods": {
        "mcq": [
            ("Which expression estimates ⟨Z⟩ from Z-basis counts?", ["n0 + n1", "n1 / n0 in every case", "Always 1/2", "(n0 − n1) / (n0 + n1)"], 3, "Z has eigenvalue +1 for outcome 0 and −1 for outcome 1, so the sample mean is the normalized count difference."),
            ("For Ry(θ)|0⟩ with cost Hamiltonian Z, what is the exact ideal cost?", ["cos θ", "sin θ in every case", "Always zero", "θ²"], 0, "The probabilities are cos²(θ/2) and sin²(θ/2), whose difference is cos θ."),
            ("What normally proposes updated parameters in a variational quantum workflow?", ["The histogram axis labels", "A classical optimizer using measured cost estimates", "The browser's refresh button", "A computational-basis measurement of every amplitude"], 1, "The quantum device estimates costs; a classical optimization loop proposes new parameters."),
            ("Does one computational-basis histogram determine every Pauli expectation?", ["Yes, it determines all incompatible observables.", "Yes, if the number of shots is divisible by three.", "No; incompatible measurement bases require additional settings.", "No Pauli expectation can ever be measured."], 2, "Z, X, and Y measurements generally require different basis rotations. More Z shots alone do not supply the missing observables."),
        ],
        "written": [
            ("Given 750 zeros and 250 ones, estimate ⟨Z⟩ and explain what this estimate represents.", "The estimate is (750 − 250)/(750 + 250) = 0.5. This is the finite-sample average of Z eigenvalues +1 and −1. It estimates an expectation value, rather than a state amplitude or a guarantee about each individual shot.", ["Correct normalized count difference", "Eigenvalues +1 and −1", "Finite-sample uncertainty"]),
            ("Outline a variational quantum workflow and explain how it differs from the current fixed circuit labs.", "Choose a parameterized circuit and cost Hamiltonian, prepare states, measure the required observables in suitable bases, reconstruct the cost, and use a classical optimizer to update parameters. Repeat until a stopping criterion is met. The current labs teach these ingredients but do not run this optimization loop.", ["Parameterized preparation and measured cost", "Appropriate measurement bases", "Classical parameter updates and iteration"]),
        ],
    },
}


def public_questions(lesson_id: str) -> list[dict]:
    practice = PRACTICE.get(lesson_id)
    if practice is None:
        return []
    questions = []
    for index, (prompt, options, _correct, _explanation) in enumerate(practice["mcq"], 1):
        questions.append({
            "question_id": f"{lesson_id}-mcq-{index}", "kind": "multiple_choice", "prompt": prompt,
            "options": [{"option_id": chr(97 + i), "text": text} for i, text in enumerate(options)],
        })
    for index, (prompt, _answer, _points) in enumerate(practice["written"], 1):
        questions.append({"question_id": f"{lesson_id}-written-{index}", "kind": "short_answer", "prompt": prompt, "options": []})
    return questions


def check_answer(lesson_id: str, question_id: str, option_id: str | None, answer: str | None) -> dict:
    questions = public_questions(lesson_id)
    question = next((item for item in questions if item["question_id"] == question_id), None)
    if question is None:
        raise NotFoundError("Practice question not found for this lesson.")
    if question["kind"] == "multiple_choice":
        if answer is not None or option_id not in {item["option_id"] for item in question["options"]}:
            raise HTTPException(status_code=422, detail="Select one of this question's options.")
        multiple_choice = [item for item in questions if item["kind"] == "multiple_choice"]
        index = next(i for i, item in enumerate(multiple_choice) if item["question_id"] == question_id)
        _prompt, _options, correct, explanation = PRACTICE[lesson_id]["mcq"][index]
        return {"question_id": question_id, "kind": "multiple_choice", "correct": option_id == chr(97 + correct),
                "correct_option_id": chr(97 + correct), "explanation": explanation}
    if option_id is not None or not answer or not answer.strip():
        raise HTTPException(status_code=422, detail="Write an answer before comparing it with the sample.")
    written = [item for item in questions if item["kind"] == "short_answer"]
    index = next(i for i, item in enumerate(written) if item["question_id"] == question_id)
    _prompt, sample, points = PRACTICE[lesson_id]["written"][index]
    return {"question_id": question_id, "kind": "short_answer", "sample_answer": sample, "key_points": points}
