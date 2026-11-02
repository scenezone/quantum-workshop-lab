# Client pitching group dry run

## Goal

Check that a non-engineering audience can follow the three-minute story: the simulator predicts a distribution, quantum measurements produce sampled outcomes, and IBM hardware can differ because it is a physical noisy device.

## Before the session

- Invite 2-3 people from the client pitching group. Ask them not to prepare; the goal is to test first-time clarity.
- Configure the IBM account pool in the backend and confirm the public hardware status says hardware is enabled.
- Run each target experiment once on the simulator and hardware: `quantum_random_number`, `bell_entanglement`, and `grover_search`.
- Confirm simulator and hardware results can be displayed together. A completed IBM result is saved for that experiment and labeled as recorded if used as a fallback.
- Keep a simulator-only version ready in case the IBM queue is long. Do not describe saved results as live.

## Walk-through (about 12 minutes)

1. **Set expectations (1 min):** "We'll compare a local simulation with measurements from an IBM quantum processor. Hardware results are sampled and can be noisy."
2. **Quantum random bit (3 min):** Run the simulator and IBM hardware, explain the H gate creates equal measurement probabilities, and ask what a 50/50 result should look like over many shots.
3. **Bell state (3 min):** Explain that each bit is individually unpredictable while the pair is correlated. Ask the group what outcomes they expect and point out any extra hardware outcomes.
4. **Grover search (3 min):** Explain that the circuit marks `11` among four possibilities, then amplifies it. Compare the measured frequency of `11` between simulator and hardware.
5. **Wrap-up (2 min):** Ask what was clear, what sounded like jargon, and whether the charts made the comparison easy to explain to a client.

## Capture feedback

For each person, note ratings from 1 (unclear) to 5 (clear):

- I understood what the simulator was showing.
- I understood what an IBM hardware result was showing.
- I could explain the Bell correlation in my own words.
- I understood why simulator and hardware results might differ.
- The screen made it obvious when results were saved rather than live.

Record one confusing term, one question they asked, and one suggested change. Treat any uncertainty about whether a result is live or recorded as a release blocker for the pitch flow.
