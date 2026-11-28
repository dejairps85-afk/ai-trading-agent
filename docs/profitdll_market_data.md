# ProfitDLL market data integration (planned)

Reference: https://github.com/rlquilez/nelogica-profitdll (documentation version 4.0.0.42).

PAPER_ONLY: no order, account or routing bindings. Do not store credentials or distribute the proprietary DLL. Future Windows adapter must use DLLInitializeMarketLogin only. Keep callbacks short, copy data into a bounded queue, and invalidate data on overflow or degraded connection. Historical requests should be split by day within the documented 30-day window. Preserve native contract, timestamp, trade identifiers and source provenance. Never infer trade aggression from candles. Test adapter with synthetic callbacks on Linux before any licensed Windows integration.

License entitlement and actual market data remain unverified. This document is a design boundary, not an implemented connector. CSV research must remain independently usable.
