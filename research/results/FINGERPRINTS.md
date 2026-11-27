# Fingerprints

Generated 2026-11-27 17:04 by `python fingerprint.py`. Git HEAD: `2b994c73946f6b488895029d05e2d80407ee0435 2026-11-27 17:03:59 +0530`.

SHA-256 is a fingerprint: changing a single byte of a file changes its hash completely. To check, re-run this script or hash a file yourself (`certutil -hashfile <file> SHA256` on Windows, `sha256sum <file>` elsewhere).

## Pre-registration integrity

Earlier versions of `PREREGISTRATION.md` are rebuilt from today's file and hashed. If a rebuilt hash equals the hash recorded at run time, that part's text has not changed since. Part C (deviations log) only grows by rows appended at the end, so each hardware run's version is today's file cut after the log rows it had; each of those hashes is also checked against the run's `manifest.json`. Part F (recipe v2, 25 Nov) was inserted before Part C, so versions from before it are rebuilt with Part F removed. The last row is today's file, which has no earlier record to match.

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
| A-E + 5 Part C rows (recorded by the v2 design runs, 24-25 Nov) | `8b1b6812f12014ee…` | `8b1b6812f12014ee…` | ✅ yes |
| A-F + 7 Part C rows (recorded by the v2 held-out test and dry run, 25 Nov) | `ffe5e2637af7b67a…` | `ffe5e2637af7b67a…` | ✅ yes |
| A-F + 11 Part C rows (recorded by the v2 hardware round, 25 Nov 14:50 IST, and the replication dry run) | `037d45941177382b…` | `037d45941177382b…` | ✅ yes |
| A-G + 11 Part C rows (recorded by the replication round, the v1.1 design replay and the v1.2 dry run, 26 Nov) | `7cb2acc714255172…` | `7cb2acc714255172…` | ✅ yes |
| Current file (A-H + all Part C log entries) | `44c9df50bb864d94…` | `44c9df50bb864d94…` | ✅ yes |
| recipe.py (frozen 11:22, quoted in Part B) | `0b08bb7e96d9046e…` | `0b08bb7e96d9046e…` | ✅ yes |
| recipe_v2.py (frozen 25 Nov, quoted in Part F) | `c98dd89d6d4cb794…` | `c98dd89d6d4cb794…` | ✅ yes |

## Frozen records (PREREGISTRATION.md Parts F7, G5 and H6, with Part C supersessions)

| File | Hash quoted | Expected now | Now | Match |
|---|---|---|---|---|
| `recipe_v2.py` | `c98dd89d6d4cb794…` | `c98dd89d6d4cb794…` | `c98dd89d6d4cb794…` | ✅ yes |
| `twirl.py` | `3a80e48152259026…` | `3a80e48152259026…` | `3a80e48152259026…` | ✅ yes |
| `heldout_v2.py` | `47cebe4405b52f8e…` | `47cebe4405b52f8e…` | `47cebe4405b52f8e…` | ✅ yes |
| `mitigation_v2.py` | `0de8e15281a132a8…` | `0de8e15281a132a8…` | `0de8e15281a132a8…` | ✅ yes |
| `hardware_v2.py` | `a24f2acd3b55bd0a…` | `1c8b4e376bde624a…` (Part C) | `1c8b4e376bde624a…` | ✅ yes |
| `recipe.py` | `0b08bb7e96d9046e…` | `0b08bb7e96d9046e…` | `0b08bb7e96d9046e…` | ✅ yes |
| `mitigation.py` | `4b8036fee7d8228a…` | `4b8036fee7d8228a…` | `4b8036fee7d8228a…` | ✅ yes |
| `folding.py` | `2309126cb3bc1c61…` | `2309126cb3bc1c61…` | `2309126cb3bc1c61…` | ✅ yes |
| `baseline.py` | `3c216afa124ae8b3…` | `3c216afa124ae8b3…` | `3c216afa124ae8b3…` | ✅ yes |
| `hardware.py` | `0fcc586b83a42b7c…` | `0fcc586b83a42b7c…` | `0fcc586b83a42b7c…` | ✅ yes |
| `hardware_v1_replication.py` | `5e54ce25580e09ef…` | `5e54ce25580e09ef…` | `5e54ce25580e09ef…` | ✅ yes |
| `recipe_v1_2.py` | `36e1a325bbb3e2d7…` | `36e1a325bbb3e2d7…` | `36e1a325bbb3e2d7…` | ✅ yes |
| `recipe_v1_1.py` | `4b9a2a84ff354876…` | `4b9a2a84ff354876…` | `4b9a2a84ff354876…` | ✅ yes |
| `heldout_v12.py` | `ba31d48b8e056ba8…` | `ba31d48b8e056ba8…` | `ba31d48b8e056ba8…` | ✅ yes |
| `hardware_v1_2.py` | `ce3a636ec86e9eac…` | `ce3a636ec86e9eac…` | `ce3a636ec86e9eac…` | ✅ yes |
| `v1_1_design_replay.py` | `114a3416f83d91ec…` | `114a3416f83d91ec…` | `114a3416f83d91ec…` | ✅ yes |

## Key files now

| File | SHA-256 | Last commit touching it |
|---|---|---|
| `PREREGISTRATION.md` | `44c9df50bb864d948d33ee182cadcd8693c1f909ccb8c2e955a748c5068ca74d` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `recipe.py` | `0b08bb7e96d9046e3be34ada9917c09859d2dba9895d1894d647ad26f1a67428` | d65539c 2026-11-23 12:25:17 +0530 |
| `heldout.py` | `7d6b0c9ae9f677876c244174345a672540e99165eea9e3e1cfd028b575c36109` | d65539c 2026-11-23 12:25:17 +0530 |
| `mitigation.py` | `4b8036fee7d8228aae51fa9a8aa9877e294254447281eb6b14341dafbd82c4a3` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `folding.py` | `2309126cb3bc1c6128af01a9fb3b471e52a1673b9a2f25d6765ff46378d8450a` | d65539c 2026-11-23 12:25:17 +0530 |
| `hardware.py` | `0fcc586b83a42b7ce1b5fdecbe2df597d994883c1b7c8537a84a431e74f06b9d` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `hardware_usage.py` | `642691af914c45b0b82a8a62f6e21f18e708560c5c67cf9cd38def279693b7c7` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `noise_scaling.py` | `db4c5ebc9a84a9e198a5661d1aa9563c170761fdafd3e6f4b95ed67f607c4d10` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `baseline.py` | `3c216afa124ae8b3e4d340c3dc74958c1eda1e14df702fec8d29b6841940d094` | d65539c 2026-11-23 12:25:17 +0530 |
| `runlog.py` | `763418ea443a12291c1b8fed8af8729de876c7678bda1d1d677b7069f1f03663` | d65539c 2026-11-23 12:25:17 +0530 |
| `recipe_v2.py` | `c98dd89d6d4cb794cdefd9c63277734ca5d2d24417f60dcfe522c1b7a957bfd8` | 9c7a332 2026-11-25 12:52:06 +0530 |
| `twirl.py` | `3a80e48152259026c71c9b1a4c74417d9451782df6d849e6d1cd44779d015a4a` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `heldout_v2.py` | `47cebe4405b52f8ee46d84b121fa9ec39862fa97011a4b210a97c05e2207d3be` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `mitigation_v2.py` | `0de8e15281a132a858f6b491411185b1945000369b9b7afae78087cf1485b183` | 9c7a332 2026-11-25 12:52:06 +0530 |
| `hardware_v2.py` | `1c8b4e376bde624a8c31ca6903793eb8ed56d7cd86591db6dc721e7e2453a3e2` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `v2_design_replay.py` | `a212eecd6c540304d0faaeaabd692ba1013d53c4ddab13344015d06380524f63` | d92ee5d 2026-11-25 10:18:01 +0530 |
| `hardware_v1_replication.py` | `5e54ce25580e09efb5c29018854b23ec66e8b3aa72be26b8e09627a9dbd26486` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `recipe_v1_1.py` | `4b9a2a84ff354876c52a4feacd1333ece298e87fae34a57608d5406f320b4693` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `v1_1_design_replay.py` | `114a3416f83d91ec1f09b44134855c275f981f8f7336ceb147c4bb7895383e21` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `recipe_v1_2.py` | `36e1a325bbb3e2d7f595c7e18846457fbafd6b154e7c3414c21332ea0591b412` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `heldout_v12.py` | `ba31d48b8e056ba8814c265fd5082d24e411643658ce06aac1e5bcf82d5b8a77` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `hardware_v1_2.py` | `ce3a636ec86e9eac9ec02a6760ad4e516db3f4383a33d8d09dc2fbfc91d5af58` | 8e667fa 2026-11-27 13:31:31 +0530 |
| `failure_analysis.py` | `ab4f6480b9e64b48f5d8be955066728399e08eb987e2c43108a7d769f447c933` | dae4f35 2026-11-27 17:03:41 +0530 |

## Runs (newest first)

### `20261127-155639_failure-analysis`

Created 2026-11-27T15:56:39 · code at commit `73f2ab6 + uncommitted research changes` · pre-registration `44c9df50bb864d94…`

| File | Bytes | SHA-256 |
|---|---|---|
| `failure_analysis.md` | 20394 | `d4e4779c8328ca31fde3bee53696f640a19e524037fbaebb24e5cd66d1445a57` |
| `manifest.json` | 2511 | `9cbc835a8c887912e520959914e0c98e1f451d3d2ccb87787e0376d54f154772` |
| `summary.json` | 81493 | `1f2c32c4e7d45b0c925c1bb619dc7ddeca8eb952719b48294cd765ff43078fd0` |

### `20261126-225723_hardware-v1-2`

Created 2026-11-26T22:57:23 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `44c9df50bb864d94…`

| File | Bytes | SHA-256 |
|---|---|---|
| `account_reads.json` | 1032 | `df748c53282eef18bab94be9e37504cc490b7c3abd2423419acba3b022b97f48` |
| `hardware_v1_2.md` | 4607 | `263d9de7cae229a1504094b8a1f6295f252095d1a2be48bc9c974d0007777297` |
| `manifest.json` | 1680 | `b9ad45665087b16a62bfdf71f62b1d4340bdf44e1702bfbea3a36afc0240c786` |
| `results.json` | 8810 | `92f39de01893c8dc8d2d02e187418d7d75c3b22fd66b44110b87630b02b2b77d` |
| `summary.json` | 7237 | `4938d648d55f207ae8a346bcd8aa4381f18be772be1a3d80c088252eaebc2fa7` |

### `20261126-224957_hardware-v1-2-dryrun`

Created 2026-11-26T22:49:57 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `7cb2acc714255172…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware_v1_2.md` | 4776 | `6940bf12ae5573335b65865f4090a5f5864e44e7f02d3a80658d578b0e713327` |
| `manifest.json` | 1646 | `616fbe3258e33bebc4c5b0d97bf720fde14312bd0388cc583f4768b468e1af3d` |
| `results.json` | 6532 | `0fbdfe086b166d17edbec078c799296ab09937bfaf6d61d88511d96a7a1aab7d` |
| `summary.json` | 7230 | `a3a11e00c0b4345d7ce0978717da93158c7cddbb6bf701b960f2408c3378f7c5` |

### `20261126-223700_v1-1-design-replay`

Created 2026-11-26T22:37:00 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `7cb2acc714255172…`

| File | Bytes | SHA-256 |
|---|---|---|
| `manifest.json` | 1941 | `9923234d46740d6cb294a9a1c0cc101850d474eaa57bfbafcc2d114ec67424f1` |
| `summary.json` | 59723 | `819ab0f93c3706a865a86b396b4a784e21616f03ce6d684e29d14a2ad1a51743` |
| `v1_1_design_replay.md` | 11409 | `1027e3eb449763c47206a6abdb341749d9e75e797a7eafba10d3edd5e077b5a4` |

### `20261126-120458_hardware-v1-replication`

Created 2026-11-26T12:04:58 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `7cb2acc714255172…`

| File | Bytes | SHA-256 |
|---|---|---|
| `account_reads.json` | 1014 | `4ccc095f607cf588e93662f277a697f35f5cfc8790032d016a518768317e6212` |
| `hardware_v1_replication.md` | 3409 | `367f503afa152e3b68bdf2e0791e9c671236e1f3530e53562c45657301adab23` |
| `manifest.json` | 1758 | `d282141f7ee8ec2ba0ecdefe075f07e5d47fd2f03bf4e63f5d548a9e4f339260` |
| `results.json` | 7717 | `d57a056c72d878e14aa1f7156970ecaa16ddc3b31abcc485cb313b29332c0b3e` |
| `summary.json` | 4842 | `cf729dd6609cc56c125fc4620eb629e82f2cb870eac200d351e6ac25c4c6c00b` |

### `20261126-120029_hardware-v1-replication-dryrun`

Created 2026-11-26T12:00:29 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `037d45941177382b…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware_v1_replication.md` | 3456 | `b0688efc5bc360a0f9c92399780ece70615f3c909e4fded6a45b397bfceeda27` |
| `manifest.json` | 1728 | `af6280f7d89ee3af616734d81c8487545450bd1d7672469388a12b3784958c66` |
| `results.json` | 4429 | `08032acc8eb80a843161b502aef8fc26ffd5fc38318bdbef945b34b1e0b01585` |
| `summary.json` | 4714 | `b0eb71e8177ad5bf310061fc165048d530757a70b76aad8b0a16cb065f62e14e` |

### `20261125-145032_hardware-v2`

Created 2026-11-25T14:50:32 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `037d45941177382b…`

| File | Bytes | SHA-256 |
|---|---|---|
| `account_reads.json` | 1349 | `c5be90e63ddd050a33e6b99ceada7abef7e316da3e8ca9026fcc9c23837e3314` |
| `hardware_v2.md` | 3704 | `5103e6a4503f5da2fba5a9ea977391bbfb50bccb98c7b7ecb10bee88d9cfeefa` |
| `manifest.json` | 2756 | `0bcc74a112adc77a9482c45a290151723da8b69fb34871bac32e80351633079a` |
| `results.json` | 43417 | `176dd94f2726dc486d8deabc786c7fec9c257ff2c28d8bf1399f00e5c64e0b6a` |
| `summary.json` | 4260 | `b09961f6433aab66ec9cc513f839dd1d05a99d94f92ea3abda74ed69c5f19f2c` |

### `20261125-125318_hardware-v2-dryrun`

Created 2026-11-25T12:53:18 · code at commit `9c7a332 + uncommitted research changes` · pre-registration `ffe5e2637af7b67a…`

| File | Bytes | SHA-256 |
|---|---|---|
| `hardware_v2.md` | 3873 | `683498ec3f0bef0ad01df1b285e5a3b782ec3a89ffe094dbd9db43d88a58a9af` |
| `manifest.json` | 2707 | `77601d84957d781ae3d5093d17c04fcef2f7e7daa956d27e795183f699fa803f` |
| `results.json` | 35887 | `2f86e56f2db524081a99d961ffdc9936ddeba541d9dc5f9783009ed7332888e8` |
| `summary.json` | 4167 | `6821b4434bf486c6afe4066ad871e562a1e597b9f5f54c3c7e493908e7a738c3` |

### `20261125-124533_mitigation-v2-test`

Created 2026-11-25T12:45:33 · code at commit `d92ee5d + uncommitted research changes` · pre-registration `ffe5e2637af7b67a…`

| File | Bytes | SHA-256 |
|---|---|---|
| `counts.json` | 108284 | `d3c3309de2390300339556f593f5c71ce303122043beeb1dd49278e8bfcf059d` |
| `manifest.json` | 8729 | `d8a744722a5bfa5d940196e4bcb0f7d1f2d781fdcf543bcbc59a685d1778ff92` |
| `mitigation_v2.csv` | 1035 | `2b067856bdb48e8da8e999acae1c37dfa1f493bf3bb568642d337ec6b9086366` |
| `mitigation_v2.md` | 4326 | `b8b0406cfecb4e8171545f6d2c2b7972f702dedc707fc2d4e494bdb08e6c5291` |
| `targets.json` | 677 | `17bc904ec6dd80501af58f59e4c0c240c3544396b253a029aa3074380095f0e0` |

### `20261125-120531_mitigation-v2-train-partial`

Created 2026-11-25T12:05:31 · code at commit `d92ee5d + uncommitted research changes` · pre-registration `8b1b6812f12014ee…`

| File | Bytes | SHA-256 |
|---|---|---|
| `counts.json` | 34163 | `d356b910ffad8ae814a893ebe8b5fe2cbd693b8b65179a7203c7997d20676297` |
| `manifest.json` | 15219 | `3c816d4ca59067b70c112aeff98da5ca0084c946a89538daa23c05f6a00b347c` |
| `mitigation_v2.csv` | 1314 | `80cdc5e345a9925f2e7beb81d1ba650eb12e27bf0b40538491bb1f8d6dd06ffe` |
| `mitigation_v2.md` | 4772 | `01835cb4abc3a668f04bd236742475fad0a8d0c5383b7a954c40c4f1bdd89693` |

### `20261125-101929_mitigation-v2-train-scales1-2-3`

Created 2026-11-25T10:19:29 · code at commit `d92ee5d + uncommitted research changes` · pre-registration `8b1b6812f12014ee…`

| File | Bytes | SHA-256 |
|---|---|---|
| `counts.json` | 879405 | `48a2d945b8e3c4053eccf919fcd303b1e42b724056523ac9bbe00abde7dff6f9` |
| `manifest.json` | 45391 | `d0ab2df29dc26bcf7a02f9b2937352540bac6e4682083fa3c43aa16a2e558a54` |
| `mitigation_v2.csv` | 4552 | `a22d4506ce24b6738a1a5e727cd792bc1e52481f7a33e160714170b78ee212eb` |
| `mitigation_v2.md` | 9319 | `6d232e783e23af45631b4c80a796e71c3bfac506e7ac6f021befb17bdd0a7522` |

### `20261124-161451_mitigation-v2-train`

Created 2026-11-24T16:14:51 · code at commit `d65539c + uncommitted research changes` · pre-registration `8b1b6812f12014ee…`

| File | Bytes | SHA-256 |
|---|---|---|
| `counts.json` | 877570 | `7e3129974309107a47c227a8858e605b5f4fe050e13a6f9ef2748a60c67b985a` |
| `manifest.json` | 45612 | `ec9f4250027accbbf71e581ea05aead0fac0071575ce197772dae9572b54294b` |
| `mitigation_v2.csv` | 4540 | `23bd29dd33865fd3196c0e33ac745f1bff4d0980f69c2de991291d84c613a807` |
| `mitigation_v2.md` | 9308 | `646c901642a94a6f19514246894a733c35e1e7215cb3837dfe39fd7bce017307` |

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
