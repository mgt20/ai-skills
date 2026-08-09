# Security and privacy

Do not report or commit credentials, receipt exports, loyalty identifiers, home addresses, shopping history, or generated household plans. If a secret is committed, revoke it first, then report the file path and remediation without reproducing the secret.

Provider integrations must use environment variables or private local configuration for credentials. The project does not implement checkout or payment flows.

Before changing repository visibility to public, scan **all reachable Git history** as well as the working tree. Remove private modules and redact/rewrite any sensitive history before publishing; deleting a file only in the latest commit is not sufficient.
