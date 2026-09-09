# FEAT-UI-DEBUG_CONSOLE

Permission-gated, removable presentation for bounded redacted diagnostics exposed through `interfaces.operate-settings@1`. The widget renders log text inertly, keeps truncation/staleness explicit, clears only its local viewport, and disposes subscriptions/buffers on close. It never deletes retained audit records or requests a raw/unredacted diagnostic mode.
