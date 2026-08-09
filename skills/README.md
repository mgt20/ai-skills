# Portable skills

Each direct child directory is a portable skill. Copy the contents of this folder
into a harness's skills directory without flattening the individual skill folders:

```bash
cp -a skills/. ~/.hermes/skills/
```

| Skill | Purpose |
| --- | --- |
| `grocery-planner` | Review-only, sale-aware household grocery planning |

A copied skill provides instructions, references, and a neutral config template.
It does **not** include private household configuration, credentials, receipt data,
or generated shopping artifacts. The cloned repository remains the source for the
optional Python engine and store adapters.
