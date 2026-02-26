# Security Policy

## Reporting a Vulnerability

If you discover a security vulnerability in TextTools, please report it responsibly.

**Do not open a public issue.** Instead, email the maintainer directly or use GitHub's private vulnerability reporting feature (Security tab > "Report a vulnerability").

### What to include

- Description of the vulnerability
- Steps to reproduce
- Affected version(s)
- Any potential impact you've identified

### Response timeline

- **Acknowledgment**: within 48 hours
- **Assessment**: within 1 week
- **Fix**: depends on severity, but we aim for prompt resolution

### Supported versions

| Version | Supported |
|---------|-----------|
| Latest on `main` | Yes |
| Older commits | No |

## Scope

TextTools is a local desktop application. Security concerns most likely involve:
- File handling vulnerabilities (path traversal, symlink attacks)
- Unsafe deserialization of user-provided data
- Dependencies with known CVEs
