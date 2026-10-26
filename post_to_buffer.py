#!/usr/bin/env python3
"""
Gilded Eye — Buffer posting helper.

Status: internal tooling. Posting is EXTERNAL and requires Brianna's explicit
approval plus a working BUFFER_API_KEY. Default mode is --list (dry run).

Setup
-----
1. BUFFER_API_KEY must be set in the environment.
2. The X profile to post to must resolve to exactly one match. Resolution order:
   a. GOLDED_EYE_PROFILE_ID env var (explicit wins)
   b. BUFFER_CONFIG.md "profile_id" field if it has been filled in
   c. auto-match on service=twitter and service_username containing
      "gildedleovenus" (the alt account, not Brianna's main)

Usage
-----
    python post_to_buffer.py --list              # show queued posts, no network
    python post_to_buffer.py --check             # verify key + resolve profile
    python post_to_buffer.py --post --yes        # actually publish

Stdlib only. No third-party deps.
"""

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
DRAFTS = HERE / "SOCIAL_DRAFTS.md"
CONFIG = HERE / "BUFFER_CONFIG.md"
LOG = HERE / "MESSAGING_LOG.md"

API = "https://api.bufferapp.com/1"
PROFILE_HINT = "gildedleovenus"


# ---------------------------------------------------------------- queue parsing

def parse_queue(text):
    """Pull unposted tweet drafts out of SOCIAL_DRAFTS.md.

    Recognised block format:
        ## Tweet N [ANGLE]
        <body>

    Only blocks that appear BEFORE the first dated weekly-posts heading are
    treated as the live queue. Blocks already marked [POSTED] are skipped.
    """
    live_end = len(text)
    m = re.search(r"^#\s+\d{4}-\d{2}-\d{2}\s+Weekly\s+Posts", text, re.M)
    if m:
        live_end = m.start()

    live = text[:live_end]
    blocks = re.findall(
        r"^##\s+Tweet\s+(\d+)\s*\[([^\]]*)\]\s*\n(.*?)(?=^##\s+Tweet|\Z)",
        live,
        re.M | re.S,
    )
    queue = []
    for num, angle, body in blocks:
        # Strip horizontal rules / stray separators that some blocks carry.
        body = "\n".join(
            line for line in body.strip().splitlines()
            if line.strip() not in ("---", "***", "___")
        ).strip()
        if not body or "[POSTED]" in body:
            continue
        queue.append({
            "id": int(num),
            "angle": angle.strip(),
            "text": body,
        })
    return queue


def mark_posted(text, body_text):
    """Stamp a tweet block as POSTED so it leaves the live queue.

    Matches on the exact body text rather than the tweet number, because the
    draft file has historical duplicate numbers (two "Tweet 2" blocks).
    """
    needle = body_text.strip()
    pattern = re.compile(
        r"(^##\s+Tweet\s+\d+\s*\[[^\]]*\]\s*\n)(.*?)(?=\n##\s+Tweet|\Z)",
        re.M | re.S,
    )
    def repl(m):
        body = m.group(2)
        stripped = "\n".join(
            line for line in body.strip().splitlines()
            if line.strip() not in ("---", "***", "___")
        ).strip()
        if stripped != needle:
            return m.group(0)
        return m.group(1) + body.rstrip() + "\n[POSTED]\n"
    return pattern.sub(repl, text, count=1)


# ------------------------------------------------------------------- buffer api

def api_get(path, key):
    req = urllib.request.Request(
        API + path,
        headers={"Authorization": "Bearer " + key},
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def api_post(path, key, payload):
    body = urllib.parse.urlencode(payload).encode("utf-8")
    req = urllib.request.Request(
        API + path,
        data=body,
        headers={
            "Authorization": "Bearer " + key,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.loads(r.read().decode("utf-8"))


def resolve_profile(profiles, explicit_id=None):
    """Pick the target X profile. Returns (profile_dict, reason)."""
    if explicit_id:
        for p in profiles:
            if str(p.get("id")) == str(explicit_id):
                return p, "explicit id"
        return None, "explicit id not found"

    twitters = [p for p in profiles if p.get("service") == "twitter"]
    matches = [
        p for p in twitters
        if PROFILE_HINT in (p.get("service_username") or "").lower()
    ]
    if len(matches) == 1:
        return matches[0], "auto-matched alt account"
    if len(matches) > 1:
        return None, "multiple alt-account matches, set GOLDED_EYE_PROFILE_ID"
    if len(twitters) == 1:
        return twitters[0], "only twitter profile available"
    return None, "no unambiguous twitter profile, set GOLDED_EYE_PROFILE_ID"


def read_config_profile_id():
    if not CONFIG.exists():
        return None
    m = re.search(r"`profile_id`\s*:\s*`([^`]+)`", CONFIG.read_text(encoding="utf-8", errors="ignore"))
    if m:
        val = m.group(1).strip()
        if val and val != "<TO_BE_FILLED>":
            return val
    return None


# ------------------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true", help="list queued posts, no network calls")
    ap.add_argument("--check", action="store_true", help="verify API key and resolve target profile")
    ap.add_argument("--post", action="store_true", help="publish queued posts to Buffer")
    ap.add_argument("--yes", action="store_true", help="confirm --post")
    ap.add_argument("--limit", type=int, default=1, help="max posts to publish in one run")
    args = ap.parse_args()

    if not DRAFTS.exists():
        print("ERROR: %s not found" % DRAFTS, file=sys.stderr)
        return 2

    text = DRAFTS.read_text(encoding="utf-8", errors="ignore")
    queue = parse_queue(text)

    if args.list or not (args.check or args.post):
        print("GILDED EYE — QUEUE (%d live draft(s))" % len(queue))
        for item in queue:
            print("")
            print("  Tweet %d  [%s]" % (item["id"], item["angle"]))
            print("  " + "-" * 60)
            for line in item["text"].splitlines():
                print("  " + line)
        if not queue:
            print("  (queue empty)")
        return 0

    key = os.environ.get("BUFFER_API_KEY")
    if not key:
        print("ERROR: BUFFER_API_KEY is not set in the environment.", file=sys.stderr)
        return 2

    try:
        profiles = api_get("/profiles.json", key)
    except urllib.error.HTTPError as e:
        print("ERROR: Buffer API returned HTTP %s" % e.code, file=sys.stderr)
        print("       The key is present but rejected. It needs to be replaced.", file=sys.stderr)
        return 3
    except Exception as e:
        print("ERROR: could not reach Buffer API: %s" % e, file=sys.stderr)
        return 3

    explicit = os.environ.get("GOLDED_EYE_PROFILE_ID") or read_config_profile_id()
    profile, reason = resolve_profile(profiles, explicit)

    print("Buffer auth: OK")
    print("Profile resolution: %s" % reason)
    if profile:
        print("  id=%s service=%s user=@%s" % (
            profile.get("id"), profile.get("service"), profile.get("service_username")))
    else:
        print("  NO PROFILE RESOLVED — cannot post.")
        return 4

    if args.check:
        return 0

    if not args.yes:
        print("")
        print("Refusing to post without --yes. Re-run with --post --yes to publish.")
        return 1

    published = 0
    for item in queue[: args.limit]:
        payload = {
            "profile_ids[]": profile["id"],
            "text": item["text"],
            "now": "true",
        }
        try:
            api_post("/updates/create.json", key, payload)
        except Exception as e:
            print("ERROR publishing tweet %d: %s" % (item["id"], e), file=sys.stderr)
            break
        published += 1
        print("Published tweet %d [%s]" % (item["id"], item["angle"]))
        text = mark_posted(text, item["text"])
        DRAFTS.write_text(text, encoding="utf-8")

    if published:
        stamp = "## %s Post Log\n\n- Posted %d update(s) via Buffer.\n- Queue state updated in SOCIAL_DRAFTS.md\n\n---\n\n" % (
            __import__("datetime").date.today().isoformat(), published)
        if LOG.exists():
            existing = LOG.read_text(encoding="utf-8", errors="ignore")
            LOG.write_text(stamp + existing, encoding="utf-8")

    return 0


if __name__ == "__main__":
    sys.exit(main())
