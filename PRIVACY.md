# Privacy Policy

**Agent Skill Plugin for Dify**

*Last Updated: January 23, 2026*

## Overview

This Privacy Policy describes how the Agent Skill Plugin ("Plugin") handles user data when used within the Dify platform. We are committed to protecting your privacy and being transparent about our data practices.

## Data Collection

### Data We Do NOT Collect

This Plugin does **not** collect, store, or transmit any of the following personal information:

- Names or personal identifiers
- Email addresses
- Phone numbers
- Physical addresses
- Government-issued identification numbers
- Device identifiers (IMEI, MAC address, device ID)
- IP addresses
- Location data (GPS coordinates, city, region)
- Biometric data
- Financial information
- Health information
- Web browsing history

### Data We Process

The Plugin processes the following data **in real-time** for functionality purposes only:

| Data Type | Purpose | Storage |
|-----------|---------|---------|
| User Queries | Process requests and match appropriate skills | Not stored permanently |
| Conversation Context | Maintain context during a session | Session-only, cleared after use |
| Custom Skill Configurations | Enable user-defined skills | Stored within Dify platform |

## How We Use Data

The Plugin uses data exclusively for the following purposes:

1. **Query Processing**: Analyze user queries to match and activate relevant skills
2. **Response Generation**: Generate appropriate responses using the configured LLM model
3. **Skill Execution**: Execute activated skills to provide specialized assistance
4. **Debug Logging**: When enabled by the user, provide diagnostic information (disabled by default)

## Data Storage

- All data processing occurs within the Dify platform environment
- The Plugin uses Dify's built-in storage (`storage.size: 1048576` bytes) only for caching operational data
- No user data is stored on external servers
- No data is retained after the session ends

## Third-Party Services

### LLM Model Providers

This Plugin integrates with LLM models through the Dify platform. When you use the Plugin:

- Your queries are sent to the configured LLM model provider
- Data handling by the LLM provider is governed by their respective privacy policies
- We recommend reviewing the privacy policy of your chosen LLM provider

### External Tools

If you configure external tools with this Plugin:

- Tool interactions are governed by those tools' respective privacy policies
- The Plugin does not independently share data with third parties

## Data Security

We implement the following security measures:

- All data processing occurs within Dify's secure environment
- No external network calls for data transmission
- No persistent storage of sensitive user data
- Session data is cleared after completion

## User Rights

You have the right to:

- **Access**: View what data is being processed during your session
- **Control**: Enable or disable debug logging
- **Configure**: Choose which skills are enabled
- **Delete**: Session data is automatically cleared after use

## Changes to This Policy

We may update this Privacy Policy from time to time. Any changes will be reflected in the "Last Updated" date at the top of this document.

## Contact

For privacy-related questions or concerns about this Plugin, please:

- Open an issue on our [GitHub repository](https://github.com/xun404/dify-agent-skill-plugin)
- Contact the plugin author: xun404, mx@rmbz.net

## Consent

By using this Plugin, you consent to the data practices described in this Privacy Policy.

---

*This Privacy Policy is provided in accordance with the [Dify Plugin Privacy Policy Guidelines](https://docs.dify.ai/en/develop-plugin/publishing/standards/privacy-protection-guidelines).*
