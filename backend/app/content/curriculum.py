"""Canonical workshop lessons and approved circuit definitions."""
from enum import StrEnum


class ExperimentId(StrEnum):
    SUPERPOSITION = 'superposition'
    BELL_ENTANGLEMENT = 'bell_entanglement'
    INTERFERENCE = 'interference'
    PHASE_KICKBACK = 'phase_kickback'
    GHZ_ENTANGLEMENT = 'ghz_entanglement'
    DEUTSCH_JOZSA = 'deutsch_jozsa'
    GROVER_SEARCH = 'grover_search'
    QFT_PHASE = 'qft_phase'
    QUANTUM_TELEPORTATION = 'quantum_teleportation'
    BIT_FLIP_CORRECTION = 'bit_flip_correction'


LESSONS = [{'lesson_id': 'intro-quantum',
  'title': 'Introduction to Quantum Computing',
  'description': 'What quantum computers are and why they differ from classical computers.',
  'difficulty': 'beginner',
  'order': 1,
  'learning_objectives': ['Explain the difference between classical and quantum computing',
                          'Describe a qubit and its two basis states',
                          'Identify why quantum computers are not simply faster classical computers'],
  'related_experiments': ['superposition'],
  'content': ('A classical computer stores information in **bits**, which are either `0` or `1`.\n'
              '\n'
              'A quantum computer uses **qubits**. A qubit has two basis states, written $|0⟩$ and $|1⟩$. '
              'Before measurement, it can exist in a *superposition* of both.\n'
              '\n'
              'Quantum computers are not simply faster laptops. They are useful when a problem can be '
              'expressed so that quantum effects—superposition, interference, and entanglement—help '
              'compute a result.'),
  'prerequisites': [],
  'references': [{'title': 'IBM Quantum Learning: basics',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}]},
 {'lesson_id': 'superposition',
  'title': 'Superposition and the Hadamard Gate',
  'description': 'Create an equal superposition with the Hadamard gate.',
  'difficulty': 'beginner',
  'order': 2,
  'learning_objectives': ['Explain superposition',
                          'Describe what a Hadamard gate does',
                          'Predict ideal measurement probabilities'],
  'related_experiments': ['superposition', 'interference'],
  'content': ('A qubit begins in $|0⟩$. Applying a **Hadamard gate** (`H`) creates an equal '
              'superposition:\n'
              '\n'
              '$$\n'
              '|0⟩ \\xrightarrow{H} \\frac{|0⟩ + |1⟩}{\\sqrt{2}}\n'
              '$$\n'
              '\n'
              'When measured once, the result is either `0` or `1`; a single outcome is random. Across '
              'many shots, an ideal device produces `0` and `1` about 50% each.'),
  'prerequisites': ['intro-quantum'],
  'references': [{'title': 'IBM Quantum Learning: basics',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}]},
 {'lesson_id': 'entanglement',
  'title': 'Entanglement and Bell States',
  'description': 'Use H and CX to create correlated two-qubit measurements.',
  'difficulty': 'beginner',
  'order': 3,
  'learning_objectives': ['Create a Bell state',
                          'Explain correlated measurement outcomes',
                          'Distinguish entanglement from independent randomness'],
  'related_experiments': ['bell_entanglement'],
  'content': ('Start with two qubits in $|00⟩$. Apply `H` to qubit 0, then apply `CX` with qubit 0 as '
              'control and qubit 1 as target:\n'
              '\n'
              '$$\n'
              '|00⟩ \\xrightarrow{I \\otimes H} \\frac{|00⟩ + |01⟩}{\\sqrt{2}}\n'
              '\\xrightarrow{CX} \\frac{|00⟩ + |11⟩}{\\sqrt{2}}\n'
              '$$\n'
              '\n'
              'The result is a Bell state. Measurement yields `00` or `11`, each ideally with probability '
              '50%. The outcomes are correlated: you never see `01` or `10` in the ideal circuit.\n'
              '\n'
              'This correlation is stronger than two independent coins: measuring one qubit tells you '
              'something definite about the other.'),
  'prerequisites': ['superposition'],
  'references': [{'title': 'IBM Quantum Learning: basics',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}]},
 {'lesson_id': 'gates',
  'title': 'Quantum Gates',
  'description': 'X, Y, Z, Hadamard, CNOT, and measurement.',
  'difficulty': 'beginner',
  'order': 4,
  'learning_objectives': ['Identify common single- and two-qubit gates',
                          'Explain measurement',
                          'Interpret circuit diagrams'],
  'related_experiments': ['superposition', 'bell_entanglement', 'interference'],
  'content': ('- **X**: flips $|0⟩$ to $|1⟩$ and $|1⟩$ to $|0⟩$.\n'
              '- **Y**: rotates a qubit around the Y axis of the Bloch sphere.\n'
              '- **Z**: applies a phase flip; it changes relative phase rather than measurement '
              'probabilities for basis states.\n'
              '- **H**: creates or removes superposition.\n'
              '- **CX / CNOT**: flips the target qubit when the control qubit is `1`; essential for '
              'entanglement.\n'
              '- **Measure**: converts a qubit state into a classical bit.\n'
              '\n'
              'Circuits are read left to right. Each horizontal line is a qubit wire; boxes are gates; '
              'meters represent measurement.'),
  'prerequisites': ['entanglement'],
  'references': [{'title': 'IBM Quantum Learning: basics',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}]},
 {'lesson_id': 'hardware-noise',
  'title': 'Quantum Hardware and Noise',
  'description': 'Why real quantum results differ from ideal simulations.',
  'difficulty': 'beginner',
  'order': 5,
  'learning_objectives': ['Explain hardware noise',
                          'Compare ideal and real results',
                          'Interpret small deviations from expected probabilities'],
  'related_experiments': ['superposition', 'bell_entanglement', 'interference'],
  'content': ('Real quantum processors are physical devices. Their qubits and gates are imperfect, so '
              'results can include:\n'
              '\n'
              '- **Gate errors**: a gate does not perform its intended transformation perfectly.\n'
              '- **Measurement errors**: a `0` may occasionally be read as `1`, or vice versa.\n'
              '- **Decoherence**: qubits lose quantum information over time.\n'
              '\n'
              'Therefore, a Bell-state circuit may produce a few `01` or `10` outcomes on hardware even '
              'though the ideal circuit predicts none. Small deviations are normal; the goal is to compare '
              'the observed distribution with the ideal distribution.'),
  'prerequisites': ['gates'],
  'references': [{'title': 'IBM Quantum Learning: basics',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}]},
 {'lesson_id': 'complex-amplitudes',
  'title': 'Statevectors, Complex Amplitudes, and Measurement',
  'description': 'Connect linear algebra, the Bloch sphere, relative phase, and Born probabilities.',
  'difficulty': 'intermediate',
  'prerequisites': ['superposition', 'gates'],
  'related_experiments': ['superposition', 'qft_phase'],
  'learning_objectives': ['Normalize a complex statevector',
                          'Distinguish amplitudes from probabilities',
                          'Explain global and relative phase'],
  'content': ('A pure qubit state is\n'
              '$$\n'
              '|\\psi\\rangle=\\alpha|0\\rangle+\\beta|1\\rangle,\\qquad |\\alpha|^2+|\\beta|^2=1.\n'
              '$$\n'
              'The **Born rule** gives $P(0)=|\\alpha|^2$ and $P(1)=|\\beta|^2$. The amplitudes are '
              'complex numbers, not ordinary probabilities.\n'
              '\n'
              'For example, $(|0\\rangle+i|1\\rangle)/\\sqrt{2}$ gives 50/50 computational-basis counts. '
              'So does $(|0\\rangle-|1\\rangle)/\\sqrt{2}$, even though these states have different '
              'relative phases. A later gate can turn those phase differences into different measurement '
              'statistics.\n'
              '\n'
              'Up to global phase, write\n'
              '$$\n'
              '|\\psi\\rangle=\\cos(\\theta/2)|0\\rangle+e^{i\\phi}\\sin(\\theta/2)|1\\rangle.\n'
              '$$\n'
              'This is the Bloch-sphere parameterization. Multiplying the whole state by $e^{i\\gamma}$ '
              'changes no observable probabilities. Changing the phase of one component relative to '
              'another can matter.\n'
              '\n'
              'For several qubits, tensor products define the joint space. Qiskit displays '
              "$|q_{n-1}\\ldots q_0\\rangle$: qubit 0 is the rightmost bit. The QFT lab's amplitude table "
              'uses this convention.\n'
              '\n'
              '**Worked example:** for $\\alpha=\\sqrt{3}/2$ and $\\beta=i/2$, the squared magnitudes add '
              'to 1 and $P(1)=1/4$.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}],
  'order': 6},
 {'lesson_id': 'phase-kickback',
  'title': 'Relative Phase and Phase Kickback',
  'description': "Use an eigenstate target to make a controlled gate change the control's phase.",
  'difficulty': 'intermediate',
  'prerequisites': ['complex-amplitudes'],
  'related_experiments': ['phase_kickback', 'deutsch_jozsa'],
  'learning_objectives': ['Use the eigenvalue equation for a controlled operation',
                          'Trace kickback through a CNOT',
                          'Convert relative phase into a deterministic measurement'],
  'content': ('If $U|u\\rangle=e^{i\\phi}|u\\rangle$, then a controlled-U operation acts as\n'
              '$$\n'
              '(\\alpha|0\\rangle+\\beta|1\\rangle)|u\\rangle\n'
              '\\longmapsto\n'
              '(\\alpha|0\\rangle+e^{i\\phi}\\beta|1\\rangle)|u\\rangle.\n'
              '$$\n'
              'The target keeps its eigenstate while the control acquires a relative phase.\n'
              '\n'
              'In this lab, prepare the target in $|-\\rangle=(|0\\rangle-|1\\rangle)/\\sqrt{2}$ using X '
              'then H. Since $X|-\\rangle=-|-\\rangle$, a CNOT with a $|+\\rangle$ control changes the '
              'control to $|-\\rangle$. A final H converts it to $|1\\rangle$.\n'
              '\n'
              '**Trace the circuit:** target X,H; control H; CX(control,target); control H; measure only '
              'the control. The single classical output should be 1. The unmeasured target is still '
              '$|-\\rangle$.\n'
              '\n'
              'This is phase kickback, a building block for oracle algorithms and phase estimation. A '
              "phase that would be global for a target alone becomes relative between the control's "
              'branches.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms'}],
  'order': 7},
 {'lesson_id': 'multipartite-entanglement',
  'title': 'GHZ States, Correlations, and Coherence',
  'description': 'Build a three-qubit entangled state and understand what counts can and cannot prove.',
  'difficulty': 'intermediate',
  'prerequisites': ['entanglement', 'complex-amplitudes'],
  'related_experiments': ['ghz_entanglement'],
  'learning_objectives': ['Prepare a GHZ state',
                          'Distinguish coherent entanglement from a classical mixture',
                          'Choose a complementary measurement basis'],
  'content': ('H on qubit 0 followed by CX(0,1) and CX(0,2) prepares\n'
              '$$\n'
              '|\\mathrm{GHZ}\\rangle=\\frac{|000\\rangle+|111\\rangle}{\\sqrt{2}}.\n'
              '$$\n'
              'All three computational-basis outcomes agree: 000 or 111, ideally with equal probability.\n'
              '\n'
              'Those counts alone do **not** prove coherent entanglement. The classical mixture\n'
              '$$\n'
              '\\rho_{\\mathrm{mix}}=\\tfrac12|000\\rangle\\langle000|+\\tfrac12|111\\rangle\\langle111|\n'
              '$$\n'
              'has the same Z-basis distribution. The pure GHZ density matrix additionally contains '
              'off-diagonal coherence terms.\n'
              '\n'
              'A complementary test measures X on each qubit, implemented by H before Z measurement. The '
              'plus GHZ state has $\\langle X\\otimes X\\otimes X\\rangle=1$, while the mixture has '
              'expectation 0. The standard lab shows the Z-basis experiment; reproducing an X-basis test '
              'requires an additional measurement circuit.\n'
              '\n'
              '**Try it:** compare the two nonzero simulator amplitudes with the three-bit histogram. '
              'Increase shots to reduce sampling uncertainty, then consider what real-device errors would '
              'add.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}],
  'order': 8},
 {'lesson_id': 'deutsch-jozsa',
  'title': 'Deutsch–Jozsa and Quantum Oracle Queries',
  'description': 'Solve a promised constant-versus-balanced problem with interference.',
  'difficulty': 'advanced',
  'prerequisites': ['phase-kickback'],
  'related_experiments': ['deutsch_jozsa'],
  'learning_objectives': ['State the constant-or-balanced promise',
                          'Trace a reversible oracle',
                          'Interpret the final input register'],
  'content': ('For $f:\\{0,1\\}^n\\to\\{0,1\\}$, the promise is that f is either constant or balanced '
              '(half of inputs map to 1). A reversible oracle performs\n'
              '$$\n'
              'U_f|x\\rangle|y\\rangle=|x\\rangle|y\\oplus f(x)\\rangle.\n'
              '$$\n'
              'With the output qubit in $|-\\rangle$, phase kickback gives\n'
              '$$\n'
              '2^{-n/2}\\sum_x(-1)^{f(x)}|x\\rangle|-\\rangle.\n'
              '$$\n'
              'After H on every input qubit, the amplitude for the all-zero input outcome is\n'
              '$$\n'
              '2^{-n}\\sum_x(-1)^{f(x)}.\n'
              '$$\n'
              'Its magnitude is 1 for constant functions and 0 for balanced ones.\n'
              '\n'
              'The lab fixes $n=2$ and $f(x_0,x_1)=x_0$, implemented by CX(0,2). Qubit 2 is the unmeasured '
              'output ancilla. Only inputs q0 and q1 are measured. The output is **01** in displayed '
              '$c_1c_0$ order, identifying a balanced oracle.\n'
              '\n'
              'A deterministic classical algorithm can require $2^{n-1}+1$ queries in the worst case under '
              'this promise; the ideal quantum algorithm uses one oracle query. Oracle construction and '
              'noisy implementation costs are separate. Randomized classical query complexity has '
              'different guarantees.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms'}],
  'order': 9},
 {'lesson_id': 'grover-search',
  'title': 'Grover Search and Amplitude Amplification',
  'description': 'Use a phase oracle and diffusion to amplify one marked basis state.',
  'difficulty': 'advanced',
  'prerequisites': ['phase-kickback', 'complex-amplitudes'],
  'related_experiments': ['grover_search'],
  'learning_objectives': ['Represent a marked item with a phase oracle',
                          'Explain diffusion about the mean',
                          'Separate query complexity from end-to-end speedup'],
  'content': ('For one marked item $w$ among N basis states, Grover search starts with the uniform state '
              '$|s\\rangle$. The phase oracle changes the sign of the marked amplitude:\n'
              '$$\n'
              'O_w=I-2|w\\rangle\\langle w|.\n'
              '$$\n'
              'Diffusion is $D=2|s\\rangle\\langle s|-I$. The iterate $DO_w$ rotates the state toward the '
              'marked subspace. With $\\sin\\theta=1/\\sqrt N$, the success probability after r iterations '
              'is $\\sin^2((2r+1)\\theta)$.\n'
              '\n'
              'The lab has two qubits, $N=4$, and marks **11** with CZ. One oracle-plus-diffusion '
              'iteration gives ideal success probability 1. The implemented H-X-CZ-X-H diffusion differs '
              'from D by an irrelevant global sign.\n'
              '\n'
              '**Worked example:** begin with amplitudes $(1/2,1/2,1/2,1/2)$. The oracle gives '
              '$(1/2,1/2,1/2,-1/2)$, whose mean is 1/4. Reflection about that mean yields amplitudes '
              '$(0,0,0,1)$, up to global phase.\n'
              '\n'
              'General unstructured search uses $O(\\sqrt N)$ oracle queries. This is not a claim that '
              'loading arbitrary classical data or building the oracle is free. Too many iterations rotate '
              'amplitude away from the marked state.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms'}],
  'order': 10},
 {'lesson_id': 'quantum-fourier-transform',
  'title': 'Quantum Fourier Transform and Phase Encoding',
  'description': 'Read complex phases that a measurement histogram alone cannot reveal.',
  'difficulty': 'advanced',
  'prerequisites': ['complex-amplitudes', 'phase-kickback'],
  'related_experiments': ['qft_phase'],
  'learning_objectives': ['Apply the QFT to a basis state',
                          'Interpret controlled-phase gates and output swaps',
                          'Explain why inverse QFT is needed to decode phase'],
  'content': ('For $N=2^n$, the quantum Fourier transform is the unitary\n'
              '$$\n'
              '\\mathrm{QFT}_N|x\\rangle=\\frac1{\\sqrt N}\\sum_{y=0}^{N-1}e^{2\\pi ixy/N}|y\\rangle.\n'
              '$$\n'
              'It transforms amplitudes, not a classical list that can all be read out for free.\n'
              '\n'
              'The lab prepares $x=1$ as $|q_1q_0\\rangle=|01\\rangle$ and applies the two-qubit QFT. The '
              'resulting amplitudes for 00, 01, 10, 11 are\n'
              '$$\n'
              '\\tfrac12,\\quad \\tfrac i2,\\quad -\\tfrac12,\\quad -\\tfrac i2.\n'
              '$$\n'
              'Every computational-basis probability is 1/4. The amplitude table exposes the relative '
              'phases that the histogram cannot show. Multiplying all amplitudes by the same phase would '
              'change none of these probabilities.\n'
              '\n'
              'The circuit uses Hadamards, a controlled phase of $\\pi/2$, and a SWAP to account for '
              'output bit order. Its inverse reverses the gate order and negates phase angles. Applying '
              'that inverse returns this state to 01.\n'
              '\n'
              'Phase estimation uses controlled powers of a unitary to encode an eigenphase, followed by '
              'inverse QFT to make the phase measurable. The lab demonstrates the QFT building block, not '
              'a full phase-estimation or factoring algorithm.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms'}],
  'order': 11},
 {'lesson_id': 'quantum-teleportation',
  'title': 'Teleportation and Deferred Measurement',
  'description': 'Transfer a prepared state and distinguish coherent verification from classical '
                 'feed-forward.',
  'difficulty': 'advanced',
  'prerequisites': ['entanglement', 'complex-amplitudes'],
  'related_experiments': ['quantum_teleportation'],
  'learning_objectives': ['Identify the shared Bell pair and Bell-basis transformation',
                          'Explain the two classical correction bits',
                          'Understand the limits of a single-basis verification'],
  'content': ('Standard teleportation transfers an unknown qubit state using a shared Bell pair and two '
              'classical bits. Alice performs CX and H, measures her two qubits, and sends the outcomes to '
              'Bob. Bob applies X and Z corrections conditioned on those outcomes. No usable information '
              'arrives faster than the classical message, and the original unknown state is not copied.\n'
              '\n'
              'The lab prepares $|+\\rangle$ on q0 and a Bell pair on q1,q2. It applies CX(0,1), H(0), '
              'then coherent corrections CX(1,2), CZ(0,2). By deferred measurement these controlled '
              'operations reproduce the corrected receiver state while leaving the two would-be '
              'measurement qubits unmeasured.\n'
              '\n'
              'Finally H on q2 rotates the X basis to Z before measuring q2 into c0. A correct '
              '$|+\\rangle$ receiver gives classical output **0** with probability 1.\n'
              '\n'
              'This is a **coherent, deferred-measurement demonstration**. Its two controlled correction '
              'gates require quantum connectivity; it does not implement separated laboratories '
              'communicating only classical bits. It verifies a known input in one basis, not '
              'arbitrary-state teleportation fidelity or full state tomography.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/basics-of-quantum-information'}],
  'order': 12},
 {'lesson_id': 'quantum-error-correction',
  'title': 'Repetition Codes, Syndromes, and Error Correction',
  'description': 'Encode a logical qubit and correct one deliberately injected bit flip.',
  'difficulty': 'advanced',
  'prerequisites': ['multipartite-entanglement'],
  'related_experiments': ['bit_flip_correction'],
  'learning_objectives': ['Encode a logical qubit without cloning it',
                          'Distinguish a syndrome from a logical measurement',
                          'State the limitations of the repetition code'],
  'content': ('The three-qubit repetition code encodes\n'
              '$$\n'
              '\\alpha|0\\rangle+\\beta|1\\rangle\\longmapsto\\alpha|000\\rangle+\\beta|111\\rangle.\n'
              '$$\n'
              'This is an entangled encoding, not three independent copies of an unknown qubit.\n'
              '\n'
              'Parity checks such as $Z_0Z_1$ and $Z_1Z_2$ form error syndromes. They locate a single X '
              'error without revealing the logical amplitudes. A complete correction cycle measures '
              'appropriate ancillas and applies a recovery operation.\n'
              '\n'
              'The fixed lab initializes q0 to 1, encodes with two CNOTs, deliberately flips q0, and '
              'decodes with two CNOTs. A Toffoli controlled by q1 and q2 restores q0. Only q0 is measured; '
              'the ideal output is **1**. The other qubits retain syndrome information. This coherent '
              'decode-and-recover circuit is a compact demonstration rather than a fault-tolerant repeated '
              'syndrome-extraction cycle.\n'
              '\n'
              'The code corrects one bit-flip error but does not protect against a general phase error. '
              'Two bit flips can cause a logical failure. Protecting arbitrary errors requires richer '
              'codes and suitable fault-tolerant operations.\n'
              '\n'
              '**Worked example:** 111 becomes 110 after X on the rightmost q0. Decoding exposes syndrome '
              'bits 11; the final controlled-controlled-X restores the logical bit.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/foundations-of-quantum-error-correction'}],
  'order': 13},
 {'lesson_id': 'variational-methods',
  'title': 'Variational Algorithms and Expectation Values',
  'description': 'Connect parameterized circuits to classical optimization and honest measurement estimates.',
  'difficulty': 'advanced',
  'prerequisites': ['complex-amplitudes', 'quantum-fourier-transform'],
  'related_experiments': ['phase_kickback', 'grover_search'],
  'learning_objectives': ['Define a variational cost function',
                          'Explain Pauli measurements and shot uncertainty',
                          'Separate a fixed circuit demonstration from an optimizer'],
  'content': ('A variational algorithm prepares '
              '$|\\psi(\\boldsymbol\\theta)\\rangle=U(\\boldsymbol\\theta)|0\\ldots0\\rangle$ and '
              'minimizes a measured cost, for example\n'
              '$$\n'
              'E(\\boldsymbol\\theta)=\\langle\\psi(\\boldsymbol\\theta)|H|\\psi(\\boldsymbol\\theta)\\rangle.\n'
              '$$\n'
              'In VQE, $H=\\sum_j h_jP_j$ is a weighted sum of Pauli strings, so the energy is '
              'reconstructed from several expectation estimates. Measuring Z uses the computational basis; '
              'measuring X requires H first; measuring Y can use S-dagger then H. Different observables '
              'may require separate circuit executions.\n'
              '\n'
              '**Worked example:** for $H=Z$ and $|\\psi(\\theta)\\rangle=R_y(\\theta)|0\\rangle$, the '
              'exact cost is $\\cos\\theta$. With Z counts, estimate it as $(n_0-n_1)/(n_0+n_1)$. A '
              'classical optimizer proposes the next angle.\n'
              '\n'
              'For suitable gates with a two-eigenvalue generator, parameter-shift rules can express '
              'derivatives using shifted circuit evaluations. Finite shots introduce uncertainty; noise, '
              'optimizer choice, and flat landscapes affect convergence.\n'
              '\n'
              'The Playground currently runs fixed guided circuits. Its gate explanations, probabilities, '
              'and amplitude table provide the prerequisites for a variational workflow; it does **not** '
              'run a VQE optimizer or claim a variational speedup.'),
  'references': [{'title': 'Continue with IBM Quantum Learning',
                  'url': 'https://quantum.cloud.ibm.com/learning/en/courses/fundamentals-of-quantum-algorithms'}],
  'order': 14}]

EXPERIMENTS = {'superposition': {'experiment_id': 'superposition',
                   'title': 'Superposition',
                   'description': 'Put one qubit into an equal superposition of |0⟩ and |1⟩ using a Hadamard '
                                  'gate.',
                   'qubits': 1,
                   'classical_bits': 1,
                   'gates': [{'name': 'H',
                              'qubits': [0],
                              'explanation': 'Creates an equal superposition of |0⟩ and |1⟩.'},
                             {'name': 'Measure',
                              'qubits': [0],
                              'explanation': 'Reads the qubit as a classical bit.',
                              'classical_bits': [0]}],
                   'qiskit_code': 'from math import pi\n'
                                  'from qiskit import QuantumCircuit\n'
                                  '\n'
                                  'qc = QuantumCircuit(1, 1)\n'
                                  'qc.h(0)\n'
                                  'qc.measure([0], [0])',
                   'ideal_probabilities': {'0': 0.5, '1': 0.5},
                   'interpretation': 'A single shot is unpredictable, but many shots should approach 50% `0` '
                                     'and 50% `1`.',
                   'next_experiment': 'bell_entanglement',
                   'difficulty': 'beginner',
                   'lesson_id': 'superposition'},
 'bell_entanglement': {'experiment_id': 'bell_entanglement',
                       'title': 'Bell-State Entanglement',
                       'description': 'Create an entangled pair whose measurements are perfectly correlated.',
                       'qubits': 2,
                       'classical_bits': 2,
                       'gates': [{'name': 'H',
                                  'qubits': [0],
                                  'explanation': 'Puts qubit 0 into superposition.'},
                                 {'name': 'CX',
                                  'qubits': [0, 1],
                                  'explanation': 'Entangles qubit 1 with qubit 0.'},
                                 {'name': 'Measure',
                                  'qubits': [0, 1],
                                  'explanation': 'Measures both qubits.',
                                  'classical_bits': [0, 1]}],
                       'qiskit_code': 'from math import pi\n'
                                      'from qiskit import QuantumCircuit\n'
                                      '\n'
                                      'qc = QuantumCircuit(2, 2)\n'
                                      'qc.h(0)\n'
                                      'qc.cx(0, 1)\n'
                                      'qc.measure([0, 1], [0, 1])',
                       'ideal_probabilities': {'00': 0.5, '01': 0.0, '10': 0.0, '11': 0.5},
                       'interpretation': 'The ideal Bell state produces only `00` and `11`. Hardware noise '
                                         'can introduce a small number of `01` or `10` outcomes.',
                       'next_experiment': 'interference',
                       'difficulty': 'beginner',
                       'lesson_id': 'entanglement'},
 'interference': {'experiment_id': 'interference',
                  'title': 'Quantum Interference',
                  'description': 'Apply two Hadamard gates and observe constructive interference back to '
                                 '|0⟩.',
                  'qubits': 1,
                  'classical_bits': 1,
                  'gates': [{'name': 'H', 'qubits': [0], 'explanation': 'Creates superposition.'},
                            {'name': 'H',
                             'qubits': [0],
                             'explanation': 'Interferes the paths, returning the qubit to |0⟩.'},
                            {'name': 'Measure',
                             'qubits': [0],
                             'explanation': 'Reads the qubit.',
                             'classical_bits': [0]}],
                  'qiskit_code': 'from math import pi\n'
                                 'from qiskit import QuantumCircuit\n'
                                 '\n'
                                 'qc = QuantumCircuit(1, 1)\n'
                                 'qc.h(0)\n'
                                 'qc.h(0)\n'
                                 'qc.measure([0], [0])',
                  'ideal_probabilities': {'0': 1.0, '1': 0.0},
                  'interpretation': 'The two Hadamard gates interfere constructively for `0` and '
                                    'destructively for `1`, so an ideal simulator returns `0` every time.',
                  'next_experiment': 'phase_kickback',
                  'difficulty': 'beginner',
                  'lesson_id': 'phase-kickback'},
 'phase_kickback': {'experiment_id': 'phase_kickback',
                    'title': 'Phase Kickback',
                    'difficulty': 'intermediate',
                    'lesson_id': 'phase-kickback',
                    'qubits': 2,
                    'classical_bits': 1,
                    'description': 'Prepare an X-eigenstate target and read its eigenvalue through the '
                                   'control.',
                    'gates': [{'name': 'X', 'qubits': [1], 'explanation': 'Start the target in |1>.'},
                              {'name': 'H',
                               'qubits': [1],
                               'explanation': 'Prepare the target eigenstate |->.'},
                              {'name': 'H', 'qubits': [0], 'explanation': 'Prepare the control in |+>.'},
                              {'name': 'CX',
                               'qubits': [0, 1],
                               'explanation': "The target eigenvalue -1 changes the control's relative "
                                              'phase.'},
                              {'name': 'H',
                               'qubits': [0],
                               'explanation': 'Convert the control phase into |1>.'},
                              {'name': 'Measure',
                               'qubits': [0],
                               'explanation': 'Read only the control into c0.',
                               'classical_bits': [0]}],
                    'ideal_probabilities': {'0': 0, '1': 1},
                    'interpretation': 'The measured control is 1 even though CNOT never flips the control '
                                      'directly. The unmeasured target remains |->.',
                    'next_experiment': 'ghz_entanglement',
                    'qiskit_code': 'from math import pi\n'
                                   'from qiskit import QuantumCircuit\n'
                                   '\n'
                                   'qc = QuantumCircuit(2, 1)\n'
                                   'qc.x(1)\n'
                                   'qc.h(1)\n'
                                   'qc.h(0)\n'
                                   'qc.cx(0, 1)\n'
                                   'qc.h(0)\n'
                                   'qc.measure([0], [0])'},
 'ghz_entanglement': {'experiment_id': 'ghz_entanglement',
                      'title': 'Three-Qubit GHZ State',
                      'difficulty': 'intermediate',
                      'lesson_id': 'multipartite-entanglement',
                      'qubits': 3,
                      'classical_bits': 3,
                      'description': 'Create a coherent three-qubit superposition with correlated '
                                     'measurements.',
                      'gates': [{'name': 'H', 'qubits': [0], 'explanation': 'Create two coherent branches.'},
                                {'name': 'CX', 'qubits': [0, 1], 'explanation': 'Correlate q1 with q0.'},
                                {'name': 'CX',
                                 'qubits': [0, 2],
                                 'explanation': 'Extend the correlation to q2.'},
                                {'name': 'Measure',
                                 'qubits': [0, 1, 2],
                                 'explanation': 'Read all three qubits into matching classical bits.',
                                 'classical_bits': [0, 1, 2]}],
                      'ideal_probabilities': {'100': 0,
                                              '101': 0,
                                              '110': 0,
                                              '111': 0.5,
                                              '000': 0.5,
                                              '001': 0,
                                              '010': 0,
                                              '011': 0},
                      'interpretation': 'Only 000 and 111 appear ideally. These Z-basis counts alone also '
                                        'fit a classical mixture; additional bases are needed to test '
                                        'coherence.',
                      'next_experiment': 'deutsch_jozsa',
                      'qiskit_code': 'from math import pi\n'
                                     'from qiskit import QuantumCircuit\n'
                                     '\n'
                                     'qc = QuantumCircuit(3, 3)\n'
                                     'qc.h(0)\n'
                                     'qc.cx(0, 1)\n'
                                     'qc.cx(0, 2)\n'
                                     'qc.measure([0, 1, 2], [0, 1, 2])'},
 'deutsch_jozsa': {'experiment_id': 'deutsch_jozsa',
                   'title': 'Deutsch–Jozsa: Balanced Oracle',
                   'difficulty': 'advanced',
                   'lesson_id': 'deutsch-jozsa',
                   'qubits': 3,
                   'classical_bits': 2,
                   'description': 'Use one query to the fixed balanced oracle f(x0,x1)=x0.',
                   'gates': [{'name': 'X',
                              'qubits': [2],
                              'explanation': 'Initialize the oracle output qubit in |1>.'},
                             {'name': 'H', 'qubits': [0], 'explanation': 'Put input q0 in superposition.'},
                             {'name': 'H', 'qubits': [1], 'explanation': 'Put input q1 in superposition.'},
                             {'name': 'H', 'qubits': [2], 'explanation': 'Prepare the oracle output in |->.'},
                             {'name': 'CX',
                              'qubits': [0, 2],
                              'explanation': 'Implement the reversible oracle y XOR x0.'},
                             {'name': 'H',
                              'qubits': [0],
                              'explanation': 'Interfere the phase-encoded inputs.'},
                             {'name': 'H',
                              'qubits': [1],
                              'explanation': 'Finish the input Hadamard transform.'},
                             {'name': 'Measure',
                              'qubits': [0, 1],
                              'explanation': 'Measure only the input register.',
                              'classical_bits': [0, 1]}],
                   'ideal_probabilities': {'10': 0, '11': 0, '00': 0, '01': 1},
                   'interpretation': '01 is nonzero, so this promised oracle is balanced. Displayed c1c0 '
                                     'order puts input q0 on the right; the output ancilla is not measured.',
                   'next_experiment': 'grover_search',
                   'qiskit_code': 'from math import pi\n'
                                  'from qiskit import QuantumCircuit\n'
                                  '\n'
                                  'qc = QuantumCircuit(3, 2)\n'
                                  'qc.x(2)\n'
                                  'qc.h(0)\n'
                                  'qc.h(1)\n'
                                  'qc.h(2)\n'
                                  'qc.cx(0, 2)\n'
                                  'qc.h(0)\n'
                                  'qc.h(1)\n'
                                  'qc.measure([0, 1], [0, 1])'},
 'grover_search': {'experiment_id': 'grover_search',
                   'title': 'Grover Search for 11',
                   'difficulty': 'advanced',
                   'lesson_id': 'grover-search',
                   'qubits': 2,
                   'classical_bits': 2,
                   'description': 'Mark 11 with a phase oracle, then amplify it using one diffusion step.',
                   'gates': [{'name': 'H', 'qubits': [0], 'explanation': 'Prepare a uniform search state.'},
                             {'name': 'H',
                              'qubits': [1],
                              'explanation': 'Complete the uniform two-qubit state.'},
                             {'name': 'CZ',
                              'qubits': [0, 1],
                              'explanation': 'The oracle changes the sign of the 11 amplitude.'},
                             {'name': 'H',
                              'qubits': [0],
                              'explanation': 'Begin diffusion in the Hadamard basis.'},
                             {'name': 'H', 'qubits': [1], 'explanation': 'Transform the second qubit.'},
                             {'name': 'X',
                              'qubits': [0],
                              'explanation': 'Map the zero-state reflection to a controlled phase.'},
                             {'name': 'X', 'qubits': [1], 'explanation': 'Map the second reflection input.'},
                             {'name': 'CZ',
                              'qubits': [0, 1],
                              'explanation': 'Reflect the joint amplitude, up to a global sign.'},
                             {'name': 'X', 'qubits': [0], 'explanation': 'Undo the first X mapping.'},
                             {'name': 'X', 'qubits': [1], 'explanation': 'Undo the second X mapping.'},
                             {'name': 'H',
                              'qubits': [0],
                              'explanation': 'Finish the first diffusion transform.'},
                             {'name': 'H', 'qubits': [1], 'explanation': 'Finish diffusion and amplify 11.'},
                             {'name': 'Measure',
                              'qubits': [0, 1],
                              'explanation': 'Read the amplified marked state.',
                              'classical_bits': [0, 1]}],
                   'ideal_probabilities': {'10': 0, '11': 1, '00': 0, '01': 0},
                   'interpretation': 'One Grover iteration finds the unique marked state 11 with ideal '
                                     'probability 1 for a four-item search. Oracle construction costs are '
                                     'outside this fixed demonstration.',
                   'next_experiment': 'qft_phase',
                   'qiskit_code': 'from math import pi\n'
                                  'from qiskit import QuantumCircuit\n'
                                  '\n'
                                  'qc = QuantumCircuit(2, 2)\n'
                                  'qc.h(0)\n'
                                  'qc.h(1)\n'
                                  'qc.cz(0, 1)\n'
                                  'qc.h(0)\n'
                                  'qc.h(1)\n'
                                  'qc.x(0)\n'
                                  'qc.x(1)\n'
                                  'qc.cz(0, 1)\n'
                                  'qc.x(0)\n'
                                  'qc.x(1)\n'
                                  'qc.h(0)\n'
                                  'qc.h(1)\n'
                                  'qc.measure([0, 1], [0, 1])'},
 'qft_phase': {'experiment_id': 'qft_phase',
               'title': 'Quantum Fourier Transform',
               'difficulty': 'advanced',
               'lesson_id': 'quantum-fourier-transform',
               'qubits': 2,
               'classical_bits': 2,
               'description': 'Encode the basis input 01 into four equal magnitudes with distinct phases.',
               'gates': [{'name': 'X', 'qubits': [0], 'explanation': 'Prepare |q1 q0> = |01>.'},
                         {'name': 'H',
                          'qubits': [1],
                          'explanation': 'Begin the QFT on the highest-index qubit.'},
                         {'name': 'CP',
                          'qubits': [0, 1],
                          'explanation': 'Apply a controlled phase of pi/2.',
                          'angle': 1.5707963267948966,
                          'label': 'P(pi/2)'},
                         {'name': 'H', 'qubits': [0], 'explanation': 'Transform the low-index qubit.'},
                         {'name': 'SWAP',
                          'qubits': [0, 1],
                          'explanation': 'Reverse the output order to match the QFT convention.'},
                         {'name': 'Measure',
                          'qubits': [0, 1],
                          'explanation': 'Measure both qubits in the computational basis.',
                          'classical_bits': [0, 1]}],
               'ideal_probabilities': {'10': 0.25, '11': 0.25, '00': 0.25, '01': 0.25},
               'interpretation': 'All outcomes have probability 25%, but their amplitudes are 1/2, i/2, '
                                 '-1/2, -i/2. Inspect the simulator phase table; Z-basis counts cannot '
                                 'reveal these phases.',
               'next_experiment': 'quantum_teleportation',
               'qiskit_code': 'from math import pi\n'
                              'from qiskit import QuantumCircuit\n'
                              '\n'
                              'qc = QuantumCircuit(2, 2)\n'
                              'qc.x(0)\n'
                              'qc.h(1)\n'
                              'qc.cp(pi / 2, 0, 1)\n'
                              'qc.h(0)\n'
                              'qc.swap(0, 1)\n'
                              'qc.measure([0, 1], [0, 1])'},
 'quantum_teleportation': {'experiment_id': 'quantum_teleportation',
                           'title': 'Teleportation: Deferred Measurement',
                           'difficulty': 'advanced',
                           'lesson_id': 'quantum-teleportation',
                           'qubits': 3,
                           'classical_bits': 1,
                           'description': 'Transfer a known |+> state with coherent corrections and verify '
                                          'the receiver in the X basis.',
                           'gates': [{'name': 'H',
                                      'qubits': [0],
                                      'explanation': 'Prepare the known |+> message.'},
                                     {'name': 'H',
                                      'qubits': [1],
                                      'explanation': 'Begin preparing a shared Bell pair.'},
                                     {'name': 'CX',
                                      'qubits': [1, 2],
                                      'explanation': 'Entangle the resource qubits.'},
                                     {'name': 'CX',
                                      'qubits': [0, 1],
                                      'explanation': 'Begin the Bell-basis transformation.'},
                                     {'name': 'H',
                                      'qubits': [0],
                                      'explanation': 'Finish the Bell-basis transformation.'},
                                     {'name': 'CX',
                                      'qubits': [1, 2],
                                      'explanation': 'Apply the coherent X correction.'},
                                     {'name': 'CZ',
                                      'qubits': [0, 2],
                                      'explanation': 'Apply the coherent Z correction.'},
                                     {'name': 'H',
                                      'qubits': [2],
                                      'explanation': "Rotate the receiver's X basis to Z for verification."},
                                     {'name': 'Measure',
                                      'qubits': [2],
                                      'explanation': 'Read receiver q2 into the single classical bit c0.',
                                      'classical_bits': [0]}],
                           'ideal_probabilities': {'0': 1, '1': 0},
                           'interpretation': "Output 0 verifies the receiver's |+> state in the X basis. "
                                             'This coherent circuit uses quantum-controlled corrections; it '
                                             'is not a separated-party classical-feed-forward implementation '
                                             'or full tomography.',
                           'next_experiment': 'bit_flip_correction',
                           'qiskit_code': 'from math import pi\n'
                                          'from qiskit import QuantumCircuit\n'
                                          '\n'
                                          'qc = QuantumCircuit(3, 1)\n'
                                          'qc.h(0)\n'
                                          'qc.h(1)\n'
                                          'qc.cx(1, 2)\n'
                                          'qc.cx(0, 1)\n'
                                          'qc.h(0)\n'
                                          'qc.cx(1, 2)\n'
                                          'qc.cz(0, 2)\n'
                                          'qc.h(2)\n'
                                          'qc.measure([2], [0])'},
 'bit_flip_correction': {'experiment_id': 'bit_flip_correction',
                         'title': 'Three-Qubit Bit-Flip Correction',
                         'difficulty': 'advanced',
                         'lesson_id': 'quantum-error-correction',
                         'qubits': 3,
                         'classical_bits': 1,
                         'description': 'Encode logical 1, inject one X error, and recover the data qubit '
                                        'coherently.',
                         'gates': [{'name': 'X', 'qubits': [0], 'explanation': 'Prepare logical data |1>.'},
                                   {'name': 'CX',
                                    'qubits': [0, 1],
                                    'explanation': 'Encode the first redundant parity relation.'},
                                   {'name': 'CX',
                                    'qubits': [0, 2],
                                    'explanation': 'Complete the repetition-code word 111.'},
                                   {'name': 'X',
                                    'qubits': [0],
                                    'explanation': 'Deliberately flip the data qubit.'},
                                   {'name': 'CX',
                                    'qubits': [0, 1],
                                    'explanation': 'Decode the first syndrome bit.'},
                                   {'name': 'CX',
                                    'qubits': [0, 2],
                                    'explanation': 'Decode the second syndrome bit.'},
                                   {'name': 'CCX',
                                    'qubits': [1, 2, 0],
                                    'explanation': 'The two syndrome controls recover the data qubit.'},
                                   {'name': 'Measure',
                                    'qubits': [0],
                                    'explanation': 'Read only the recovered logical data into c0.',
                                    'classical_bits': [0]}],
                         'ideal_probabilities': {'0': 0, '1': 1},
                         'interpretation': 'Logical output 1 is recovered after one specified bit flip. '
                                           'Ancillas retain syndrome information. This code does not protect '
                                           'against general phase errors or two bit flips.',
                         'next_experiment': 'superposition',
                         'qiskit_code': 'from math import pi\n'
                                        'from qiskit import QuantumCircuit\n'
                                        '\n'
                                        'qc = QuantumCircuit(3, 1)\n'
                                        'qc.x(0)\n'
                                        'qc.cx(0, 1)\n'
                                        'qc.cx(0, 2)\n'
                                        'qc.x(0)\n'
                                        'qc.cx(0, 1)\n'
                                        'qc.cx(0, 2)\n'
                                        'qc.ccx(1, 2, 0)\n'
                                        'qc.measure([0], [0])'}}
