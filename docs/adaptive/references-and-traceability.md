# Adaptive development: source register and decision traceability

Recorded from materials supplied by Guilherme on or before 2026-09-26; development resumed on 2026-09-29. Page numbers below are **1-based PDF viewer pages**, including covers, not slide labels or printed journal pagination. Exact file hashes and page counts are in [source-manifest.json](source-manifest.json). The PDFs remain in the researcher's source collection; this public repository records references and original implementation, not redistribution of classroom or publisher PDFs.

## Primary lecture sources

All three files were supplied in `Material_Identificação_e_controle_adaptativo.zip`. No publication year or DOI is inferred for classroom material.

| ID / supplied file | Author / material | Exact location | Adopted use / boundary |
|---|---|---|---|
| L1: `aula1_ident_linear (2).pdf` | Jeremias Barbosa Machado, ECAC06 - Identificação de Sistemas e Técnicas Avançadas de Controle | pp.5–10 | Identification as model selection, estimation and validation. An estimator is not itself a controller. |
| L1 | Same | pp.11–14 | Excitation signals. The input sequence in our reproduction is a documented project choice, not recovered original lecture data. |
| L1 | Same | pp.15–16 | Sampling considerations. No physical sample interval is selected from these general rules yet. |
| L1 | Same | pp.23–25 | Linear regression, least squares and weighting; basis of the independent batch cross-check. |
| L1 | Same | pp.26–28 | Recursive least squares; initial theta and P must be specified. |
| L1 | Same | **p.29** | RLS with forgetting: gain, parameter update and inverse information update. Implemented in `RLS4` and `ADP_RLS4`. |
| L1 | Same | **p.30** | Fixed process: y(k)=1.2y(k-1)-0.36y(k-2)+0.1u(k-1)+0.06u(k-2). Implemented in `ARX22` and `ADP_ARX22_PROCESS`. |
| L1 | Same | pp.31–36 | Example estimation plots and initial-matrix examples. Our deterministic P0=10000 I is NOT the lecture's displayed random matrix. |
| L1 | Same | **p.37** | b1=0.1 for samples 1–50 and b1=0.4 for samples 51–100; other coefficients unchanged. |
| L1 | Same | pp.38–42; especially **40–41** | Comparison with/without forgetting; lambda=0.6 and 0.8 are lecture example values, not approved plant tuning. |
| L2: `aula2.pdf` | Jeremias Barbosa Machado, ECA404, Aula 02 | pp.3–7 | Separate model structure, desired response, controller structure, adjustment mechanism and control law. |
| L2 | Same | **pp.20–23** | Self-tuning control and distinction between indirect and direct adaptation. Our intended architecture is indirect. |
| L2 | Same | **pp.24–29** | Pole placement with R,S,T and Diophantine equation; p.25 gives AR+BS=Ac; p.29 lists the repeated algorithm. This does not automatically define a PID tuning formula. |
| L2 | Same | pp.30–32 | Worked self-tuning example. Its controller is not silently substituted for a PID. |
| L3: `PID Adaptativo.pdf` | Supplied one-page design diagram; author not printed in the extracted text | **p.1** | Reference -> PID -> process; u and y -> MMQE -> Kp/Ki/Kd adjustment -> PID. Structural requirement, no numerical gain law. |

### Mathematical convention actually implemented

The regressor is `[y(k-1), y(k-2), u(k-1), u(k-2)]`. Theta uses signed coefficients `[1.2, -0.36, b1, 0.06]` directly. Do not switch to the alternative ARX denominator convention with negative y regressors without also changing theta signs.

Given old P and theta:

1. y_hat = phi^T theta; e = y - y_hat.
2. K = P phi / (lambda + phi^T P phi).
3. theta_new = theta + K e.
4. P_new = (P - K phi^T P) / lambda.

All right-hand sides use old state. P is symmetrized after the update as a numerical implementation choice. K here is the estimator gain, not PID Kp. Prediction is one-step-ahead using measured output history, not a free-running multi-step prediction.

## Supplied articles

The five files P1–P5 below are the complete contents of `Artigos_com_o_tema_do_mestrado.zip`. P6 was supplied separately; the separately supplied MPC PDF duplicates P2. P7 was supplied earlier. DOI entries below are transcribed from the supplied PDFs where available; link resolution has not been re-audited in this checkpoint. Missing DOI metadata is deliberately not guessed.

| ID / exact supplied file | Bibliographic identity | Location consulted | Decision informed |
|---|---|---|---|
| P1 `Implementation_and_evaluation_of_event-based_PID_in_the_IEC-61499_standard.pdf` | Oscar Miguel-Escrig and Julio-Ariel Romero-Pérez; *Implementation and evaluation of event-based PID in the IEC-61499 standard* (2018) | PDF pp.1–4; sections II–V; Listing 1 and Figs.2–4 | Basic FB/ECC, initialization and acquisition/controller/output chain. Distinguish a periodic event-driven IEC application from threshold-triggered control. Threshold trigger, variable-step PID and specific real-time platform are not adopted now. |
| P2 `MPC_Under_IEC-61499_Using_Low-Cost_Devices_for_Oil_Pipeline_System.pdf` | Carlos A. Garcia et al.; title as filename (2018) | PDF pp.3–5, implementation of communication and control FBs; p.6 conclusions | Encapsulation and interfaces. Do not reuse MPC optimization or its 0.108 s identification interval as adaptive-PID choices. |
| P3 `61499_ED2_OVW (2).pdf` | Christensen, Strasser, Valentini, Vyatkin and Zoitl; *The IEC 61499 Function Block Standard: Overview of the Second Edition* (2012) | PDF pp.3–4, section II, Figs.1–2 | Event/data interface, encapsulation, ECC. Overview is not the full normative standard and does not certify our files. |
| P4 `state of the art 61499 (1).pdf` | Valeriy Vyatkin; *IEC 61499 as Enabler of Distributed and Intelligent Automation: State-of-the-Art Review* (2011); DOI [10.1109/TII.2011.2166785](https://doi.org/10.1109/TII.2011.2166785) | PDF pp.2–4, function-block and execution discussion | Historical background on execution and portability. Predates the second edition; not the sole authority for current semantics. |
| P5 `Towards_IEC_61499-Based_Distributed_Intelligent_Automation_A_Literature_Review (1).pdf` | Guolin Lyu and Robert William Brennan (2021); DOI [10.1109/TII.2020.3016990](https://doi.org/10.1109/TII.2020.3016990) | PDF pp.2–4, modeling/transition challenges; implementation discussion begins p.7 | Record event order, consistency and runtime assumptions. A block diagram alone is insufficient validation. |
| P6 `Experimental_Platform_for_Testing_Open_Process_Automation_Technologies_Based_on_OPC_UA_and_IEC_61499.pdf` | *Experimental Platform for Testing Open Process Automation Technologies Based on OPC UA and IEC 61499* (2024); DOI [10.1109/SIOT63830.2024.10780765](https://doi.org/10.1109/SIOT63830.2024.10780765) | PDF p.4, section IV-A; Fig.7 on p.5 | Distinct communication/control responsibilities, FORTE and OPC UA, PID back-calculation anti-windup. The reported 1 s temperature sampling is not copied. Anti-windup implementation for our future PID is still pending. |
| P7 `1-s2.0-S2405896324007298-main.pdf` | Guzmán González-Mateos et al.; *A PID Control Architecture Based on IEC 61499* (2024), IFAC-PapersOnLine 58(7), 91–96; DOI [10.1016/j.ifacol.2024.08.016](https://doi.org/10.1016/j.ifacol.2024.08.016) | PDF pp.2–3, three-layer architecture and PID tuning; pp.4–6 experiments | Separate acquisition, PID execution and tuning. Its tuning architecture is related work, not evidence that RLS/PID is novel or that its tuning rule has been selected here. |

These are implementation references, not proof of publication novelty. Adaptive-control literature mapping remains open. The earlier candidate *Adaptive Industrial Control Systems via IEC 61499 and Runtime Enforcement* (DOI 10.1145/3691345) was identified by title/metadata only; its full text was not verified and no algorithm is adopted from it.

## Videos supplied by the advisor

Each URL is preserved below. Access attempts did not yield transcripts/content. **Not viewed or transcribed; no timestamp-level claim or implementation decision is attributed to them.**

| ID | Supplied group | URL |
|---|---|---|
| V1 | Identification/adaptive lessons | https://youtu.be/52vXi0ZhdIU |
| V2 | Same | https://youtu.be/JJVvJJaPhzQ |
| V3 | Same | https://youtu.be/-c5JGYkIcic |
| V4 | Same | https://youtu.be/aAs0s3aQRYU |
| V5 | Same | https://youtu.be/ygmBztzTd6M |
| V6 | Same | https://youtu.be/j2nbVRi-h14 |
| V7 | Same | https://youtu.be/7gtzSIZ9jGI |
| V8 | Same | https://youtu.be/EH1--pHu_gg |
| V9 | Self-tuning control | https://youtu.be/g-cJf-xLi-A |
| V10 | Self-tuning control | https://youtu.be/J2Y5g55_cbw |

The unresolved question is the exact model-to-PID gain law expected by the advisor. Obtain the relevant transcript or teaching script before claiming fidelity to that law.

## Previously supplied project material: retained context

- `IA.pdf`: Jeremias Barbosa Machado, intelligent/fuzzy control lessons (16 PDF pages); pp.1–3 identify subject. Historical fuzzy direction; no RLS or PID tuning parameters adopted.
- `aula3.pdf`: same lecturer, predictive control lessons (30 pages); pp.1–3 identify subject. Historical MPC direction; not an adaptive tuning specification.
- `Captura de tela 2026-09-25 135548.png`: advisor's architecture drawing; corroborates L3. No numerical parameters derived from its connections.
- `Apostila_Estudo_Projeto_MPC_PI.pdf` and `Apostila_Estudo_Projeto_MPC_PI_Expandida.pdf`: project study aids, not primary mathematical authorities. Their historical values must be checked against the versioned implementation before reuse.
- Dissertation/template archives and revised dissertation PDF: writing/layout artifacts, not sources for adaptive equations. Personal/institutional content is not needed in these implementation docs.
- `master-thesis-level-control-main.zip` and `master-thesis-level-control-main(2).zip`: historical repository snapshots. The current Git history is authoritative for code; this branch starts at `d4c08e8848e6d6e448ee7ce164121e7cb1ec4ac3`.
- IEEE/Scopus BibTeX exports and Parsifal screenshots from the fuzzy mapping: literature-search provenance, not implementation specifications. No claim of an exhaustive adaptive-control review is made from that search.
- Prior PI/MPC screenshots, runtime logs and experimental CSVs: historical engineering evidence, already documented under `docs/experiments/` and `docs/4diac/`. Their gains, scaling and sample intervals are not assigned to the new simulated process.
- New user-returned four CSVs, four PNGs and `resumo.json`: reproduced identification evidence from 2026-09-26, archived under `data/sample/adaptive/20260926/` and `results/adaptive/20260926/`. Portuguese filenames and plot labels are preserved to keep original bytes; new code and documentation use English.

This inventory covers the materials identifiable in this conversation and available source collection; it does not claim unseen files or unreviewed pages were read.

## Parameter provenance: what is NOT from the professor

| Parameter/choice | Value | Origin and limit |
|---|---|---|
| theta initialization | four zeros | Project reproduction choice |
| P initialization | 10000 I | Deterministic project choice; distinguish from L1 random-matrix plots |
| Input | original reproduction used NumPy seed 26092026, uniform [0,1); u(0)=0 | Project choice; archived sequence is replayed verbatim to avoid generator-version differences |
| Fixed experiment length | 100 samples | Extended fixed case; not the exact p.30 plotted window |
| Input/output prehistory | zero | Project choice |
| Noise | none | Mathematical reproduction only |
| P symmetrization | (P+P^T)/2 | Numerical implementation addition |
| Prototype guard | finite magnitude <=1e100; denominator >1e-100 | Numerical guard, not a physical limit or a proof of estimator quality |
| E_CYCLE display pace | 100 ms | Offline demonstration pace, not the identified plant Ts or approved PID period |
| VALID flag | update passed numerical guards | Does NOT mean identified model is accurate, excited, stable or safe for PID tuning |

## Implementation map

- `simulation/adaptive/identification.py`: L1 pp.29–30,37, with explicitly listed initialization choices.
- `scripts/reproduce_adaptive_identification.py`: checks the four archived scenarios.
- `scripts/generate_adaptive_4diac.py`: produces original ST implementations and event wiring.
- `ADP_REPLAY100`: replay of archived input; L1 p.37 parameter-change schedule.
- `ADP_HISTORY2`: original sample-alignment mechanism, motivated by L1 regression formulation.
- `ADP_ARX22_PROCESS`: L1 p.30 signed coefficients.
- `ADP_RLS4`: L1 p.29 update, plus initialization/guard handling.
- `ADP_IDENTIFICATION`: original composite implementing the serial event contract; structural inspiration P1/P3, not a copied application.

No PID gain-adaptation law has been implemented or selected in this checkpoint.
