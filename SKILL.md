---
name: decision-keeper
description: Capture and organize confirmed project decisions and reusable corrections in projects that have opted into Decision Keeper. Use when the user sets or revises a lasting rule for design, code, behavior, or business policy, or asks to organize the decision files. Skip one-off requests and brainstorming.
---

# Decision Keeper

Use only in an opted-in project. The project root has this skill in `.agents/skills/decision-keeper/` for Codex or `.claude/skills/decision-keeper/` for Claude Code, and the `<!-- decision-keeper:begin -->` block in the corresponding `AGENTS.md` or `CLAUDE.md` (which may be under `.claude/`). Resolve the `docs/decision/decision-keeper.md` index from that project root and resolve topic links relative to the file containing them, even when working in a subdirectory. Keep reads and writes for this workflow inside that project. Respect a request to keep the turn read-only or to skip saving the correction.

1. **Recognize a decision.** Capture a clear, lasting rule the user confirms, or a reusable correction to an existing or proposed choice. Corrective feedback like “Make the primary button solid” is enough. Skip ordinary task requirements with no lasting scope, tentative ideas, vague feedback, quoted examples, and explicit one-off exceptions. Store only the reusable rule. Omit secrets, personal data, and transcripts.
2. **Apply the decision.** Read the index in full if present. Open relevant topic files and follow their relevant child links before doing the work. Apply the rules at their narrowest supported scope. A correction to how the app presents dates applies to comparable date labels across screens. Preserve the user's choices about locale, stored timestamps, and API fields unless the correction changes them. The user's current instruction takes precedence over a recorded default. Resolve a material conflict with project requirements before recording a new default.
3. **Organize before writing.** Batch the confirmed decisions from the current request. Use the [organizer procedure](references/organizer.md) for every batch and for requests to organize the decision files. Resolve the procedure relative to this skill file. In Codex, if the installed `decision_keeper_organizer` subagent is available, give it the project root, confirmed decisions, and any explicit scope or supersession. Wait for its result before replying. In Claude Code or when that subagent is unavailable, follow the procedure in the current session. Keep one writer for the decision files. If a handoff fails, reload the current files before continuing in the current session.
4. **Verify and reply.** Use the organizer's verification to check the saved decisions and apply the relevant rules to the work. Continue without routine announcements about knowledge base edits. Surface an unresolved conflict or blocked write when it prevents the requested outcome.

Examples:

- “Make the signup primary button plain instead of gradient” → `- Use a solid fill for primary buttons.`
- “I don't like the notification date format. Write the month as text, then the day” → `- In user-facing date labels, show the month name before the day of the month.`
- “Use day first on this export only” → Apply the exception to the export and leave the rules unchanged.
- “From now on, show day before month in the app” → Replace the matching date rule and retain the month-name requirement if the user changed only the order.

## Manual triggers

Recognize these commands at the start of a user message. Match `/keep and go` before `/keep`. Treat the following text as explicitly selected for recording, with optional surrounding quotes. Use the organizer and identify the text as a manual entry. If the command has no text, ask what to record.

- `/keep <text>` records the text and replies only with where it was saved.
- `/keep and go <text>` records the text the same way, then handles it as a normal user request.
