# `FEAT-UI-ADMINISTER_SYSTEM` — Administer System

## Purpose
Manages client preferences, appearance settings, client runtime configuration, and licensing inspection without embedding authorization or business policy in the client.

## Contributed Capabilities
- `ui.administer-system@1`: Presentation port for client administration, appearance, client preferences, and license status.

## Owned Widgets
- `settings` (`app/ui/src/widgets/settings/`): Tabbed/sectioned workstation settings covering Appearance (`FR-UI-SET_APPEARANCE`), Client Configuration (`FR-UI-CONFIGURE_CLIENT`), and Licensing & Entitlements (`FR-UI-MANAGE_LICENSE`).

## Completable Requirements
- `FR-UI-SET_APPEARANCE`: Theme (system, dark, light), density (comfortable, compact), font scale, motion preference (reduced motion), high contrast, and accessible display options.
- `FR-UI-CONFIGURE_CLIENT`: Client configuration (timezone, log level, runtime broker, app display name, autosave interval), secret-safe write-only credential slots with masked fields and no credential leakage, validation, and reset to defaults.
- `FR-UI-MANAGE_LICENSE`: Inspect edition/entitlements and refresh license state without embedding authorization policy.

## Mock-Build Requirements (De-mock Gates)
- `FR-UI-SET_LANGUAGE`: Mock build; completes at Stage 3 Plugins de-mock gate (3.10).
- `FR-UI-MANAGE_UPDATES`: Mock build; completes at Stage 14 Orchestration de-mock gate (14.11).
- `FR-UI-ADMINISTER_CAPABILITIES`: Mock build; completes at Stage 15 Interfaces de-mock gate (15.8).
