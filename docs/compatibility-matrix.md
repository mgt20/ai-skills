# Compatibility matrix

| Integration | Status | Boundary |
|---|---|---|
| Generic local Python | Supported | Core package and local files |
| Hermes | Documented | Skill + profile/workdir + optional cron |
| OpenClaw | Documented | Skill + workspace + harness scheduler |
| Safeway/Flipp | Bootstrap | Sanitized fixture; live source must be configured |
| Recipe providers | Planned | Must be a separately reviewed, optional edge adapter |

“Documented” means the skill is usable by the harness; it does not imply an automatic installer or delivery integration.
