# Noggimigo mastery-tracking study protocol

## Aim

Evaluate whether explicit knowledge components plus BKT/MIRT-style state estimates improve held-out prediction and calibration over simpler baselines. This protocol tests mastery estimation; it does not treat the model as a diagnostic or infer attention, fatigue, emotion, disability, intelligence, or biological state.

## Dataset and unit of analysis

Recruit learners who consent to educational research, record age band and prior experience only when necessary, and avoid collecting names in the interaction log. Define a fixed item bank for each knowledge component (KC), with expert-reviewed tags, difficulty strata, and parallel items for pre-test, training, immediate post-test, and delayed post-test.

The primary observation is one learner-item attempt: KC labels, item ID, binary correctness from the deterministic verifier, hint count, and timestamps needed to compute elapsed calendar gaps. Do not use raw response time as a cognitive-state label.

## Conditions

Use a randomized or matched two-condition design:

1. **Baseline:** deterministic lesson progression with a fixed hint policy and no adaptive mastery-based selection.
2. **Adaptive:** the same content and verifier, with BKT/MIRT-style estimates allowed to select review items or hint intensity.

If an unconstrained LLM comparison is scientifically necessary, predefine a third arm, keep content and exposure comparable, and manually audit its explanations for factual and step-level errors. Do not compare arms using completion alone.

## Modeling plan

Pre-register the KC map, item splits, priors, learning rate, forgetting assumptions, and all exclusion rules. Fit or update:

- a global accuracy baseline;
- BKT with fixed and learned transition parameters;
- the lightweight MIRT-style online baseline in `noggimigo.mastery`;
- an ablation without KC labels; and
- an ablation without forgetting or monotonicity constraints when those are implemented.

Split by learner, not by random row, so no learner's future responses leak into training. Report cold-start performance separately from within-learner performance.

## Primary outcomes

- **Next-item predictive performance:** log loss, Brier score, and AUC on held-out attempts.
- **Calibration:** expected calibration error and reliability plots; lower ECE is better.
- **Mastery ordering:** agreement between estimated mastery and post-test performance across learners and KCs.
- **Transfer:** performance on parallel items not shown during training.
- **Retention:** performance on delayed post-test items after a preregistered gap.

Use bootstrap confidence intervals clustered by learner. Report point estimates, uncertainty, sample sizes, missingness, and the exact item/KC split.

## Falsification criteria

The theory-guided approach is not supported if it fails to beat the global baseline on held-out Brier score and calibration, or if any apparent gain disappears under learner-level splitting. It is not evidence of cognitive validity if it only predicts repeated items or if it improves accuracy while worsening calibration and transfer.

The adaptive condition should not be deployed broadly unless it shows a pre-registered improvement in delayed transfer or retention without increasing exposure burden, inequity across learner groups, or unsafe feedback.

## Minimum reporting package

Publish the KC schema, item metadata, model configuration, analysis code, anonymized aggregate traces, calibration plots, error taxonomy, and a limitations statement. Keep raw learner data access-controlled and separate from model artifacts.
