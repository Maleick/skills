# Secret Redaction Rules

Never store secret values in markdown memory notes.

Allowed in notes:
- environment variable name (`SERVICE_API_TOKEN`)
- redacted hint (`[REDACTED: service api token]`)
- storage location (`$CODEX_HOME/env/<project>/.env`)

Not allowed in notes:
- raw API keys
- tokens
- passwords
- private keys
- bearer tokens

When secret persistence is required:
1. Store with `store_secret_env.py`.
2. Reference only variable name and redacted hint in notes.
3. Redact secret-like strings in user-facing output.

Example safe note line:
- `Secrets: SERVICE_API_TOKEN stored in $CODEX_HOME/env/workspace/.env ([REDACTED])`
