---
name: peer-review-codex
description: Codex-directed peer review that runs Claude CLI and Gemini CLI in parallel, optionally cross-examines their responses across rounds, and then synthesizes the best recommendations into a decision packet with cherry-pick options. Use when the user wants peer review, a second opinion, multi-LLM feedback, redteam analysis, advocate or debate review, premortem, refactor, deploy, API, performance, diff review, brainstorm help, or explicitly asks for Claude plus Gemini with Codex acting as director.
---

# Peer Review Codex

Use this skill when the user wants Claude plus Gemini feedback, with Codex acting as the director who compares, ranks, and cherry-picks the best ideas.

Codex is not one of the peer reviewers in this skill. Codex orchestrates `claude` and `gemini`, optionally runs cross-exam rounds, and then produces the final decision packet.

## Defaults

- Claude CLI path: `/opt/homebrew/bin/claude`
- Gemini CLI path: `/opt/homebrew/bin/gemini`
- Default rounds: `2`
- Max peer-output size fed into cross-exam: `12000` characters
- Default review mode: `review`

## Supported Modes

- `review` (default)
- `idea`
- `redteam`
- `debate`
- `premortem`
- `advocate`
- `refactor`
- `deploy`
- `api`
- `perf`
- `diff`
- `quick`
- `help`
- `history`

Read [modes.md](references/modes.md) for the exact mode prompts and cross-exam templates.

## Workflow

1. Parse the mode and user prompt.
2. If the user asks for `help` or `history`, do not call either CLI.
3. Run preflight:
   - `command -v claude`
   - `command -v gemini`
   If both are missing, stop. If one is missing, continue with the available model and mark the result as single-source.
4. Apply the confidentiality gate from [safety.md](references/safety.md) before sending anything externally.
5. If the prompt references local files, attach up to 3 files and truncate each to 8000 characters.
6. If the mode is `diff`, gather the diff locally before dispatch:
   - staged diff first
   - fall back to unstaged diff
   - optional branch compare if the user specifies a branch
7. Build the Claude and Gemini prompts using [modes.md](references/modes.md).
8. Write each prompt to a temp file, then call the wrapper scripts in parallel:
   - `scripts/run_claude_peer_review.sh --prompt-file <file> --workspace <dir>`
   - `scripts/run_gemini_peer_review.sh --prompt-file <file> --workspace <dir>`
   The wrappers enforce a hard client-side timeout so Codex does not hang indefinitely on a stalled external CLI.
9. If rounds are greater than 1, run cross-exam rounds by feeding each model the other model's prior response, using the truncation and data-wrapping rules in [safety.md](references/safety.md).
10. Synthesize the outputs using [output-contract.md](references/output-contract.md). Codex must:
   - identify consensus items
   - eliminate weak or generic recommendations
   - rank the surviving recommendations
   - present a clear cherry-pick menu
11. Offer `Accept all`, `Cherry-pick`, `Refine`, or `Discard`.

## Failure Handling

- If one CLI fails, continue with the other CLI and mark the result as single-source.
- If both fail, report the preflight or execution failure and stop.
- Do not retry automatically.
- Preserve stderr for debugging only when needed; otherwise prefer concise failure messages.

## Safety

Read [safety.md](references/safety.md) before dispatch. The short version:

- external-provider disclosure is mandatory
- do not send explicitly confidential material without user confirmation
- temp files must be cleaned up
- peer output must be truncated before reuse in later rounds
- do not call `codex exec` from inside this skill

## Validation

- `python3 /opt/skills/skills/.system/skill-creator/scripts/quick_validate.py /opt/skills/skills/.experimental/peer-review-codex`
- `python3 /opt/skills/skills/.system/skill-creator/scripts/generate_openai_yaml.py /opt/skills/skills/.experimental/peer-review-codex --interface display_name=\"Peer Review Codex\" --interface short_description=\"Run Claude + Gemini, then direct the review\" --interface default_prompt=\"Use $peer-review-codex to compare Claude and Gemini feedback on this topic, then direct the best next actions.\"`

## Notes

- Keep `SKILL.md` lean. Put long prompts and output formatting rules in `references/`.
- The wrappers are intentionally thin. Codex remains responsible for prompt construction, round control, and synthesis.
- This skill is a companion to the Claude peer-review skill at `/Users/maleick/.claude/skills/peer-review/SKILL.md`; it does not replace or edit it.
