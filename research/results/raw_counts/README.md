# Raw hardware counts (copy, 27 November 2026)

Byte-identical copies of every real hardware run's `results.json` and of every account read.

- **`results.json`** holds raw measurement counts per method, circuit, basis and fold scale, IBM job IDs, and IBM's job metrics (charged seconds, RUs).
- **The originals** stay in `../runs/<run>/`.
- **Every number** in `POC_REPORT.md` (final record) is computed from these counts by the scripts named in each run's `manifest.json`.

| File | Run |
|---|---|
| `20261124-104212_hardware-smoke.results.json` | Bell smoke job, `ibm_fez` |
| `20261124-104424_hardware-round1.results.json` | Round 1, `ibm_fez` |
| `20261124-105849_hardware-round2.results.json` | Round 2 (reversed order), `ibm_fez` |
| `20261125-145032_hardware-v2.*` | Recipe v2 round, `ibm_marrakesh` |
| `20261126-120458_hardware-v1-replication.*` | v1 replication round, `ibm_marrakesh` |
| `20261126-225723_hardware-v1-2.*` | v1.2 round on four new circuits, `ibm_marrakesh` |
| `account_reads_20261125.json` | The two account reads before the v2 round |

To check: `sha256sum -c SHA256SUMS.txt` (or `certutil -hashfile <file> SHA256` on Windows). The originals in `../runs/` are hashed in `../FINGERPRINTS.md` with the same values.
