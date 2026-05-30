#!/usr/bin/env python3
"""Compare greedy play with an offline baseline that knows all future blocks."""

import argparse
import json
import os
import random
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, PROJECT_ROOT)
sys.path.insert(0, os.path.join(PROJECT_ROOT, "bot"))

from foresight import optimize_known_blocks, replay_slots, simulate_greedy_board_score
from scoring import evaluate_board
from training_data import generate_dataset, load_dataset, save_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--dataset", help="Existing CRN dataset JSON file")
    source.add_argument(
        "--generate-dataset",
        metavar="PATH",
        help="Generate one new scenario at PATH and compare it immediately",
    )
    parser.add_argument("--master-seed", type=int, help="Seed for --generate-dataset")
    parser.add_argument("--dataset-id", help="Dataset ID for --generate-dataset")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Replace an existing file passed to --generate-dataset",
    )
    parser.add_argument("--scenario-id", default="scenario-0001")
    parser.add_argument("--beam-width", type=int, default=500)
    parser.add_argument("--json-output", help="Optional path for machine-readable results")
    parser.add_argument("--no-ui", action="store_true", help="Do not open comparison windows")
    return parser


def _find_scenario(dataset, scenario_id):
    for scenario in dataset.scenarios:
        if scenario.scenario_id == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario_id: {scenario_id}")


def _payload(dataset, scenario, beam_width, greedy, foresight):
    turns = []
    for index, block in enumerate(scenario.blocks):
        turns.append({
            "turn": index + 1,
            "block": list(block),
            "greedy_slot": list(greedy.slots[index]),
            "greedy_board_score": greedy.turn_scores[index],
            "foresight_slot": list(foresight.slots[index]),
            "foresight_board_score": foresight.turn_scores[index],
        })
    return {
        "dataset_id": dataset.dataset_id,
        "scenario_id": scenario.scenario_id,
        "beam_width": beam_width,
        "note": "Foresight uses beam search and is not a proof of the absolute optimum.",
        "greedy_final_score": greedy.final_score,
        "foresight_final_score": foresight.final_score,
        "improvement": foresight.final_score - greedy.final_score,
        "greedy_expanded_states": greedy.expanded_states,
        "foresight_expanded_states": foresight.expanded_states,
        "turns": turns,
    }


def _load_or_generate_dataset(args):
    if args.dataset:
        if args.master_seed is not None or args.dataset_id or args.overwrite:
            raise ValueError("--master-seed, --dataset-id, and --overwrite require --generate-dataset")
        return load_dataset(args.dataset)

    master_seed = args.master_seed
    if master_seed is None:
        master_seed = random.SystemRandom().randrange(2 ** 63)
    dataset_id = args.dataset_id or f"known-future-{master_seed}"
    dataset = generate_dataset(dataset_id, "validation", master_seed, 1)
    path = save_dataset(dataset, args.generate_dataset, overwrite=args.overwrite)
    print(f"Generated dataset={dataset.dataset_id} master_seed={master_seed} path={path}")
    return dataset


def _display_results(scenario, greedy, foresight):
    from utils.display import display_final_game_state

    greedy_state = replay_slots(scenario.blocks, greedy.slots)
    foresight_state = replay_slots(scenario.blocks, foresight.slots)
    _, greedy_streaks = evaluate_board(
        greedy_state.get_grid_2d(), is_final=True, return_streaks=True
    )
    _, foresight_streaks = evaluate_board(
        foresight_state.get_grid_2d(), is_final=True, return_streaks=True
    )
    display_final_game_state(
        greedy_state.get_grid_2d(), greedy.final_score, greedy_streaks, "greedy", block=False
    )
    display_final_game_state(
        foresight_state.get_grid_2d(), foresight.final_score, foresight_streaks,
        "known-future foresight", block=True
    )


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dataset = _load_or_generate_dataset(args)
    scenario = _find_scenario(dataset, args.scenario_id)
    greedy = simulate_greedy_board_score(scenario.blocks)
    foresight = optimize_known_blocks(scenario.blocks, beam_width=args.beam_width)
    payload = _payload(dataset, scenario, args.beam_width, greedy, foresight)

    print("Offline known-future comparison (beam search, approximate)")
    print(f"dataset={dataset.dataset_id} scenario={scenario.scenario_id} beam_width={args.beam_width}")
    print("turn block       greedy slot score | foresight slot score")
    for turn in payload["turns"]:
        print(
            f"{turn['turn']:>4} {str(tuple(turn['block'])):<11} "
            f"{str(tuple(turn['greedy_slot'])):<8} {turn['greedy_board_score']:>5} | "
            f"{str(tuple(turn['foresight_slot'])):<8} {turn['foresight_board_score']:>5}"
        )
    print(
        f"final greedy={greedy.final_score} foresight={foresight.final_score} "
        f"improvement={payload['improvement']:+d} expanded={foresight.expanded_states}"
    )

    if args.json_output:
        with open(args.json_output, "w", encoding="utf-8") as output:
            json.dump(payload, output, indent=2)
            output.write("\n")
        print(f"Saved JSON report: {args.json_output}")
    if not args.no_ui:
        try:
            _display_results(scenario, greedy, foresight)
        except ImportError as error:
            print(f"Display not available: {error}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
