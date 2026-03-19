# Buffer Config — The Gilded Eye

## API endpoints

- Base URL: https://api.bufferapp.com/1/
- Profiles endpoint: GET /profiles.json
- Updates endpoint: POST /updates/create.json

## Auth

- Use an environment variable named `BUFFER_API_KEY` on your machine.
- Do **not** hardcode the key in this repo.

### Setting BUFFER_API_KEY (examples)

**PowerShell (per-session):**
```powershell
$env:BUFFER_API_KEY = "your_buffer_api_key_here"
```

**PowerShell (profile script):**
- Add the line above to your `$PROFILE` if you want it set automatically for new shells.

**cmd.exe (per-session):**
```cmd
set BUFFER_API_KEY=your_buffer_api_key_here
```

**bash/zsh (per-session):**
```bash
export BUFFER_API_KEY="your_buffer_api_key_here"
```

**bash/zsh (permanent):**
- Add the export line to `~/.bashrc`, `~/.zshrc`, or equivalent.

## Profile ID

- `profile_id`: `<TO_BE_FILLED>`

Once you have `BUFFER_API_KEY` set, run a small helper script (to be added)
that:
- Calls `GET /profiles.json` with the Bearer token.
- Finds the profile corresponding to the `gildedleovenus` alt Twitter account.
- Writes the chosen `profile_id` back into this file.

The posting script will then read `BUFFER_API_KEY` from the environment and
`profile_id` from this file, and queue posts from `SOCIAL_DRAFTS.md`.
