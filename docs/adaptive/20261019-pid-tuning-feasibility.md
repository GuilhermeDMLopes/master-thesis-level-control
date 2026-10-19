# Model-to-PID tuning: source boundary and feasibility

Date: 2026-10-19. Analytical development only; no new deployed function block.

## What the supplied sources establish

See [PID source review](../pid/20261011-architecture-review.md) and [lecture register](references-and-traceability.md).
- Caiza et al. (2018), PDF pp.3–4: separate I/O and PID, gain interface; not a ready MMQE-to-PID gain law.
- Ramos et al. (2024), PDF pp.4–5: PID and communication architecture; not the selected model-to-gain calculation.
- aula2.pdf, PDF pp.24–29: RST pole placement, AR+BS=Ac. This supplies a design principle, not a direct substitute for the whiteboard PID.
- PID Adaptativo.pdf p.1 and advisor drawing: identification and gain adjustment responsibilities. The diagram is not a numerical tuning law.

These statements rely on the previously recorded page review; no new full-PDF or video review is claimed here. The project is authorized to derive/select the rule, rather than wait for a professor-provided formula. A separate tuner is a project modularity decision, not an IEC requirement for a type named PID_GAIN_TUNER.

## Derivation for the actual PID

Assume fixed gains, flag=TRUE, no saturation, coherent uniform samples, negative unity feedback, zero initial histories, and no extra transport delay. Let x=z^-1 and T be the PID sample interval.

Plant: G(x)=x(b1+b2*x)/(1-a1*x-a2*x^2), using the signed output coefficients of our estimator.

The existing trapezoidal integral and backward derivative give:
C(x)=KP + KI*T/2*(1+x)/(1-x) + KD/T*(1-x)
     =(q0+q1*x+q2*x^2)/(1-x).

q0=KP+KI*T/2+KD/T
q1=-KP+KI*T/2-2*KD/T
q2=KD/T

Inverse:
KP=(q0-q1-3*q2)/2
KI=(q0+q1+q2)/T
KD=T*q2

Closed-loop characteristic polynomial:
D(x)=(1-a1*x-a2*x^2)*(1-x)+x*(b1+b2*x)*(q0+q1*x+q2*x^2).

Its coefficients, ascending in x, are:
1
-1-a1+b1*q0
a1-a2+b1*q1+b2*q0
a2+b1*q2+b2*q1
b2*q2

Thus the generic characteristic polynomial has degree four but only three independently adjustable PID numerator coefficients. Arbitrary assignment of four poles is generally impossible. We must establish compatible targets (or a documented approximate/dominant-pole design), then check every resulting pole. Do not silently solve four inconsistent equations as if exact matching were guaranteed.

## Verification and next gate

The gain inverse and polynomial expansion were cross-checked using exact Python Fraction arithmetic with KP=1, KI=0.5, KD=0.1, T=0.1 and the original lecture model, at x=1/5,2/5,3/5. This is a narrow arithmetic check, not a tuning or stability validation.

No gains have been selected for the ARX process. The previously validated PID demo uses a different, first-order process; its test gains must not be relabeled as ARX tuning.

Next: choose realizable response targets; compute candidate gains; check full closed-loop poles and the time response using the actual saturation/flag algorithm; then test estimated-model inputs. Only after those checks implement the separate event-driven tuner. Gain scheduling can produce output jumps and fixed-gain pole stability alone does not establish adaptive closed-loop stability.

The identification timer's 100 ms was demonstration pacing. Any T assigned to the combined synthetic control experiment must be an explicit project choice, consistent with PID arithmetic and simulation indexing, not an inferred physical sampling interval from the lecture.
