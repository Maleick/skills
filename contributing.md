## Contributing

### Community values

- **Be kind and inclusive.** Treat others with respect; we follow the [Contributor Covenant](https://www.contributor-covenant.org/).
- **Assume good intent.** Written communication is hard - err on the side of generosity.
- **Teach & learn.** If you spot something confusing, open an issue or PR with improvements.

### Security & responsible AI

Have you discovered a vulnerability or have concerns about model output? Please e-mail **security@openai.com** and we will respond promptly.

### Skill audit CI policy

Use CI mode for deterministic gate behavior in automation:

```bash
python3 -m tools.skill_audit.cli --ci
```

Policy modes:

```bash
# Strict gate
python3 -m tools.skill_audit.cli --ci --max-severity valid

# Warning-tolerant gate with explicit scope
python3 -m tools.skill_audit.cli --ci --tiers experimental --max-severity warning

# Strict curated-only scope
python3 -m tools.skill_audit.cli --ci --tiers curated --max-severity valid
```

Artifact-emitting CI run:

```bash
python3 -m tools.skill_audit.cli \
  --ci \
  --json-out .artifacts/skill-index.json \
  --markdown-out .artifacts/skill-remediation.md
```

Exit codes:
- `0`: gate pass
- `1`: policy failure (severity threshold exceeded in scope)
- `2`: runtime or configuration error
