# Decision Keeper

Hate writing down decisions? You tell yourself, “I’ll remember why we did that.” Six months later, the app has grown, someone asks why it works that way, and your only clue is a commit called `fix stuff`.

Decision Keeper is the friend who hears “Actually, let’s do it this way” and quietly writes down the new decision while you keep talking. One change at a time, those notes become a knowledge base for your project.

Decision Keeper maintains project decisions in `docs/decision/`.

## Prerequisites

You need Python 3.9 or newer. Your project must already have an instructions file before you install Decision Keeper.

- For Codex, use `AGENTS.md` at the project root.
- For Claude Code, use `CLAUDE.md` at the project root or `.claude/CLAUDE.md`.

If your project does not have the relevant file yet, create it with your project instructions before running the installer.

## Install

Clone or download this repository. From the Decision Keeper checkout, run the command for your client with the path to your own project root.

```bash
# Codex
python3 install.py --client codex "/path/to/your/project"

# Claude Code
python3 install.py --client claude "/path/to/your/project"
```

The installer appends a marked Decision Keeper section to your existing instructions and copies the skill into `.agents/skills/decision-keeper/` for Codex or `.claude/skills/decision-keeper/` for Claude Code. If both Claude instructions files exist, it updates the root `CLAUDE.md`. Run both commands if you use both clients in the same project. They share the same decision files.

To upgrade an older installation of Decision Keeper, Record Me, or Teach Me, rerun the command for each client you use.

## Use it

Start a new Codex or Claude Code session from your project root. Decision Keeper triggers automatically when you set, change, or remove a rule for future work. You can say it in your own words.

1. “From now on, use sentence case for all button labels.”
2. “Whenever you add a new screen, use the shared page layout.”
3. “Remember this for future changes: meeting times in emails use the venue’s local time zone.”
4. “Change our default reminder time from 45 minutes to 30 minutes.”
5. “Drop the rule that every new screen needs a welcome banner.”

Decision Keeper applies saved rules before future project changes and skips instructions that apply only to the current task. You can also ask it to organize the decision files at any time.

To record something explicitly, start your chat message with one of these prefixes.

| Prefix | What it does | Example |
| --- | --- | --- |
| `/keep` | Records the text and confirms where it was saved. | `/keep "Add a population-density heatmap"` |
| `/keep and go` | Records the text, then handles it as a normal request. | `/keep and go What data would a population-density heatmap need?` |

You can also invoke the skill directly with `$decision-keeper` in Codex or `/decision-keeper` in Claude Code. See the [Codex skills documentation](https://learn.chatgpt.com/docs/build-skills) and the [Claude Code skills documentation](https://code.claude.com/docs/en/skills) for more on skill discovery.

## Contributing

Everyone is welcome to contribute. Bug reports, documentation improvements, ideas, and pull requests are all appreciated. Include enough detail to reproduce a problem or explain a proposed change.

## License

Decision Keeper is released under the [MIT License](LICENSE). You may use, copy, modify, and distribute it, including for commercial use, provided you retain the copyright and license notices.

The software is provided “as is,” without warranty. To the extent permitted by applicable law, the creator and contributors are not liable for any claims, damages, data loss, or other liability arising from its use. See the license for the full terms.
