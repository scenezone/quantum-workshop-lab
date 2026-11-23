# Crashed dry run (no results)

All three Sampler jobs completed; the IBM Estimator job then failed with the memory error. Local mode lays Estimator observables out on all 156 qubits, which cannot be simulated. Fixed by building and checking, but not executing, Estimator PUBs in dry runs.

Kept as a record; the dry run that completed is a later `*_hardware-dryrun` folder.
