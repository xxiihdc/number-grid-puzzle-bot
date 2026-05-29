# Research Findings: Post-Game Score Visualization

## Decision: Language/Version
**Chosen**: Python 3.9+ (consistent with existing codebase)
**Rationale**: The existing codebase uses Python 3.9+ as evidenced by the reference implementation in `ref/main.py` and project requirements. Maintaining version consistency ensures compatibility and reduces setup complexity.
**Alternatives considered**: 
- Python 3.11+: Would require verifying compatibility with existing dependencies
- Other languages: Would require significant rewrite and break integration with existing bot code

## Decision: Primary Dependencies
**Chosen**: numpy, matplotlib (already used in ref/main.py)
**Rationale**: The reference implementation in `ref/main.py` already demonstrates successful use of numpy for array operations and matplotlib for graphical display. These dependencies are already satisfied in the development environment.
**Alternatives considered**:
- Pure Python implementations: Would be significantly slower for numerical operations
- Alternative GUI frameworks (Tkinter, PyQt, etc.): Would require learning new APIs and may not integrate as well with existing matplotlib-based code

## Decision: Storage
**Chosen**: N/A (in-memory display only, no persistence needed)
**Rationale**: The feature is purely for visualizing the final game state. All required data (final board state, score, winning streaks) is available in memory at game completion and doesn't need to be stored beyond the display duration.
**Alternatives considered**:
- File-based storage: Would add unnecessary complexity for a transient display
- Database storage: Completely overkill for this simple use case

## Decision: Testing
**Chosen**: pytest (consistent with Python project standards)
**Rationale**: Using the same testing framework as the rest of the project ensures consistency in test running, reporting, and development practices.
**Alternatives considered**:
- unittest: Built-in but less feature-rich than pytest
- nose2: Less commonly used in modern Python projects

## Decision: Target Platform
**Chosen**: Desktop (macOS, Linux, Windows - wherever matplotlib is supported)
**Rationale**: matplotlib is a cross-platform library that works on all major desktop operating systems. The existing reference implementation confirms it works on macOS (development environment).
**Alternatives considered**:
- Web-based display: Would require setting up a web server and introduce unnecessary complexity
- Mobile platforms: Would require completely different GUI frameworks and doesn't match the desktop development context

## Decision: Project Type
**Chosen**: desktop-app feature (GUI display component)
**Rationale**: The feature is a graphical window that displays game results, which is characteristic of a desktop application component rather than a library, CLI, or web service.
**Alternatives considered**:
- Library: While the display function could be packaged as a library, it's primarily an application feature
- CLI: Doesn't match the graphical nature of the requirement
- Web service: Would be overkill for a local display feature

## Decision: Performance Goals
**Chosen**: Display window appears within 1 second of game completion
**Rationale**: This provides a responsive user experience without being overly restrictive. The existing reference implementation likely already meets this goal.
**Alternatives considered**:
- <100ms: Unnecessarily strict for a GUI display feature
- <5 seconds: Too slow for good user experience

## Decision: Constraints
**Chosen**: Must not activate during tournament/batch mode; must handle headless environments gracefully
**Rationale**: These directly address requirements from the specification:
- Not activating during tournament/batch mode prevents disruption of automated processes
- Graceful headless handling allows the code to run in server environments without crashing
**Alternatives considered**:
- Always display: Would interfere with batch processing
- Crash in headless: Would prevent running in server/container environments

## Decision: Scale/Scope
**Chosen**: Single functionality addition - post-game visualization display
**Rationale**: The feature is specifically defined as a single function that displays the final game state after all 27 turns are complete. It doesn't affect core game logic, training processes, or other systems.
**Alternatives considered**:
- Per-turn display: Explicitly ruled out by the requirement ("not for each turn")
- Integrated game mode selection: Would complicate the simple post-game display requirement