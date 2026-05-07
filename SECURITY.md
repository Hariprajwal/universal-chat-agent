# Security Policy

## Supported Versions

The following versions of Chat Agent are currently being supported with security updates.

| Version | Supported          |
| ------- | ------------------ |
| v1.0.x  | :white_check_mark: |
| < v1.0  | :x:                |

## Reporting a Vulnerability

**Please do not report security vulnerabilities through public GitHub issues.**

If you discover a security vulnerability within this project, please report it privately. You can contact the lead maintainer directly:

- **Contact:** K R HARI PRAJWAL
- **Method:** Please open a private disclosure on GitHub or reach out via the contact information provided on the maintainer's profile.

We will acknowledge your report within 48 hours and provide a timeline for a fix if the vulnerability is confirmed.

## Safe Usage Guidelines

Chat Agent is a powerful automation tool that interacts with your desktop at the pixel level. To ensure your security while using this software:

1. **API Key Safety:** Never share your `.env` file or your OpenRouter API key. This file is included in `.gitignore` by default to prevent accidental leakage.
2. **Untrusted Instructions:** Be cautious when giving the agent instructions that involve sensitive information or financial transactions.
3. **Local Mode:** For maximum privacy, use the **Local Ollama** backend. This ensures that no screen data or text ever leaves your local machine.
4. **Monitoring:** Always monitor the agent while it is executing tasks. You can stop the agent at any time by clicking the **⏹ Stop** button or using the system tray menu.

## Security Features

- **Pixel-Only Interaction:** The agent does not require account-level access to your chat platforms. It only sees what you see on your screen.
- **Failover Logic:** Backend failover is handled silently and securely to ensure continuous operation without exposing internal states.
- **Coordinate Normalization:** Coordinates are normalized to prevent raw screen data from being the primary mode of targeting, adding a layer of abstraction.
