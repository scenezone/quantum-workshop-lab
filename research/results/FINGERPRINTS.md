# Fingerprints

Generated 2026-11-24 14:10 by `python fingerprint.py`. Git HEAD: `d65539c39a6d06577d23ecc4bbcedab915e579b0 2026-11-23 12:25:17 +0530` (research folder has uncommitted changes).

SHA-256 is a fingerprint: changing a single byte of a file changes its hash completely. To check, re-run this script or hash a file yourself (`certutil -hashfile <file> SHA256` on Windows, `sha256sum <file>` elsewhere).

## Pre-registration integrity

Earlier versions of `PREREGISTRATION.md` are rebuilt from today's file and hashed. If a rebuilt hash equals the hash recorded at run time, that part's text has not changed since. Part C (deviations log) only grows by rows appended at the end, so each hardware run's version is today's file cut after the log rows it had; each of those hashes is also checked against the run's `manifest.json`. The last row is today's file, which has no earlier record to match.

| Version | Recorded at run time | Rebuilt / checked now | Match |
|---|---|---|---|
| Part A only (11:14) | `042725112296bf1b…` | `042725112296bf1b…` | ✅ yes |
| Parts A+B (11:22) | `15bb2568d7fe804d…` | `15bb2568d7fe804d…` | ✅ yes |
| Parts A+B+C as committed (before Part D) | `ebbdb7d17bb4643b…` | `ebbdb7d17bb4643b…` | ✅ yes |
| Parts A-D (16:11, recorded by the noise-scaling runs) | `caceaa4bc588c549…` | `caceaa4bc588c549…` | ✅ yes |
| Parts A-E (16:48, hardware plan; sent to reviewer) | `67e4955c6c969b20…` | `67e4955c6c969b20…` | ✅ yes |
| A-E + 2 Part C rows (recorded by the smoke job, 24 Nov 10:42) | `1e6445875334a37c…` | `1e6445875334a37c…` | ✅ yes |
| A-E + 3 Part C rows (recorded by hardware round 1, 10:44) | `97b5eb8abf74fb82…` | `97b5eb8abf74fb82…` | ✅ yes |
| A-E + 4 Part C rows (recorded by hardware round 2, 10:58) | `2a0fb6425bff06ae…` | `2a0fb6425bff06ae…` | ✅ yes |
| Current file (A-E + all Part C log entries) | `8b1b6812f12014ee…` | `8b1b6812f12014ee…` | ✅ yes |
| recipe.py (frozen 11:22, quoted in Part B) | `0b08bb7e96d9046e…` | `0b08bb7e96d9046e…` | ✅ yes |

## Key files now

| File | SHA-256 | Last commit touching it |
|---|---|---|
| `PREREGISTRATION.md` | `8b1b6812f12014ee89d96621f21850342c97cf46b6dcba9c8b236df04083ba0f` | d65539c 2026-11-23 12:25:17 +0530 |
| `recipe.py` | `0b08bb7e96d9046e3be34ada9917c09859d2dba9895d1894d647ad26f1a67428` | d65539c 2026-11-23 12:25:17 +0530 |
| `heldout.py` | `7d6b0c9ae9f677876c244174345a672540e99165eea9e3e1cfd028b575c36109` | d65539c 2026-11-23 12:25:17 +0530 |
| `mitigation.py` | `4b8036fee7d8228aae51fa9a8aa9877e294254447281eb6b14341dafbd82c4a3` | d65539c 2026-11-23 12:25:17 +0530 |
| `folding.py` | `2309126cb3bc1c6128af01a9fb3b471e52a1673b9a2f25d6765ff46378d8450a` | d65539c 2026-11-23 12:25:17 +0530 |
| `hardware.py` | `0fcc586b83a42b7ce1b5fdecbe2df597d994883c1b7c8537a84a431e74f06b9d` | d65539c 2026-11-23 12:25:17 +0530 |
| `hardware_usage.py` | `642691af914c45b0b82a8a62f6e21f18e708560c5c67cf9cd38def279693b7c7` | not committed yet |
| `noise_scaling.py` | `db4c5ebc9a84a9e198a5661d1aa9563c170761fdafd3e6f4b95ed67f607c4d10` | not committed yet |
| `baseline.py` | `3c216afa124ae8b3e4d340c3dc74958c1eda1e14df702fec8d29b6841940d094` | d65539c 2026-11-23 12:25:17 +0530 |
| `runlog.py` | `763418ea443a12291c1b8fed8af8729de876c7678bda1d1d677b7069f1f03663` | d65539c 2026-11-23 12:25:17 +0530 |

## Runs (newest first)

### `20261124-105849_hardware-round2`

Created 2026-11-24T10:58:49 · code at commit `d65539c + uncommitted research changes` · pre-registration `2a0fb6425bff06ae…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware.md` | 2131 | `e6bd10da2d75c3f17c838ca75dc088ac9020d55bdb3acdde61ab55852deb9373` |
| `manifest.json` | 2219 | `b027bb85f6a2df77d4dfc8db5030f0555b816229894205186e5b72b88aae41e2` |
| `results.json` | 37377 | `b3f04e7977030eecf394da6d67228ef5dd33a2d1ad1a5af771d7bd306a98272b` |
| `summary.json` | 3810 | `7040f96cf47dbb9f8ff1eb9dc0401c302e3db2ca9681b18de414c7075ca38956` |

### `20261124-104424_hardware-round1`

Created 2026-11-24T10:44:24 · code at commit `d65539c + uncommitted research changes` · pre-registration `97b5eb8abf74fb82…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware.md` | 2132 | `46700f261ddc6ff7ec3e7a7e7e7c57f77039a7d1f1d19aae886ca1c0238cc86d` |
| `manifest.json` | 2216 | `a889e9b74c5f23744ec0212e14816ec47fee52f89b250f545a68b1845b628108` |
| `results.json` | 37455 | `5ffba233311219009d3e486f0b7a9d51decf0e77a2b12bb6aa3379877d099d4d` |
| `summary.json` | 3812 | `48f47050ba91d2802c046f96c768163c507b713f7dfe4997936a33a9c4f5e12b` |

### `20261124-104212_hardware-smoke`

Created 2026-11-24T10:42:12 · code at commit `d65539c + uncommitted research changes` · pre-registration `1e6445875334a37c…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware.md` | 1086 | `197d398fc3cf79f7525f7d62a1cd8e1afafe19a5e65fd1c85ab252c2f78c3ee2` |
| `manifest.json` | 1923 | `1c7fac58d30104926fb82c393ec2d7ea147e2c17516e29b35ef4c18ffbc34733` |
| `results.json` | 2239 | `a982a2a4f90299895a0628afe07523a70983232bab4a5b949b5d5c092de7288f` |
| `summary.json` | 569 | `d8443155460793fc13737fe496d637b64564d7ea66eab98e85b6d5e5d8bccf80` |

### `20261123-161940_mitigation-test-noise2`

Created 2026-11-23T16:19:40 · code at commit `d65539c + uncommitted research changes` · pre-registration `caceaa4bc588c549…`

| File | Bytes | SHA-256 |
|---|---|---|
| `circuits.qpy` | 119525 | `0d38f6d09d91d58fe973f962f8ed271d0af2eb8af6b18a0ed4ce95d6fd6f6a72` |
| `counts.json` | 503001 | `33d1b4e1250c9eb877097862da0472e2f8b9aee59bf05536c0de109bf3fd6d61` |
| `manifest.json` | 13934 | `ecd3e9925f38dc1548e80aeff22ed9aa271e46e8482f91d38257c3e0ba89be43` |
| `mitigation.csv` | 5316 | `3a454d005608097201b6541f22400010b474baab37d9e6e82334efb7c69266e3` |
| `mitigation.md` | 9129 | `5dc49e82c19937fa4a45a6c6f86f75654df0472cf82d91e2319ee0561de14eb7` |
| `targets.json` | 651 | `a9ee7343231484c6ac8cc402fff1a033d7c9d432cd9bca270bbf3cb21801e129` |

### `20261123-161735_mitigation-test-noise1.5`

Created 2026-11-23T16:17:35 · code at commit `d65539c + uncommitted research changes` · pre-registration `caceaa4bc588c549…`

| File | Bytes | SHA-256 |
|---|---|---|
| `circuits.qpy` | 119525 | `dcda461a3a40fee9eb7a7cff632c2098fbf1f6855550e1f3ed4e42b997622e1b` |
| `counts.json` | 491950 | `f42cf5b57e56643891812ce04a5e71c2c0c02507fc50656532ca799dbf00626e` |
| `manifest.json` | 13938 | `97a305e17cdfdeb445c0660cce4a1a2922e6d7bb4e2d9c1c41434570c5f45090` |
| `mitigation.csv` | 5311 | `35e667580037be6b140fbc3f49e1f34e74806f9f0395bea6981b935a95dba25f` |
| `mitigation.md` | 9137 | `14796a30056220c619cb286405a2d7861c688ad8f12212503556cd9d1dc83d23` |
| `targets.json` | 651 | `63cef3abee033cf7e7f5b2c1e25769d7881330085042a4db4579d1269f6b4e1e` |

### `20261123-161435_mitigation-test-noise0.5`

Created 2026-11-23T16:14:35 · code at commit `d65539c + uncommitted research changes` · pre-registration `caceaa4bc588c549…`

| File | Bytes | SHA-256 |
|---|---|---|
| `circuits.qpy` | 119525 | `1efdd2a139898fa2e19faa5938067761fadbdd92b07c6a7246ae3e4a437f98dd` |
| `counts.json` | 448388 | `7589dd479e383f114e97b9baea46948192e2d531ec3d98063c6eaeda21998eae` |
| `manifest.json` | 13902 | `22fee893a38ad7c2f139e14d98580ec0955f79495d3bdee98a3388f992c40eaf` |
| `mitigation.csv` | 5348 | `182c182631a89ef07e2e49a25fffdf6caec539472d8bb4f295f7604c2ae4c4c2` |
| `mitigation.md` | 9140 | `27ad4885a1645c6e518ff0f2b9752f051cff9ec44340c25fd1cff2bc938a885d` |
| `targets.json` | 651 | `9a12dd1cae4ae00c163959287056f4599bed91cfb43595566aa201ab52a4a5cd` |

### `20261123-161422_noise-scaling`

Created 2026-11-23T16:14:22 · code at commit `d65539c + uncommitted research changes` · pre-registration `caceaa4bc588c549…`

| File | Bytes | SHA-256 |
|---|---|---|
| `manifest.json` | 1219 | `b6fc04ac0e229609f701034828886e20ba8b49afa714ba74251e8b0882e485a1` |
| `noise_scaling.md` | 4304 | `1a02743b6e08e9e674ba7efb8b9fff15c334c8a55cafebb5efd5a2ef8665cd89` |
| `summary.json` | 710 | `ac563294d55733578784d3bba5260eca0384e1a6532a25ef2f08750f143141af` |

### `20261123-115437_hardware-dryrun`

Created 2026-11-23T11:54:37 · code at commit `46d5348 + uncommitted research changes` · pre-registration `ebbdb7d17bb4643b…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware.md` | 1817 | `e5a0c3955a7677d1b50e72d95e5fb02fb81b18737de92285975c2650956d07ce` |
| `manifest.json` | 1967 | `2a828bbe047987c4333ef82eeb1d67e9975e0d323d1051df796a2ee791cc5aa2` |
| `results.json` | 28845 | `d73d9cc8e6957117b83d614827f42203fc0729ac7b83f20bbc0efa3a9841c792` |
| `summary.json` | 3074 | `19b7c5e4476954524bfdad006581b0f25e21a65aef8322972873eb1a93418507` |

### `20261123-113635_hardware-dryrun` (crashed, see FAILED.md)

Created 2026-11-23T11:36:35 · code at commit `46d5348 + uncommitted research changes` · pre-registration `ebbdb7d17bb4643b…`

| File | Bytes | SHA-256 |
|---|---|---|
| `FAILED.md` | 375 | `b2f0793540cbb0b132ee271984978dc476924a872bfe47c006cb27673ce82d8e` |
| `manifest.json` | 1967 | `e0cc39758034d750395b1ae4a1bcde73a825abf405997360b4c2e84de1aa35c7` |

### `20261123-113115_hardware-dryrun` (crashed, see FAILED.md)

Created 2026-11-23T11:31:15 · code at commit `46d5348 + uncommitted research changes` · pre-registration `ebbdb7d17bb4643b…`

| File | Bytes | SHA-256 |
|---|---|---|
| `FAILED.md` | 190 | `ef44876e3fc4d6f6b62ac3d0f39eb6ecb871481169552ac3b29366f74629e7c2` |
| `manifest.json` | 1967 | `27503d9753be250eb34c39ad39c0485b7398b2b8d107acb3df316721623e4503` |

### `20261123-112713_hardware-dryrun` (crashed, see FAILED.md)

Created 2026-11-23T11:27:13 · code at commit `46d5348 + uncommitted research changes` · pre-registration `15bb2568d7fe804d…`

| File | Bytes | SHA-256 |
|---|---|---|
| `FAILED.md` | 240 | `ccfe7ebbf0e9c95f9fa5bffd757da849b64bcdc75dab0ae47cfacd8cca2cde6d` |
| `manifest.json` | 1967 | `8c4a85810ad17800a667ea54a13cc5eaea734fdb345e5e0b435ad616d2971da9` |

### `20261123-112504_hardware-dryrun` (crashed, see FAILED.md)

Created 2026-11-23T11:25:04 · code at commit `46d5348 + uncommitted research changes` · pre-registration `15bb2568d7fe804d…`

| File | Bytes | SHA-256 |
|---|---|---|
| `FAILED.md` | 289 | `91a04e6fa96ee1a0d3419b9e1d325ea83bc0480c283731563b58fb30ae2a7645` |
| `manifest.json` | 1778 | `80dc8bd0bf2a33f966ee63f3e70cb1f7a292f4d00617f26a782c5580e6b15b7d` |

### `20261123-112303_mitigation-test`

Created 2026-11-23T11:23:03 · code at commit `46d5348 + uncommitted research changes` · pre-registration `15bb2568d7fe804d…`

| File | Bytes | SHA-256 |
|---|---|---|
| `circuits.qpy` | 119525 | `91002f0b3f80d271ef1457046c0418d84aadc303e31b5c4b09c0490030bd33e1` |
| `counts.json` | 475378 | `6822531c00d02ea95065201f14887761478eaaf47394d11cdd62b6c00dbf611e` |
| `manifest.json` | 13869 | `7f5ba54060be49cfdf1e21cd2053f1ea948e586759ac31f320f3cfe111a8114f` |
| `mitigation.csv` | 5340 | `de840b99f7a0d446d67a06a9ce25907f3d34acd81a81afa05054bf2251fa3b72` |
| `mitigation.md` | 9118 | `e49f7504a227eb4bddc3e873ce32c601df5f5a0872c1267b65d139d6940a4567` |
| `targets.json` | 651 | `64c0022adf5aed5001f026017dea587fba2e3e907be596168dfbb49810fcd0c1` |

### `20261123-111818_mitigation-train`

Created 2026-11-23T11:18:18 · code at commit `46d5348 + uncommitted research changes` · pre-registration `042725112296bf1b…`

| File | Bytes | SHA-256 |
|---|---|---|
| `circuits.qpy` | 150557 | `e9533504c3ce9803d440ecaf181befa49ca8c974f18cd330914235a038a54961` |
| `counts.json` | 703866 | `e2ab8d616f0291a224119a7d20c4c3771cd7e0424a064ef69c7769d1fe39d896` |
| `manifest.json` | 27866 | `7fce6abb99d48cab3e8d97a582302775dedba251868c0f3b7f0b8a95c8b24a18` |
| `mitigation.csv` | 10391 | `48b2575374d485be1b46a0e4a44c8153de66a67c97afb0b7343df230768d37b8` |
| `mitigation.md` | 12693 | `34784a1148758be371b01e3caba0af7620f09b34df52be2869cea4415d55739f` |

### `20261121-142309_selection`

Created 2026-11-21T14:23:09 · code at commit `46d5348 + uncommitted research changes` · pre-registration `none recorded…`

| File | Bytes | SHA-256 |
|---|---|---|
| `counts.json` | 339682 | `784e6735f7339762d7a421551e0da66296f24835ef80123e17d8eb9c7bd0b807` |
| `manifest.json` | 1700 | `01d137b2d047eda66aca4b58b2271048e02e6db66efd15cc3a217bb62fd9601f` |
| `selection_FakeKingston.md` | 5274 | `fd8d8fbb59c7d32f2fc3ce6a0a9534c94ba231ac4a47f9f613ff2509b2592ada` |
| `selection_FakeSherbrooke.md` | 5397 | `2e9c09549c95cfbb7266fd78859488ecb53de60452e3fb82cf9f48daf4dabf9c` |

### `20261121-141802_baseline`

Created 2026-11-21T14:18:02 · code at commit `46d5348 + uncommitted research changes` · pre-registration `none recorded…`

| File | Bytes | SHA-256 |
|---|---|---|
| `baseline.csv` | 30388 | `34e12eeb6e208a156a66e08906e9999097047efc7779088bd840da6d2b943762` |
| `baseline_FakeKingston.md` | 12642 | `639854b9637259034d2db7dda6a56ac573f2e251524e8140cd9371a25e1c8769` |
| `baseline_FakeSherbrooke.md` | 12643 | `4f36762fa62c524765e8e50b22a5f0bfaec6d3f6b186f2817130cc210e322b29` |
| `comparison.md` | 1163 | `b16875406c11ce355e45ce7928b0bdc52a007aed6c3190df002f1257cddae06d` |
| `counts_FakeKingston.json` | 167097 | `fa67e1941b7bf2c2eb01ed915d6f6f4385902d5be37240be5f19e3e8746879a3` |
| `counts_FakeSherbrooke.json` | 193649 | `3de6cc85c64158419c2554e366a1ca99ac12a10f6a72ada8e5db3961cc691f91` |
| `manifest.json` | 1721 | `1d4f4227d64997fbf4e58054024896c0b1f35aff41cbc472d48691263d8b72bc` |

### `20261121-141701_selection`

Created 2026-11-21T14:17:01 · code at commit `46d5348 + uncommitted research changes` · pre-registration `none recorded…`

| File | Bytes | SHA-256 |
|---|---|---|
| `counts.json` | 50835 | `384abad02157e62d80c6bbb541e72ec2c19c795548f7e31e374c03bb9d7a7d6a` |
| `manifest.json` | 1610 | `700f6cd18ae4201bebb0a179742be42b013fc3483aaa20f3c706bde567afe52d` |
| `selection_FakeKingston.md` | 2464 | `cd2a01078b842d23acef3dbc29e506ef8f891318ef3cfb4d38dbf2acf07bb124` |

### `20261121-141214_mitigation`

Created 2026-11-21T14:12:14 · code at commit `46d5348 + uncommitted research changes` · pre-registration `none recorded…`

| File | Bytes | SHA-256 |
|---|---|---|
| `circuits.qpy` | 150557 | `b410a25bcb12c256880881534ab0e22165ae8c3a4868e0994208419fb442df2f` |
| `counts.json` | 704355 | `4fe3b6510b71390c353e3afacc2fa8f7367138c92b6fa07e056c76d03031a32c` |
| `manifest.json` | 24334 | `c4d7453a4666fc5a098faee7569763badd09eb0c6ce5e0aa04845d20d815dee4` |
| `mitigation.csv` | 9684 | `489e971857e36dc09c4d1a59b4c9d43977a79a531dd8f0baeac81bd307894506` |
| `mitigation.md` | 13966 | `cc438ba22d84e61412bf2003c8629e0e9d0fee4a8c68507a1b18cc5a4e58bf9f` |
