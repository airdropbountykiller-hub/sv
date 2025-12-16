"""SV API hub.

This package centralizes all external API integrations:
- Market data providers (CryptoCompare, Yahoo, ...)
- Broker/trading APIs (IG, Bybit, ...)

The goal is to keep generators/engine/portfolio code free of vendor-specific
HTTP/auth/signing details.
"""
