# Training Optimization Checklist

Status: in_progress
Created: 2026-06-10
Objective: break the repeated pattern where max score plateaus at generation 1 and training stops early.

## Baseline

- [x] Confirm the latest nested experiment run is the true latest training artifact.
- [x] Confirm recent runs repeatedly stop with `watchdog_plateau` around generation 13.
- [x] Confirm repeated runs often peak at generation 1 and then stay flat.

## Experiment Sequence

### Step 1: Remove watchdog as the immediate limiter

- [x] Create a new experiment directory from the latest local `active_chromosome.json`.
- [x] Run training with the same GA hyperparameters but `--disable-watchdog`.
- [x] Analyze the completed run and check whether improvements appear after generation 13.
- [x] Decide whether watchdog was prematurely truncating useful search.

### Step 2: Keep watchdog, but relax early-stop sensitivity

- [x] Run a follow-up experiment with `--watchdog-patience 24`.
- [x] Raise `--watchdog-min-generations` to `20`.
- [x] Analyze whether later generations recover without fully disabling safety.

### Step 3: Increase evaluation reliability

- [x] Run a follow-up experiment with `--games-per-genome 40`.
- [x] Compare whether selection becomes less noisy and whether best fitness improves later.

### Step 4: Increase exploration pressure

- [x] Run a follow-up experiment with `--inject-ratio 0.25`.
- [x] Run a follow-up experiment with `--tournament-size 3`.
- [ ] Optionally test `--mutation-rate 0.15` if stagnation persists.

### Step 5: Reduce trajectory repetition

- [ ] Repeat the best hyperparameter profile with at least 3 distinct seeds.
- [ ] Compare whether fixed-seed reruns were hiding useful exploration variance.

## Review Notes

- Update this checklist after each run with a brief result note and the next chosen step.
- Step 1 result:
  Run analyzed: `training_runs/experiment-watchdog-disabled-20260610T1315/train-20260610T131601.697447Z.json`
  Analysis: `training_runs/experiment-watchdog-disabled-20260610T1315/analysis-train-20260610T131601.697447Z.json`
  Outcome: watchdog was not the root cause of stagnation. With `watchdog_enabled=false`, the run completed all `40/40` generations and still never improved after generation 1.
  Key facts: `best_fitness=588.8215247459111`, `validation_fitness=467.1795484770519`, `best_generation=1`, `recent_best_fitness_delta=0.0`, `final_no_improvement_generations=39`, `mutation_pulse_count=10`.
  Interpretation: the search process kept exploring distinct chromosomes, but no later candidate beat the generation-1 incumbent. The issue is broader than early stopping alone.
  Next chosen step: proceed to Step 2, but treat it as a lighter control check rather than the main hypothesis. After that, prioritize Steps 3 and 4 to improve evaluation reliability and exploration quality.
- Step 2 result:
  Run analyzed: `training_runs/experiment-watchdog-relaxed-20260610T1320/train-20260610T135600.266653Z.json`
  Analysis: `training_runs/experiment-watchdog-relaxed-20260610T1320/analysis-train-20260610T135600.266653Z.json`
  Outcome: relaxing watchdog sensitivity materially improved training. The run completed all `40/40` generations, reached a new best at generation `29`, and substantially outperformed both the earlier watchdog-disabled control and the prior plateaued runs.
  Key facts: `best_fitness=605.3706255587076`, `validation_fitness=548.7445812858684`, `best_generation=29`, `total_best_fitness_delta=270.7419716536901`, `recent_best_fitness_delta=0.0`, `final_no_improvement_generations=11`, `mutation_pulse_count=5`.
  Interpretation: the earlier stopping regime was suppressing useful later improvements when watchdog remained enabled with stricter thresholds. Step 1 showed the search can still flatline; Step 2 shows that a more permissive watchdog can preserve late-generation gains while keeping the safety mechanism.
  Next chosen step: proceed to Step 3 using this improved Step 2 profile as the new baseline. The next question is whether increasing `games_per_genome` improves selection reliability further or only adds cost.
- Step 3 result:
  Run analyzed: `training_runs/experiment-games40-20260610T1420/train-20260610T142146.403052Z.json`
  Analysis: `training_runs/experiment-games40-20260610T1420/analysis-train-20260610T142146.403052Z.json`
  Outcome: increasing `games_per_genome` from `20` to `40` did not improve the current best profile. The run still found late improvements, but its final training and validation fitness were both materially below the Step 2 baseline while costing roughly 2x generation time.
  Key facts: `best_fitness=495.93497848201923`, `validation_fitness=473.3236943649615`, `best_generation=32`, `total_best_fitness_delta=157.26292024926374`, `recent_best_fitness_delta=3.8380342630260316`, `final_no_improvement_generations=8`, `mutation_pulse_count=5`, `total_generation_seconds=2393.2374652920003`.
  Interpretation: more scenarios per genome did reduce the train-validation gap, but it also changed the search landscape enough that the discovered solution quality dropped sharply relative to Step 2. This looks more like over-constraining evaluation or reducing useful search velocity than a net gain.
  Next chosen step: keep the Step 2 profile as the active baseline and proceed to Step 4 to test exploration pressure instead of further increasing evaluation cost.
- Step 4A result:
  Run analyzed: `training_runs/experiment-inject25-20260610T1510/train-20260610T150509.885079Z.json`
  Analysis: `training_runs/experiment-inject25-20260610T1510/analysis-train-20260610T150509.885079Z.json`
  Outcome: raising `inject_ratio` from `0.15` to `0.25` preserved late improvements, but it did not outperform the Step 2 baseline. Final training and validation fitness both fell well below the best relaxed-watchdog profile.
  Key facts: `best_fitness=531.5085032360945`, `validation_fitness=464.9712605598393`, `best_generation=34`, `total_best_fitness_delta=196.87984933107697`, `recent_best_fitness_delta=7.439168518661518`, `final_no_improvement_generations=6`, `mutation_pulse_count=6`, `total_generation_seconds=1202.1864588770004`.
  Interpretation: stronger random injection increased exploration churn and allowed a late jump, but the added randomness did not translate into better final solutions on this profile. This suggests the current bottleneck may be selection pressure quality rather than simply needing more injected variants.
  Next chosen step: keep Step 2 as the best baseline and proceed to Step 4B with `--tournament-size 3` to test whether softer selection works better than heavier injection.
- Step 4B result:
  Run analyzed: `training_runs/experiment-tournament3-20260610T1535/train-20260610T152927.674067Z.json`
  Analysis: `training_runs/experiment-tournament3-20260610T1535/analysis-train-20260610T152927.674067Z.json`
  Outcome: lowering `tournament_size` from `4` to `3` improved over Step 4A, but still did not beat the Step 2 baseline. The run found a best candidate at generation `24`, with stronger validation than Steps 3 and 4A, yet both training and validation remained below the relaxed-watchdog baseline.
  Key facts: `best_fitness=558.687184166541`, `validation_fitness=504.2287865388354`, `best_generation=24`, `total_best_fitness_delta=224.05853026152346`, `recent_best_fitness_delta=0.0`, `final_no_improvement_generations=16`, `mutation_pulse_count=6`, `total_generation_seconds=1163.266433913`.
  Interpretation: softer selection was more effective than heavier random injection, but the main win still came from relaxing watchdog sensitivity rather than from altering exploration pressure alone.
  Final conclusion for the original problem: the repeated pattern of max score going flat and getting stopped early was primarily caused by an over-strict watchdog configuration. The strongest fix found in this session is the Step 2 profile: `games_per_genome=20`, `inject_ratio=0.15`, `tournament_size=4`, `watchdog_patience=24`, `watchdog_min_generations=20`. That profile produced the best overall result with `best_fitness=605.3706255587076` and `validation_fitness=548.7445812858684`, with the best generation arriving late at generation `29` instead of stalling at generation `1`.
  Recommended next action: treat Step 2 as the new default training profile. If more work is needed, skip directly to Step 5 and repeat the Step 2 profile across multiple seeds to measure stability before testing more aggressive hyperparameter changes.
