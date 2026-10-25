# HaruQuantAI CLI

Run these commands from the project root in PowerShell. The CLI runs headlessly without starting a Uvicorn HTTP server.

## Login

```powershell
uv run python -m app.cli login --username YOUR_USERNAME
```

Enter your password at the prompt. Login returns a JSON response containing the session token in `data.token`. Use the username and password configured in the application settings.

## Set the session token

Copy the token from the login response into the current PowerShell session:

```powershell
$env:HARUQUANTAI_SESSION_TOKEN = "TOKEN_FROM_LOGIN"
```

Treat this token as a credential. Do not share it or commit it to source control.

## Check health

```powershell
uv run python -m app.cli health
```

Checks local settings and session storage and returns a JSON result. When `HARUQUANTAI_SESSION_TOKEN` is set, the command also validates the CLI session and refreshes its sliding 24-hour inactivity timeout. An invalid, expired, revoked, or UI-issued token fails validation.

Without a token, this command performs the basic local health check without authentication. It does not check broker connectivity or HTTP server availability.

## Logout

```powershell
uv run python -m app.cli logout
Remove-Item Env:HARUQUANTAI_SESSION_TOKEN -ErrorAction SilentlyContinue
```

Logout revokes the token supplied through `HARUQUANTAI_SESSION_TOKEN`. The second command clears it from the current shell. CLI sessions use `peer_id="cli"` in `host_session`; logout does not revoke UI sessions.

## Help

```powershell
uv run python -m app.cli --help
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Command succeeded. |
| `1` | Health, authentication, or session operation failed, or login was cancelled. |
| `2` | Invalid or missing command-line arguments. |

Command results are written as JSON to standard output. Operational messages use central logging.
