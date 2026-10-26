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

The helper script `post_to_buffer.py` (added 2026-10-26) resolves this
automatically and does not require this field to be filled in.

## Helper script

`post_to_buffer.py` (stdlib only, no third-party deps):

```powershell
python post_to_buffer.py --list        # print the live queue, no network calls
python post_to_buffer.py --check       # verify BUFFER_API_KEY + resolve target profile
python post_to_buffer.py --post --yes  # publish (EXTERNAL — needs Brianna's approval)
```

It reads queued drafts from `SOCIAL_DRAFTS.md`, resolves the target X profile
(explicit `GOLDED_EYE_PROFILE_ID` env var first, then this file's
`profile_id`, then auto-match on the `gildedleovenus` alt account), posts via
`POST /updates/create.json`, then stamps the draft as `[POSTED]` and writes a
line to `MESSAGING_LOG.md`.

### Current status (2026-10-26)

`BUFFER_API_KEY` is set in the environment but Buffer returns **HTTP 401
Unauthorized**. The key is present and rejected, which means it is expired,
revoked, or wrong. It needs to be replaced with a fresh key from Buffer's
account settings. Until then `--post` cannot work. Nothing has been published
since 2026-06-18.

`BUFFER_CONFIG.md` must **not** be committed with a live key. Keep the key in
the environment only.
