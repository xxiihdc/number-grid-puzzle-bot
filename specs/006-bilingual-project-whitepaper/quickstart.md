# Quickstart: Bilingual Project Whitepaper

Validate documented command surfaces:

```sh
python3 run_bot.py --help
python3 run_bot.py train --help
python3 run_bot.py replay --help
python3 scripts/generate_training_seeds.py --help
python3 scripts/plot_training_log.py --help
python3 scripts/sync_latest_weights.py --help
python3 scripts/compare_known_future.py --help
python3 test_training_cli.py
```

Review the canonical manual:

```sh
sed -n '1,320p' WHITEPAPER.md
```

Confirm governance propagation:

```sh
rg -n "WHITEPAPER.md|whitepaper" .specify/memory/constitution.md CLAUDE.md AGENTS.md \
  .specify/templates/tasks-template.md README.md
```
