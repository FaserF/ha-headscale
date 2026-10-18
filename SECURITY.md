# Security Best Practices for Home Assistant OmniRoute Integration

When integrating your OmniRoute AI Gateway with Home Assistant, it is highly recommended to follow security best practices to protect your network and data privacy.

## 1. Authentication and API Keys
- **API Key Protection**: If your OmniRoute gateway is accessible outside of a private loopback or isolated Docker network, always configure and require an API key (`Authorization: Bearer <token>`).
- **Secret Redaction**: API keys and tokens are strictly redacted from diagnostic downloads (`diagnostics.py`). Never share raw configuration files or unredacted HTTP authorization headers in public issue reports.

## 2. Network Security
- **Isolated Local Network**: Run OmniRoute on an internal Docker bridge or trusted local subnet (e.g. `http://omniroute:20128/v1` or `http://127.0.0.1:20128/v1`).
- **Encrypted Transport (TLS/HTTPS)**: If routing across external subnets or over the internet, enforce HTTPS/TLS termination via a reverse proxy to prevent eavesdropping of prompts and LLM completions.

## 3. Reporting a Vulnerability
If you discover a security vulnerability within this integration, please report it privately:
- Open a private security advisory on GitHub: [Security Advisory](https://github.com/FaserF/ha-omniroute/security/advisories)
- Or contact the maintainer directly via email: `github@fabiseitz.de`

Please do not disclose security issues in public issue trackers or forums before an official patch has been published.
