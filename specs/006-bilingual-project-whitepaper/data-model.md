# Data Model: Bilingual Project Whitepaper

## Whitepaper Section

- `title`: stable navigational heading
- `english_guidance`: concise English explanation
- `vietnamese_guidance`: equivalent Vietnamese explanation
- `commands`: runnable examples when applicable
- `references`: links to deeper source documents when applicable

## Command Entry

- `purpose`: what the command does
- `command`: runnable shell example
- `inputs`: required and optional flags
- `outputs`: generated files or visible behavior
- `headless_notes`: non-GUI alternative where applicable

## Training Parameter Entry

- `flag`: CLI option
- `meaning`: optimization behavior controlled by the value
- `valid_values`: accepted range or type
- `tuning_effect`: expected tradeoff when adjusted

## Documentation Impact Rule

- `trigger`: user-facing, command, parameter, architecture, log, or optimization change
- `required_action`: update `WHITEPAPER.md` or record why no update is required
- `review_locations`: constitution, `CLAUDE.md`, `AGENTS.md`, shared tasks template
