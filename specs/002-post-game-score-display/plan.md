# Implementation Plan: [FEATURE]

**Branch**: `[###-feature-name]` | **Date**: [DATE] | **Spec**: [link]

**Input**: Feature specification from `/specs/[###-feature-name]/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

[Extract from feature spec: primary requirement + technical approach from research]

## Technical Context

<!--
  ACTION REQUIRED: Replace the content in this section with the technical details
  for the project. The structure here is presented in advisory capacity to guide
  the iteration process.
-->

**Language/Version**: Python 3.9+ (consistent with existing codebase)

**Primary Dependencies**: numpy, matplotlib (already used in ref/main.py)

**Storage**: N/A (in-memory display only, no persistence needed)

**Testing**: pytest (consistent with Python project standards)

**Target Platform**: Desktop (macOS, Linux, Windows - wherever matplotlib is supported)

**Project Type**: desktop-app feature (GUI display component)

**Performance Goals**: Display window appears within 1 second of game completion

**Constraints**: Must not activate during tournament/batch mode; must handle headless environments gracefully

**Scale/Scope**: Single functionality addition - post-game visualization display

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

### I. Mathematical Rigor
- **Status**: PASS
- **Explanation**: While the display function itself doesn't involve mathematical computation, it visualizes the results of mathematically rigorous game play and scoring algorithms that are already constitutionally compliant in the existing codebase.

### II. Algorithmic Efficiency
- **Status**: PASS
- **Explanation**: The display function is called only once per game (after 27 turns), so efficiency is not critical. However, it reuses existing efficient components from `ref/main.py` and uses standard libraries (matplotlib) appropriately.

### III. Adaptive Phased Strategies
- **Status**: PASS
- **Explanation**: This principle applies to the game playing strategy, not the display function. Our feature is orthogonal to gameplay strategy and doesn't interfere with adaptive phased approaches.

### IV. Automated Feature Discovery
- **Status**: PASS
- **Explanation**: This principle applies to heuristic optimization in the training engine. Our display feature is a presentation layer that doesn't involve heuristic feature selection.

### V. Genetic Algorithm Optimization
- **Status**: PASS
- **Explanation**: This principle applies to the offline training process. Our feature is purely for visualization and doesn't interact with the genetic algorithm training process.

### VI. Separation of Concerns
- **Status**: PASS
- **Explanation**: The display function cleanly separates presentation (concern) from inference (real-time move selection) and training (offline heuristic optimization). It only activates after inference is complete.

### VII. Action Space Reduction
- **Status**: PASS
- **Explanation**: This principle applies to the game playing algorithms that operate within the reduced 27-slot action space. Our display function works with the final game state regardless of how it was reached.

## Constitution Check Result: ALL PRINCIPLES PASS - GATE CLEARED

## Project Structure

### Documentation (this feature)

```text
specs/[###-feature]/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)
<!--
  ACTION REQUIRED: Replace the placeholder tree below with the concrete layout
  for this feature. Delete unused options and expand the chosen structure with
  real paths (e.g., apps/admin, packages/something). The delivered plan must
  not include Option labels.
-->

```text
# [REMOVE IF UNUSED] Option 1: Single project (DEFAULT)
src/
├── models/
├── services/
├── cli/
└── lib/

tests/
├── contract/
├── integration/
└── unit/

# [REMOVE IF UNUSED] Option 2: Web application (when "frontend" + "backend" detected)
backend/
├── src/
│   ├── models/
│   ├── services/
│   └── api/
└── tests/

frontend/
├── src/
│   ├── components/
│   ├── pages/
│   └── services/
└── tests/

# [REMOVE IF UNUSED] Option 3: Mobile + API (when "iOS/Android" detected)
api/
└── [same as backend above]

ios/ or android/
└── [platform-specific structure: feature modules, UI flows, platform tests]
```

**Structure Decision**: Option 1: Single project (DEFAULT) - The feature will be implemented as a module within the existing bot/ or utils/ directory, following the current project structure. Based on the existing codebase, the display function will likely be added to utils/ or bot/ as a helper module.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| [e.g., 4th project] | [current need] | [why 3 projects insufficient] |
| [e.g., Repository pattern] | [specific problem] | [why direct DB access insufficient] |
