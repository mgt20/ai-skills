---
name: tech-diary-writer
description: Drafts a dated entry for my tech diary (homelab/ops work journal kept in a Google Doc) summarizing what was actually done in the current session, in the journal's terse bullet style. Use when asked to "make a journal entry", "tech diary", "diary entry", "log what we did today", "write up today for my journal", "add this to my log", or at the end of a session of homelab, server, website, hardware, or infra work.
---

# Tech diary writer

Write a short, dated log entry of the work done in this session, matching the
existing journal exactly. The entry is for the user's own future reference:
what changed, where, and any key detail they'd want when debugging later.

## Format

```
YYYY-MM-DD:

* Past-tense action, specific nouns (host, VM, version, product)
   * Sub-bullet only for a cause, a key detail, or a follow-up
```

- Date line first, then a blank line, then bullets. Use the user's local date
  (not UTC) for the day the work happened.
- Top-level bullets are `* ` with a past-tense verb: Fixed, Replaced, Upgraded,
  Installed, Moved, Swapped out, Finished, Setup, Ordered.
- Sub-bullets are indented three spaces then `* `.
- Keep it terse: one line per bullet, no full paragraphs, no headings, no
  bold, no emoji. Name the concrete thing (e.g. `pve03`, `plex-backup VM`,
  `Debian 13 (Trixie)`, `7.0.12-1-pve`).
- One entry may hold anywhere from 1 to ~6 top-level bullets. Group related
  steps under one bullet rather than listing every command.
- Follow-ups that weren't done go as sub-bullets prefixed `TODO:`.

## Reference examples (from the real journal)

```
2026-10-06:

* Fixed website outage (WordPress critical error / HTTP 500\)  
  * Cause: plugin update pulled in Composer deps requiring PHP \>= 8.3  
  * Upgraded hosting PHP to 8.3 in cPanel  
* Replaced expired origin SSL cert on cPanel with 15-year Cloudflare Origin Certificate  
  * Switched Cloudflare SSL/TLS mode to Full (strict)  
* Ran health/security check on website. All 90 sitemap URLs returning 200, TLS 1.2/1.3 only  
  * TODO: block ?rest\_route=/wp/v2/users (leaks username), disable users sitemap  
  * TODO: enable HSTS \+ security headers in Cloudflare  
  * TODO: hide WP version, add SEO plugin, delete Sample Page, clean up tags

2026-07-29:

* Setup mnemosyne for hermes agent

2026-07-28:

* Replaced failing HDD fan on pve03  
* Installed labels on mini rack   
* Installed Shelly plugs and short power cables on mini rack 

2026-07-27:

* Upgraded plex-backup VM to Debian 13 (Trixie) and updated plex container to latest version (`docker compose pull`)

2026-07-01:

* Unpinned 6.5.13 kernel on proxmox cluster. Moved to 7.0.12-1-pve

2026-06-26:

* Swapped out bad CPU blower fan on pve03  
  * Ordered 2 replacements from Aliexpress

2024-11-12:

* Figured out to use “GPU” in tdarr on streaming VM to use intel qsv for transcoding. Lowered CPU load by about 50%  
* Added new Zigbee temp sensor for minirack

2024-11-08:

* Setup one factor auth for 192.168.0.0/24 on authelia – this didn’t work, i think because of cloudflare

2024-05-16:

* Saved proxmox nodes. Pinned 6.5? Kernel   
* Meshcentral is now working\!  
* CAD play   
* Setup backup Plex 

2024-05-08:

* Setup Meshcentral finally\! Configured Intel AMT on each HP except for monitoring box.   
  * Bought and added DP dummy plugs to provide EDID to pc and to have it generate a UI over meshcentral  
* Setup lubelogger, Wallos,  
  * Added to uptime Kuma and homer   
* VLANs setup\!

2024-04-28:

* Kometa  
  * Configured mdb api integration  
    * Created mdb account using trakt.tv auth  
  * Moved “...in-history” files from metadata to collections so they’d get correctly picked up and error "metadata attribute is required" would go away for them  
```

## Rules

1. Only log what actually happened in this session. Do not log advice the
   user was given but didn't confirm doing. If a step's outcome is unknown
   (e.g. they fixed something but didn't say how), write the most likely
   version and tell the user which line to verify.
2. Do not include secrets, private keys, passwords, IPs of private hosts, or
   usernames that were found to be exposed. Describe them generically.
3. Output the entry in a single fenced code block so it pastes cleanly, then
   at most one or two lines noting any assumption.
4. If a Google Drive/Docs connector is available and the user wants it
   written into the doc, read the doc first, insert the new entry at the top
   (newest first) with two blank lines before the previous entry, and match
   the existing formatting. Otherwise, draft it in chat for them to paste.
