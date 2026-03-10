# Output Contract

Use this structure when Codex synthesizes the Claude and Gemini outputs.

## Main Format

```markdown
## Peer Review: {mode} — "{short title}"

### Director's Read
- What matters most in this repo or conversation context
- Which model had the stronger signal and why
- One Codex-only recommendation that neither model stated clearly

### Claude
{round 1 output or failure note}

### Gemini
{round 1 output or failure note}

### Cross-Examination Highlights
- strongest challenges
- strongest convergences
- notable position changes

### Consensus Items
| # | Issue | Claude Framing | Gemini Framing |
|---|-------|----------------|----------------|

### Decision Packet
**Summary:** {count and severity mix}
**Recommended path:** {single clear recommendation}
**Top 3 risks:** {ranked}
**Open questions:** {if any}

**Actionable items**
1. {action} *(Claude/Gemini/consensus)* **[HIGH|MEDIUM|LOW CONFIDENCE]**

### Priority Matrix
| | Low Effort | High Effort |
|---|---|---|
| High Impact | {items} | {items} |
| Low Impact | {items} | {items} |

---
**What would you like to do with this feedback?**
- Accept all
- Cherry-pick
- Refine
- Discard
```

## Rules

- Number actionable items sequentially so cherry-picking is easy.
- Put findings first. Do not bury the sharpest issues.
- Mark single-source items lower confidence if the other model did not support them.
- If one model failed, say so plainly and continue with the surviving output.
- If both models failed, do not fabricate a decision packet.

## Mode-Specific Additions

- `debate`: add `Judge's Verdict`
- `advocate`: add `Advocate vs. Critic Summary`
- `deploy`: add `Deployment Readiness Checklist`
- `api`: add `API Design Scorecard`
- `perf`: add `Performance Assessment`
- `quick`: skip the full packet and give a short Codex-directed summary after the raw outputs

## Follow-Up Behavior

- `Cherry-pick`: retain only the requested numbered items and restate them as a checklist.
- `Refine`: ask one targeted follow-up to the most relevant model, or both if the user explicitly wants that.
- `Discard`: stop cleanly without converting items into tasks.
