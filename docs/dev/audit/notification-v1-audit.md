# Notification — Version 1 Code Audit

## 1. Audit Scope

* **Domain:** Notification
* **Package path:** `app/services/notification`
* **Repository:** `haruperi/HaruQuant`
* **Branch audited:** `main`
* **Repository revision:** `a39d26498e14772c571d75fa9a5f0e477a1dd912`
* **Audit date:** 2026-07-13
* **Tests path:** `tests/unit/app/services/notification/test_notification.py`
* **Usage/example paths:**
  * `tests/usage/app/services/notification/tools.py`
  * `tests/usage/app/services/01_utils.py::example_12_notifications`
* **Domain files inspected:**
  * `app/services/notification/__init__.py`
  * `app/services/notification/_common.py`
  * `app/services/notification/base.py`
  * `app/services/notification/config.py`
  * `app/services/notification/desktop.py`
  * `app/services/notification/email.py`
  * `app/services/notification/manager.py`
  * `app/services/notification/sms.py`
  * `app/services/notification/telegram.py`
  * `app/services/notification/templates.py`
  * `app/services/notification/tools.py`
  * `app/services/notification/README.md`
* **Related packages searched or inspected:**
  * `app/services/execution/live/notification_adapter.py`
  * `app/services/execution/live/engine.py`
  * `app/services/execution/live/__init__.py`
  * `app/services/risk/live/engine.py`
  * `app/services/__init__.py`
  * `app/services/utils/standard.py`
  * `app/services/utils/settings`
  * `data/database/sqlite`
  * repository-wide imports, symbol calls, tests, examples, and `pyproject.toml`
* **Excluded:** generated files, caches, virtual environments, historical code removed from `main`, and unrelated domains.
* **Audit limitations:**
  * The GitHub connector exposed file content and repository search but not a complete local checkout or authoritative recursive directory listing. The package boundary was reconstructed from package exports, intra-package imports, README contents, dynamic module-discovery code, and repository-wide code search.
  * Tests were inspected but not executed.
  * Email, Telegram, Twilio, and desktop-provider calls were not made. Operational conclusions about providers are therefore based on static call-path analysis.
  * Runtime configuration values, credentials, provider availability, and production logs were unavailable.
  * External consumers outside this repository cannot be ruled out.
  * GitHub code search cannot conclusively eliminate runtime string imports created outside the repository. Findings affected by this are labelled **Possibly used** or **Medium confidence**.

**Evidence notation:** `path::symbol (lines)` identifies the current `main` implementation at the audited revision.

---

## 2. Executive Summary

The Version 1 notification domain provides:

* canonical notification levels, messages, results, errors, rate limiting, and notifier abstractions;
* Email, Telegram, Twilio SMS, and host-desktop delivery adapters;
* a multi-channel `NotificationManager`;
* a 20-template in-memory notification catalogue;
* configuration loading from INI, environment variables, JSON, application settings, and predefined presets;
* package-root agent-facing wrappers that return standard response envelopes;
* runtime integration with the live execution engine through `LiveTradingNotifier`.

The strongest confirmed production usage is the live execution path:

```text
live execution event
→ LiveTradingNotifier
→ NotificationManager
→ template rendering
→ enabled Email and/or Telegram notifier
→ external recipient
```

Trade-result notifications, safety-violation notifications, and shutdown notifications have confirmed call paths. The risk-integrated live engine inherits this path from `MultiStrategyEngine`. Startup notification code exists but its engine call is commented out. Connection-error and daily-summary adapter methods have no call sites in the available repository.

The most important confirmed problems are:

1. **Authenticated email delivery is defective:** `EmailNotifier.send()` opens SMTP/TLS and calls `send_message()` without logging in, although `test_connection()` does log in.
2. **Default agent send tools can report success without delivering anything:** default levels exclude `INFO`, while custom and trading tool calls default to `INFO`; an empty delivery map is wrapped as a successful tool response.
3. **Tool metadata incorrectly declares that notification tools do not require a network**, even though Email, Telegram, and SMS delivery does.
4. **Two different `NotificationTemplate` classes exist**, but only the one in `templates.py` is used by the manager and tools.
5. **Desktop delivery can report false success:** command exit codes are ignored, `DesktopConfig.enabled` is not enforced by `DesktopNotifier`, and `test_connection()` always returns `True`.
6. **Provider construction can perform network calls:** Telegram and SMS credentials are tested during notifier initialization, so manager creation and service-status inspection can contact external providers.
7. **Naive local timestamps are labelled as UTC** in Email, Telegram, and SMS output.
8. **Most package-root tool wrappers have no confirmed production caller.** They are exercised by unit tests and usage scripts; the supposed export-standardization hook is currently a placeholder.
9. **Coverage is narrow:** available tests cover four wrapper functions and mocked desktop dispatch only.

Audit evidence is strong for the inspected files and static runtime call paths. It is weaker for external deployment behavior, dynamic consumers outside the repository, and actual provider success.

```text
Module folders: 1 | Files: 12 (11 Python) | Public package exports: 25 | Exports with confirmed production callers: 10 (40%) | Workflows found: 4
```

The metric counts unique names in `app/services/notification/__init__.py::__all__`. The detailed behaviour inventory additionally covers 123 top-level public definitions and public methods; enum members, dataclass fields, private helpers, dunder methods, and duplicate re-exports are excluded from that detailed count.

---

## 3. Actual Package Structure

```text
app/services/notification
├── README.md
│   └── Package documentation
├── __init__.py
│   ├── NotificationLevel
│   ├── NotificationMessage
│   ├── NotificationResult
│   ├── NotificationConfig
│   ├── DesktopConfig
│   ├── EmailConfig
│   ├── SMSConfig
│   ├── TelegramConfig
│   ├── NotificationManager
│   ├── NotificationManagerConfig
│   ├── DesktopNotifier
│   ├── EmailNotifier
│   ├── SMSNotifier
│   ├── TelegramNotifier
│   ├── build_notification_manager_config()
│   ├── build_notification_message()
│   ├── create_notification_manager()
│   ├── get_notification_service_status()
│   ├── render_notification_template()
│   ├── send_custom_notification()
│   ├── send_error_notification()
│   ├── send_position_notification()
│   ├── send_system_notification()
│   ├── send_trading_notification()
│   └── validate_notification_config()
├── _common.py
│   └── __getattr__() [dynamic compatibility hook; no public __all__]
├── base.py
│   ├── NotificationLevel
│   ├── NotificationError
│   ├── NotificationMessage
│   ├── NotificationResult
│   ├── RateLimiter
│   │   ├── can_send()
│   │   └── get_wait_time()
│   ├── BaseNotifier
│   │   ├── send()
│   │   ├── test_connection()
│   │   ├── send_message()
│   │   ├── enable()
│   │   ├── disable()
│   │   └── is_enabled()
│   └── NotificationTemplate [duplicate implementation]
│       ├── get_template()
│       ├── render()
│       ├── add_template()
│       └── list_templates()
├── desktop.py
│   ├── DesktopConfig
│   └── DesktopNotifier
│       ├── send()
│       └── test_connection()
├── email.py
│   ├── EmailConfig
│   ├── EmailNotifier
│   │   ├── send()
│   │   ├── test_connection()
│   │   └── send_test_email()
│   └── EmailProviders
│       ├── gmail()
│       ├── outlook()
│       ├── yahoo()
│       └── custom()
├── sms.py
│   ├── SMSConfig
│   └── SMSNotifier
│       ├── send()
│       ├── test_connection()
│       ├── get_account_info()
│       ├── send_test_sms()
│       ├── get_message_status()
│       ├── get_message_history()
│       └── validate_phone_number()
├── telegram.py
│   ├── TelegramConfig
│   └── TelegramNotifier
│       ├── send()
│       ├── test_connection()
│       ├── get_chat_info()
│       ├── send_test_message()
│       ├── send_photo()
│       ├── send_document()
│       └── get_updates()
├── config.py
│   ├── NotificationConfig
│   │   ├── from_ini()
│   │   ├── from_env()
│   │   ├── from_file()
│   │   ├── from_settings()
│   │   ├── save_to_file()
│   │   ├── validate()
│   │   ├── get_email_config()
│   │   ├── get_telegram_config()
│   │   ├── get_sms_config()
│   │   ├── get_desktop_config()
│   │   ├── get_default_levels()
│   │   ├── is_any_service_enabled()
│   │   ├── get_enabled_services()
│   │   └── print_configuration()
│   └── NotificationPresets
│       ├── development()
│       ├── production()
│       ├── gmail_setup()
│       ├── telegram_setup()
│       └── twilio_setup()
├── templates.py
│   └── NotificationTemplate
│       ├── get_template()
│       ├── render()
│       ├── add_template()
│       ├── update_template()
│       ├── remove_template()
│       ├── list_templates()
│       ├── get_template_variables()
│       ├── validate_template()
│       ├── preview_template()
│       ├── export_templates()
│       ├── import_templates()
│       └── get_template_info()
├── manager.py
│   ├── NotificationManagerConfig
│   └── NotificationManager
│       ├── send_notification()
│       ├── send_trading_alert()
│       ├── send_system_alert()
│       ├── send_position_update()
│       ├── send_error_alert()
│       ├── send_custom_message()
│       ├── test_all_services()
│       ├── enable_service()
│       ├── disable_service()
│       ├── get_service_status()
│       ├── get_statistics()
│       ├── reset_statistics()
│       ├── add_template()
│       ├── list_templates()
│       ├── list_services()
│       └── get_notifier()
└── tools.py
    ├── TOOL_VERSION
    ├── TOOL_CATEGORY
    ├── TOOL_RISK_LEVEL
    ├── REQUIRES_APPROVAL
    ├── READ_ONLY
    ├── WRITES_FILE
    ├── MODIFIES_DATABASE
    ├── PLACES_TRADE
    ├── REQUIRES_NETWORK
    ├── build_notification_message()
    ├── render_notification_template()
    ├── validate_notification_config()
    ├── build_notification_manager_config()
    ├── create_notification_manager()
    ├── get_notification_service_status()
    ├── send_custom_notification()
    ├── send_trading_notification()
    ├── send_system_notification()
    ├── send_position_notification()
    └── send_error_notification()
```

No child module folders were identified under `app/services/notification`.

---

## 4. Module and File Inventory

Files are arranged in approximate dependency order.

| Module | File | Responsibility | Key exports | Dependencies | Usage status | Value status |
|---|---|---|---|---|---|---|
| notification | `base.py` | Core levels, message/result models, exception, rate limiting, notifier contract, and a small duplicate template implementation | `NotificationLevel`, `NotificationMessage`, `NotificationResult`, `RateLimiter`, `BaseNotifier`, duplicate `NotificationTemplate` | **Stdlib:** `abc`, `dataclasses`, `datetime`, `enum`, `threading`, `time`, `typing`<br>**Third-party:** none<br>**Local:** `app.services.utils.logger.logger` | **Used**, except duplicate template is **Possibly used/No caller found** | **Supporting**; duplicate template is **Questionable** |
| notification | `desktop.py` | Native host desktop notifications via OS commands | `DesktopConfig`, `DesktopNotifier` | **Stdlib:** `dataclasses`, `subprocess`, `sys`, `time`<br>**Third-party:** none<br>**Local:** base models/classes | **Test-only** in confirmed repository call paths; reachable through manager configuration | **Useful**, but operational evidence is weak |
| notification | `email.py` | SMTP email formatting, connection testing, and delivery | `EmailConfig`, `EmailNotifier`, `EmailProviders` | **Stdlib:** `email.mime`, `smtplib`, `ssl`, `dataclasses`<br>**Third-party:** none<br>**Local:** base models/classes | `EmailNotifier` **Used** by live adapter path; `EmailProviders` has no caller | `EmailNotifier`: **Essential**, currently defective; presets: **Questionable** |
| notification | `sms.py` | Twilio REST SMS delivery and account/message lookup helpers | `SMSConfig`, `SMSNotifier` | **Stdlib:** `dataclasses`, `typing`<br>**Third-party:** `requests`<br>**Local:** base models/classes | **Possibly used** through configurable manager; no confirmed production SMS configuration | **Useful** |
| notification | `telegram.py` | Telegram Bot API text/media delivery and lookup helpers | `TelegramConfig`, `TelegramNotifier` | **Stdlib:** `dataclasses`, `typing`<br>**Third-party:** `requests`<br>**Local:** base models/classes | **Used** by database-configured live adapter path | **Essential** |
| notification | `config.py` | Loads, validates, serializes, and transforms notification settings | `NotificationConfig`, `NotificationPresets` | **Stdlib:** `configparser`, `dataclasses`, `json`, `os`, `pathlib`<br>**Third-party:** none<br>**Local:** `logger`, base level, channel config classes, lazy `get_settings()` | `NotificationConfig` **Used**; presets have no confirmed caller | **Essential**; presets **Questionable** |
| notification | `templates.py` | In-memory catalogue of 20 templates and template administration | `NotificationTemplate` | **Stdlib:** `datetime`, `re`, `typing`<br>**Third-party:** none<br>**Local:** `logger`, `NotificationError`, `NotificationMessage` | Core render/list/add **Used** by manager/tools; most administrative methods have no caller | **Supporting** |
| notification | `manager.py` | Initializes channels, filters alerts, renders standard alert types, dispatches synchronously, and records in-memory statistics | `NotificationManagerConfig`, `NotificationManager` | **Stdlib:** `dataclasses`, `threading`, `typing`<br>**Third-party:** none directly<br>**Local:** logger, base classes, all channel adapters, `templates.NotificationTemplate` | **Used** by live execution adapter | **Essential** |
| notification | `tools.py` | Package-root, standard-envelope wrappers around message/config/template/manager operations | 11 wrapper functions and 9 metadata constants | **Stdlib:** `collections.abc`, `time`, `typing`<br>**Third-party:** none directly<br>**Local:** logger, standard-response helpers, base/config/manager/templates | **Test-only** in confirmed repository call paths | **Questionable** for current production; useful as a boundary if externally consumed |
| notification | `__init__.py` | Declares package-root public exports | 25 names in `__all__` | **Stdlib:** `__future__`<br>**Third-party:** none<br>**Local:** all package modules, `standardize_domain_exports` | **Used** by live adapter, tests, and examples | **Essential** |
| notification | `_common.py` | Lazy compatibility resolver over lower-level notification modules | no public `__all__`; dynamic `__getattr__` | **Stdlib:** `typing`<br>**Third-party:** none<br>**Local:** `app.services.resolve_service_attr`, `service_modules` | **Possibly used**; no repository caller found | **Questionable** |
| notification | `README.md` | Documents package intent, channels, and package-root tools | n/a | n/a | Documentation only | **Supporting**, but partially stale |

**Multi-responsibility findings:**

* `base.py` combines core contracts with a second template system.
* `config.py` combines five loading sources, validation, conversion to provider configs, persistence, console output, and presets.
* `tools.py` combines pure construction/inspection operations with externally mutating delivery operations under one metadata profile.

---

## 5. Public Behaviour Inventory

### `notification/__init__.py`

**File responsibility:** Exposes the official package-root API.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| 14 model/config/manager/notifier exports | Re-exports | Makes core domain types available from `app.services.notification` | Import → referenced objects | Import-time module loading | Import errors from dependencies | Live adapter imports `NotificationLevel`, `NotificationManager`, `NotificationManagerConfig`; tests import desktop/core types | `test_notification.py` | **Used** | **Essential** |
| 11 tool exports | Re-exports | Makes agent-facing wrappers available at package root | Import → callables | Import-time module loading | Import errors | Tests and usage scripts; no production caller found | Unit and usage tests | **Test-only** | **Questionable** |
| `standardize_domain_exports(...)` call | Registration/normalization hook | Intended to standardize exported tools | Namespace and `__all__` → `None` | Logging only in current implementation | none observed | Executed on import | indirectly | **Used**, but function is a placeholder | **No demonstrated functional value** |

**Evidence:** `app/services/notification/__init__.py:12-79`; `app/services/utils/standard.py:1322-1328`.

---

### `notification/_common.py`

**File responsibility:** Dynamically resolves attributes from all notification submodules.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `__getattr__(name)` | Special module hook | Searches discovered notification modules and returns a matching symbol | name → object | Dynamically imports package modules | `AttributeError`, dependency import exceptions | No direct repository caller found | none | **Possibly used** | **Questionable** |

The hook is not in `__all__`. Repository search found only its own definition. Dynamic use cannot be fully excluded.

**Evidence:** `app/services/notification/_common.py:16-33`; `app/services/__init__.py:35-66`.

---

### `notification/base.py`

**File responsibility:** Defines common contracts and infrastructure. It also contains a second, smaller template implementation unrelated to the one imported by the manager.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `NotificationLevel` | Enum | Defines `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL` | enum value → member | None | `ValueError` on invalid construction | Config, manager, tools, adapter, providers | indirectly | **Used** | **Essential** |
| `NotificationError` | Exception | Domain-specific error | message → exception | None | n/a | Message validation, templates, provider constructors | not directly | **Used** | **Supporting** |
| `NotificationMessage` | Dataclass | Canonical message with title, body, level, timestamp, metadata, recipients, template name | fields → object | Local normalization of `level` | `NotificationError`; `ValueError` for invalid level | Manager, templates, providers, tools | desktop tests; tool tests indirectly | **Used** | **Essential** |
| `NotificationResult` | Dataclass | Canonical per-service delivery outcome | fields → object | None | none | All provider adapters, manager, tool serializers | indirectly | **Used** | **Essential** |
| `RateLimiter.can_send()` | Method | Prunes expired timestamps, records an allowed request, and returns permission | none → `bool` | **Local state mutation** | none | `BaseNotifier._check_rate_limit()` | none | **Used internally** | **Supporting** |
| `RateLimiter.get_wait_time()` | Method | Computes wait before oldest request expires | none → seconds | Read-only under lock | none | `BaseNotifier._check_rate_limit()` | none | **Used internally** | **Supporting** |
| `BaseNotifier.send()` | Abstract method | Provider-specific single-attempt send contract | message → result | Provider-defined | provider-defined | Implemented by all four adapters | desktop implementation tested | **Used** | **Supporting** |
| `BaseNotifier.test_connection()` | Abstract method | Provider connection diagnostic contract | none → `bool` | Provider-defined | provider-defined | Manager diagnostics | no manager test | **Used** | **Supporting** |
| `BaseNotifier.send_message()` | Method | Enforces enabled state, rate limiting, and retries | message → result | **Local state mutation**, then provider side effect | catches provider exceptions in retry layer | `NotificationManager.send_notification()`; provider test helpers | indirectly | **Used** | **Essential** |
| `BaseNotifier.enable()` / `disable()` / `is_enabled()` | Methods | Mutate or inspect notifier enabled state | none → `None`/`bool` | **Local state mutation** for enable/disable | none | Manager service-control and dispatch | none | **Used internally** | **Supporting** |
| `base.NotificationTemplate` | Class | Four-template rendering implementation | constructor → object | Local state | `NotificationError` | No import or instantiation found; manager imports `templates.NotificationTemplate` instead | none | **Possibly used** via dynamic resolver only | **No demonstrated value** |
| `base.NotificationTemplate.get_template()` / `render()` / `add_template()` / `list_templates()` | Methods | Read, render, mutate, and list the duplicate four-template catalogue | names/variables → template/message/list | None or **Local state mutation** | `NotificationError` | No confirmed caller | none | **Possibly used** | **No demonstrated value** |

**Side-effect labels:** rate limiting and enablement are local state mutation; actual provider calls occur in subclasses.

**Evidence:** `app/services/notification/base.py:28-242`, duplicate template at `base.py:245-341`; manager import at `manager.py:30`.

---

### `notification/desktop.py`

**File responsibility:** Sends native desktop alerts using platform commands.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `DesktopConfig` | Dataclass | Stores `enabled` flag | `enabled` → object | None | none | Config transformer, manager | desktop tests | **Test-only / reachable** | **Useful** |
| `DesktopNotifier.send()` | Method | Runs PowerShell, AppleScript, or `notify-send` | message → result | **External process call** | converts timeout/other exceptions to failed result | Manager; direct unit tests | Windows/macOS/Linux mocked tests | **Test-only / reachable** | **Useful**, but unreliable status |
| `DesktopNotifier.test_connection()` | Method | Returns `True` unconditionally | none → `True` | None | none | Manager diagnostics | none | **Reachable** | **Questionable** |

`DesktopConfig.enabled` is stored but not checked in `DesktopNotifier.send()`. `subprocess.run(..., check=False)` results are not inspected, so a non-zero command exit still produces `success=True`.

**Evidence:** `app/services/notification/desktop.py:24-141`; `tests/unit/app/services/notification/test_notification.py:46-102`.

---

### `notification/email.py`

**File responsibility:** Formats and sends SMTP email notifications.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `EmailConfig` | Dataclass | Stores SMTP credentials, TLS/SSL settings, sender, and recipients | fields → object | Local defaulting of `from_email` | none | `NotificationConfig.get_email_config()`; manager | none | **Used** | **Supporting** |
| `EmailNotifier` constructor | Class construction | Validates required SMTP fields | config/rate limiter → notifier | None | `NotificationError` | Manager initialization | none | **Used** | **Essential** |
| `EmailNotifier.send()` | Method | Builds MIME message and sends through SMTP connection | message → result | **External API/network call** | catches all and returns failed result | `BaseNotifier.send_message()` | none | **Used** | **Essential**, currently defective |
| `EmailNotifier.test_connection()` | Method | Opens connection and authenticates | none → `bool` | **External API/network call** | catches exceptions | Manager/adapter diagnostics | none | **Used** | **Useful** |
| `EmailNotifier.send_test_email()` | Method | Sends a predefined test message | recipient → result | **External API/network call** | result-based failure | No caller found | none | **Unused within repository** | **Questionable** |
| `EmailProviders.gmail()` / `outlook()` / `yahoo()` / `custom()` | Static methods | Build provider-specific `EmailConfig` objects | credentials → config | None | none | No caller found | none | **Unused within repository** | **Questionable** |

**Confirmed defect:** `send()` obtains `_get_connection()` and invokes `server.send_message(email_msg)` without calling `server.login(...)`. The separate `test_connection()` method does call `login()`. Authenticated SMTP providers can therefore pass diagnostics but fail actual delivery.

**Evidence:** `app/services/notification/email.py:29-105`, connection and diagnostics at `email.py:198-236`, presets at `email.py:239-301`.

---

### `notification/sms.py`

**File responsibility:** Sends and inspects Twilio SMS messages through direct REST requests.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `SMSConfig` | Dataclass | Stores Twilio credentials, sender, recipients, and callbacks | fields → object | None | none | Config transformer, manager | none | **Possibly used** | **Supporting** |
| `SMSNotifier` constructor | Class construction | Validates fields and immediately tests Twilio credentials | config/rate limiter → notifier | **External API call** | `NotificationError` | Manager initialization when configured | none | **Possibly used** | **Useful** |
| `SMSNotifier.send()` | Method | Formats, truncates, and sends to each recipient | message → result | **External API calls** | catches exceptions into result | Manager dispatch | none | **Possibly used** | **Useful** |
| `SMSNotifier.test_connection()` | Method | Re-tests account credentials | none → `bool` | **External API call** | catches exceptions | Manager diagnostics | none | **Possibly used** | **Supporting** |
| `SMSNotifier.get_account_info()` | Method | Fetches Twilio account JSON | none → dict/`None` | **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |
| `SMSNotifier.send_test_sms()` | Method | Sends predefined test SMS | phone → result | **External API call** | result-based failure | No caller found | none | **Unused within repository** | **Questionable** |
| `SMSNotifier.get_message_status()` | Method | Fetches one message status | SID → dict/`None` | **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |
| `SMSNotifier.get_message_history()` | Method | Fetches recent messages | limit → list | **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |
| `SMSNotifier.validate_phone_number()` | Method | Calls Twilio Lookup API | phone → dict/`None` | **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |

A multi-recipient attempt is considered successful when at least one recipient is queued. Failed recipient details are logged but not represented in the returned `NotificationResult`.

**Evidence:** `app/services/notification/sms.py:27-321`.

---

### `notification/telegram.py`

**File responsibility:** Sends Telegram messages and media and provides Bot API lookup helpers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TelegramConfig` | Dataclass | Stores token, chat IDs, formatting, and delivery flags | fields → object | Invalid parse mode is locally replaced with `HTML` | none | Config transformer, live adapter, manager | none | **Used** | **Supporting** |
| `TelegramNotifier` constructor | Class construction | Validates token and immediately calls `getMe` | config/rate limiter → notifier | **External API call** | `NotificationError` | Manager initialization | none | **Used** | **Essential** |
| `TelegramNotifier.send()` | Method | Formats and sends text to each recipient | message → result | **External API calls** | catches exceptions into result | Manager dispatch | none | **Used** | **Essential** |
| `TelegramNotifier.test_connection()` | Method | Calls token test again | none → `bool` | **External API call** | catches exceptions | Manager diagnostics | none | **Used** | **Supporting** |
| `TelegramNotifier.get_chat_info()` | Method | Calls `getChat` | chat ID → dict/`None` | **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |
| `TelegramNotifier.send_test_message()` | Method | Sends predefined text | chat ID → result | **External API call** | result-based failure | No caller found | none | **Unused within repository** | **Questionable** |
| `TelegramNotifier.send_photo()` | Method | Reads a file and calls `sendPhoto` | chat ID/path/caption → result | **Read-only** file access + **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |
| `TelegramNotifier.send_document()` | Method | Reads a file and calls `sendDocument` | chat ID/path/caption → result | **Read-only** file access + **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |
| `TelegramNotifier.get_updates()` | Method | Calls `getUpdates` | offset/limit → list | **External API call** | catches exceptions | No caller found | none | **Unused within repository** | **Questionable** |

Media methods bypass `BaseNotifier.send_message()`, so they do not use its rate limiter or retry behavior.

**Evidence:** `app/services/notification/telegram.py:27-369`.

---

### `notification/config.py`

**File responsibility:** Represents notification settings and converts them into channel configurations.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `NotificationConfig` | Dataclass | Stores all channel/general settings | fields → object | Local state | none | Live adapter, tools | indirectly | **Used** | **Essential** |
| `from_ini()` | Class method | Loads INI sections | path → config | **Read-only** file access; logging | catches broad exceptions and returns defaults | No production caller found | none | **Unused within repository** | **Questionable** |
| `from_env()` | Class method | Loads environment variables | environment → config | **Read-only** process environment | may raise on invalid integer port | No production caller found | none | **Unused within repository** | **Questionable** |
| `from_file()` | Class method | Loads JSON configuration | path → config | **Read-only** file access; logging | catches errors and returns defaults | No production caller found | none | **Unused within repository** | **Questionable** |
| `from_settings()` | Class method | Maps application settings to notification fields | optional settings → config | Reads global settings when omitted | settings/import errors may propagate | Tool manager construction | indirectly | **Test-only confirmed** | **Useful** |
| `save_to_file()` | Method | Creates parent directory and writes JSON | path → `None` | **Persistence write** | catches and logs all errors | No caller found | none | **Unused within repository** | **Questionable** |
| `validate()` | Method | Aggregates channel/general validation messages | none → list of strings | None | none | Tool wrapper | unit test indirectly | **Test-only confirmed** | **Useful** |
| `get_email_config()` / `get_telegram_config()` / `get_sms_config()` / `get_desktop_config()` | Methods | Convert enabled settings into channel config objects | none → config/`None` | None | constructor/type errors | Live adapter, tools, manager config construction | indirectly | **Used** | **Essential/Supporting** |
| `get_default_levels()` | Method | Converts strings into enum members | none → list | None | `ValueError` for invalid level | Tool manager construction | indirectly | **Test-only confirmed** | **Supporting** |
| `is_any_service_enabled()` / `get_enabled_services()` | Methods | Inspect enabled channel flags | none → bool/list | None | none | No caller found | none | **Unused within repository** | **Questionable** |
| `print_configuration()` | Method | Prints settings, optionally including credentials | flag → `None` | Console output; possible secret disclosure when requested | none | No caller found | none | **Unused within repository** | **Questionable** |
| `NotificationPresets.development()` / `production()` | Static methods | Build nominal environment presets | none → config | None | none | No caller found | none | **Unused within repository** | **Questionable** |
| `NotificationPresets.gmail_setup()` / `telegram_setup()` / `twilio_setup()` | Static methods | Build channel-specific config presets | credentials → config | None | none | No caller found | none | **Unused within repository** | **Questionable** |

`desktop_enabled` defaults to `True`; a settings-derived manager therefore includes desktop delivery unless explicitly disabled. `production()` claims “all services enabled” in its docstring but only retains default channel flags and changes general levels/enablement.

**Evidence:** `app/services/notification/config.py:28-365`, `config.py:367-594`, presets at `config.py:597-653`.

---

### `notification/templates.py`

**File responsibility:** Maintains the active in-memory template catalogue used by the manager and tool wrappers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `NotificationTemplate` | Class | Owns 20 predefined template mappings | constructor → object | Local state allocation | none | Manager and tools | render wrapper test | **Used** | **Supporting** |
| `get_template()` | Method | Returns named template | name → mapping | None | `NotificationError` | `render()`, preview/introspection methods | indirectly | **Used internally** | **Supporting** |
| `render()` | Method | Formats title/body and returns canonical message | name/variables → message | None | `NotificationError` for missing template/variable | Manager and tool wrapper | unit test | **Used** | **Essential** |
| `add_template()` | Method | Adds or replaces a template | name/title/body → `None` | **Local state mutation** | none | Manager pass-through only; no external caller found | none | **Possibly used** | **Useful** |
| `update_template()` / `remove_template()` | Methods | Modify or delete non-essential templates | name/templates → `None` | **Local state mutation** | `NotificationError` | No caller found | none | **Unused within repository** | **Questionable** |
| `list_templates()` | Method | Lists template names | none → list | None | none | Manager pass-through | none | **Reachable** | **Useful** |
| `get_template_variables()` / `validate_template()` | Methods | Extract and validate required placeholders | name/kwargs → list | None | `NotificationError` | Internal introspection only; no external caller found | none | **Unused within repository** | **Questionable** |
| `preview_template()` | Method | Produces formatted preview text | name/kwargs → string | None | `NotificationError` | No caller found | none | **Unused within repository** | **Questionable** |
| `export_templates()` / `import_templates()` | Methods | Copy or merge template dictionaries | none/mapping → dict/`None` | import mutates local state | none for export; invalid entries are logged/skipped | No caller found | none | **Unused within repository** | **Questionable** |
| `get_template_info()` | Method | Returns template text, variables, and lengths | name → mapping | None | `NotificationError` | No caller found | none | **Unused within repository** | **Questionable** |

Only `trading_alert`, `system_alert`, `position_update`, and `error_alert` are selected by manager convenience methods. The remaining templates are reachable through generic rendering but have no confirmed runtime caller.

**Evidence:** `app/services/notification/templates.py:20-484`.

---

### `notification/manager.py`

**File responsibility:** Coordinates channel creation, template rendering, delivery, service control, and statistics.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `NotificationManagerConfig` | Dataclass | Holds optional channel configs, default levels, and global enable flag | fields → object | Populates default levels | none | Live adapter and tools | indirectly | **Used** | **Essential** |
| `NotificationManager` constructor | Class construction | Creates template catalogue, configured notifiers, and stats | config → manager | May perform **External API calls** through Telegram/SMS constructors | provider constructor errors are caught per channel | Live adapter and tools | indirectly | **Used** | **Essential** |
| `send_notification()` | Method | Filters services/levels, synchronously sends through channels, and updates stats | message/services → result map | **External API/process calls** + **Local state mutation** | catches per-service exceptions; pre-dispatch errors may propagate | All manager convenience send methods | indirectly | **Used** | **Essential** |
| `send_trading_alert()` | Method | Renders trading template and dispatches | trade fields/services → result map | Provider side effects | template errors | Live adapter and tool implementation | usage examples indirectly | **Used** | **Essential** |
| `send_system_alert()` | Method | Renders system template, applies level, and dispatches | alert fields/services → result map | Provider side effects | invalid enum/template errors | Live adapter and tool implementation | usage examples indirectly | **Used** | **Essential** |
| `send_position_update()` | Method | Renders position update and dispatches | position fields/services → result map | Provider side effects | template errors | Tool implementation only | usage example | **Test-only confirmed** | **Useful** |
| `send_error_alert()` | Method | Renders error template, truncates stack trace, and dispatches | error fields/services → result map | Provider side effects | template errors | Live adapter and tool implementation | usage example | **Used** | **Essential** |
| `send_custom_message()` | Method | Creates arbitrary canonical message and dispatches | title/body/etc. → result map | Provider side effects | invalid level/message errors | Live adapter daily-summary method; tool implementation | usage example | **Used indirectly**, daily-summary caller disconnected | **Useful** |
| `test_all_services()` | Method | Calls each notifier diagnostic | none → service/bool map | **External API calls** | catches per-service exceptions | Live adapter `test_connection()` | none | **Used** | **Useful** |
| `enable_service()` / `disable_service()` | Methods | Toggle one notifier | service name → `None` | **Local state mutation** | none; missing service only logged | No caller found | none | **Unused within repository** | **Questionable** |
| `get_service_status()` | Method | Returns enabled/name/rate-limit metadata | none → mapping | Read-only | none | Tool wrapper | unit test indirectly | **Test-only confirmed** | **Useful** |
| `get_statistics()` / `reset_statistics()` | Methods | Read or clear in-memory delivery counters | none → dict/`None` | reset is **Local state mutation** | none | No caller found | none | **Unused within repository** | **Questionable** |
| `add_template()` / `list_templates()` | Methods | Pass through to template catalogue | template data/none → `None`/list | add mutates local state | template errors | No caller found | none | **Unused within repository** | **Questionable** |
| `list_services()` / `get_notifier()` | Methods | Inspect initialized channel registry | none/name → list/notifier | Read-only | none | No caller found | none | **Unused within repository** | **Questionable** |

The manager sends sequentially on the caller thread. In the live engine, notification provider latency therefore occurs in the signal/safety/shutdown call path.

**Evidence:** `app/services/notification/manager.py:33-508`.

---

### `notification/tools.py`

**File responsibility:** Exposes standard-response wrappers for agent or service callers.

| Symbol | Type | Responsibility | Inputs → Return | Side effects | Raises | Callers | Tests | Usage status | Value status |
|---|---|---|---|---|---|---|---|---|---|
| `TOOL_VERSION`, `TOOL_CATEGORY`, `TOOL_RISK_LEVEL` | Constants | Standard response metadata | n/a | None | none | `_standard_tool_response()` | indirectly | **Used internally** | **Supporting** |
| `REQUIRES_APPROVAL`, `READ_ONLY`, `WRITES_FILE`, `MODIFIES_DATABASE`, `PLACES_TRADE`, `REQUIRES_NETWORK` | Constants | Declared capability/risk metadata | n/a | None | none | Standard response builder, except `REQUIRES_APPROVAL` is not copied into `ToolStandardSpec` | indirectly | **Used internally/partially unused** | **Supporting**, but inaccurate/incomplete |
| `build_notification_message()` | Function | Validates and serializes a canonical message without sending | title/body/etc. → standard dict | None except logging | catches errors into envelope | Unit test and usage scripts | yes | **Test-only** | **Useful** |
| `render_notification_template()` | Function | Renders and serializes a named template | name/variables → standard dict | None except logging | catches errors into envelope | Unit test and usage scripts | yes | **Test-only** | **Useful** |
| `validate_notification_config()` | Function | Builds optional config and returns validation strings | optional mapping → standard dict | May read application settings when mapping is empty/falsy | catches errors into envelope | Unit test and usage scripts | yes | **Test-only** | **Useful** |
| `build_notification_manager_config()` | Function | Converts service config into serialized manager config | optional mapping → standard dict | May read settings | catches errors into envelope | Usage scripts | usage only | **Test-only** | **Useful** |
| `create_notification_manager()` | Function | Verifies manager construction and returns `"created"` status, not the manager | optional mapping → standard dict | Can perform **External API calls** during channel construction | catches errors into envelope | Usage scripts | usage only | **Test-only** | **Questionable** |
| `get_notification_service_status()` | Function | Creates/uses a manager and returns status | optional manager → standard dict | Can perform **External API calls** during default manager construction | catches errors into envelope | Unit test and usage scripts | yes | **Test-only** | **Useful**, with hidden side effects |
| `send_custom_notification()` | Function | Sends an arbitrary notification | message fields/manager/services → standard dict | Provider side effects | catches errors into envelope | Usage scripts and README only | usage only | **Test-only** | **Questionable** |
| `send_trading_notification()` | Function | Sends a trading alert | trade fields/manager/services → standard dict | Provider side effects | catches errors into envelope | Usage scripts and README only | usage only | **Test-only** | **Questionable** |
| `send_system_notification()` | Function | Sends a system alert | alert fields/manager/services → standard dict | Provider side effects | catches errors into envelope | Usage scripts only | usage only | **Test-only** | **Questionable** |
| `send_position_notification()` | Function | Sends a position update | position fields/manager/services → standard dict | Provider side effects | catches errors into envelope | Usage scripts only | usage only | **Test-only** | **Questionable** |
| `send_error_notification()` | Function | Sends an error alert | error fields/manager/services → standard dict | Provider side effects | catches errors into envelope | Usage scripts only | usage only | **Test-only** | **Questionable** |

**Metadata mismatch:** `REQUIRES_NETWORK = False`, although the send functions can perform SMTP, Telegram, or Twilio calls. `create_notification_manager()` and `get_notification_service_status()` can also contact Telegram or Twilio because those notifier constructors validate credentials.

**Default no-delivery behavior:** default levels are `WARNING`, `ERROR`, and `CRITICAL`. `send_custom_notification()` defaults to `INFO`; the trading template also remains `INFO`. With default configuration, the manager returns `{}` after level filtering, and the wrapper still returns a top-level `"success"` status.

**Evidence:** constants at `app/services/notification/tools.py:38-46`; implementation and wrappers at `tools.py:49-985`; default levels at `config.py:65-69`; manager filtering at `manager.py:160-178`.

---

## 6. Actual Workflows

### `V1-WF-NOTIFICATION-001` — Live Execution Alert Delivery

* **Scope:** `Cross-domain`
* **Trigger:** Live execution initialization, a rejected safety/portfolio check, a completed/failed trade execution, or live engine shutdown.
* **Input boundary:**
  * Runtime notification configuration from execution config or user-specific database credentials.
  * Signal, execution result, safety reason, or shutdown event from the execution domain.
* **Functions and methods used:**
  * `MultiStrategyEngine.initialize()`
  * `LiveTradingNotifier.__init__()` or `LiveTradingNotifier.from_database()`
  * `NotificationConfig.get_email_config()` / `get_telegram_config()`
  * `NotificationManagerConfig(...)`
  * `NotificationManager(...)`
  * `LiveTradingNotifier.notify_signal()` / `notify_safety_violation()` / `notify_shutdown()`
  * `NotificationManager.send_trading_alert()` / `send_error_alert()` / `send_system_alert()`
  * `NotificationTemplate.render()`
  * `NotificationManager.send_notification()`
  * `BaseNotifier.send_message()`
  * `EmailNotifier.send()` and/or `TelegramNotifier.send()`
* **Files involved:**
  * `app/services/execution/live/engine.py`
  * `app/services/execution/live/notification_adapter.py`
  * `app/services/notification/config.py`
  * `app/services/notification/manager.py`
  * `app/services/notification/templates.py`
  * `app/services/notification/base.py`
  * `app/services/notification/email.py`
  * `app/services/notification/telegram.py`
* **External dependencies:** SQLite credential store through the execution adapter; SMTP server; Telegram Bot API; logger.
* **Output boundary:** A delivery attempt to configured external recipients. Delivery results remain inside the adapter call and are not acted on by the engine.
* **Failure behaviour:**
  * Missing database credentials create a disabled adapter.
  * Provider-constructor failure is logged and removes that channel from the manager.
  * Delivery failure is returned as `NotificationResult`, but the live adapter does not return or escalate it to the engine.
  * Email delivery is likely to fail for authenticated SMTP because `send()` does not log in.
  * Telegram/SMS construction can block/fail on credential-test network calls.
* **Operational status:** `Partial`
* **Evidence:**
  * Adapter construction and database mapping: `app/services/execution/live/notification_adapter.py:23-328`
  * Engine construction: `app/services/execution/live/engine.py:25-40`, `engine.py:330-354`
  * Safety and trade calls: `engine.py:754-829`
  * Shutdown call: `engine.py:860-865`
  * Risk live engine inherits `MultiStrategyEngine`: `app/services/risk/live/engine.py:17-47`, `risk/live/engine.py:76-89`

```text
execution config or database credentials
→ LiveTradingNotifier
→ NotificationConfig
→ NotificationManagerConfig
→ NotificationManager
→ live signal/safety/shutdown event
→ manager alert method
→ NotificationTemplate.render()
→ NotificationManager.send_notification()
→ EmailNotifier and/or TelegramNotifier
→ external recipient
```

---

### `V1-WF-NOTIFICATION-002` — Internal Multi-Channel Dispatch, Retry, and Statistics

* **Scope:** `Internal`
* **Trigger:** A caller invokes a `NotificationManager.send_*` method.
* **Input boundary:** Canonical message or alert-specific fields plus optional target service names.
* **Functions and methods used:**
  * `NotificationManager.send_*`
  * `NotificationTemplate.render()`
  * `NotificationManager.send_notification()`
  * `BaseNotifier.is_enabled()`
  * `BaseNotifier.send_message()`
  * `RateLimiter.can_send()` / `get_wait_time()`
  * channel `send()`
  * `NotificationManager._update_stats()`
* **Files involved:** `manager.py`, `templates.py`, `base.py`, and the selected provider file.
* **External dependencies:** Provider-specific network or OS facility.
* **Output boundary:** Mapping of channel name to `NotificationResult`; in-memory delivery statistics.
* **Failure behaviour:**
  * Globally disabled manager, filtered level, or no valid services returns an empty mapping.
  * Per-service exceptions are converted to failed results.
  * Retries use exponential backoff and consume rate-limit entries on each attempt.
  * Dispatch is sequential.
* **Operational status:** `Partial`
* **Evidence:** `app/services/notification/manager.py:147-208`; `base.py:79-228`.

```text
manager send method
→ render/build NotificationMessage
→ global/service/level filters
→ BaseNotifier.send_message()
→ rate-limit check
→ provider send()
→ retry if failed
→ update in-memory statistics
→ per-service results
```

---

### `V1-WF-NOTIFICATION-003` — Message, Template, and Configuration Tool Inspection

* **Scope:** `Internal`
* **Trigger:** Unit test, usage script, or an unconfirmed external agent invokes a package-root inspection/build tool.
* **Input boundary:** Plain Python-compatible fields or configuration mapping.
* **Functions and methods used:**
  * `build_notification_message()`
  * `render_notification_template()`
  * `validate_notification_config()`
  * `build_notification_manager_config()`
  * `get_notification_service_status()`
  * internal serialization and standard-response helpers
* **Files involved:** `__init__.py`, `tools.py`, `base.py`, `config.py`, `templates.py`, `manager.py`, `app/services/utils/standard.py`.
* **External dependencies:** Application settings; service-status manager construction may indirectly call providers.
* **Output boundary:** Standard response envelope.
* **Failure behaviour:** Validation and execution exceptions are converted to error envelopes.
* **Operational status:** `Working` for message/template serialization; `Partial` for manager/status operations because manager creation can contact providers.
* **Evidence:**
  * Tool implementation: `app/services/notification/tools.py:49-750`
  * Unit tests: `tests/unit/app/services/notification/test_notification.py:3-43`
  * Usage example: `tests/usage/app/services/notification/tools.py:16-112`
  * Standardization hook is a placeholder: `app/services/utils/standard.py:1322-1328`

```text
test/example/unconfirmed agent caller
→ package-root tool
→ validate input
→ build/render/inspect object
→ serialize result
→ standard response envelope
```

---

### `V1-WF-NOTIFICATION-004` — Package-Root Tool Delivery

* **Scope:** `Cross-domain`
* **Trigger:** Usage script or unconfirmed external agent invokes a `send_*_notification()` wrapper.
* **Input boundary:** Alert-specific plain values, optional manager, and optional channel filter.
* **Functions and methods used:**
  * `send_custom_notification()`
  * `send_trading_notification()`
  * `send_system_notification()`
  * `send_position_notification()`
  * `send_error_notification()`
  * matching manager method and provider path
* **Files involved:** `__init__.py`, `tools.py`, `manager.py`, `templates.py`, `base.py`, channel modules.
* **External dependencies:** Application settings and selected providers.
* **Output boundary:** Standard response containing serialized per-service results.
* **Failure behaviour:**
  * Errors become standard error envelopes.
  * Filtered/no-channel delivery returns an empty result map but top-level status remains successful.
  * Default `INFO` custom/trading messages are filtered by default levels.
* **Operational status:** `Unverified` as a production workflow; `Partial` in usage examples.
* **Evidence:**
  * Wrappers: `app/services/notification/tools.py:746-985`
  * Repository callers: README and usage scripts only.
  * Usage scripts: `tests/usage/app/services/notification/tools.py:62-93`; `tests/usage/app/services/01_utils.py::example_12_notifications`
  * No functioning runtime registration was found; `standardize_domain_exports()` is a placeholder.

```text
usage script or unconfirmed agent
→ package-root send tool
→ optional default manager from settings
→ manager alert method
→ channel dispatch or level-filtered no-op
→ serialized results
→ standard success/error envelope
```

---

## 7. Usage and Caller Map

| Public symbol | Called from | Call type | Runtime or test | Evidence |
|---|---|---|---|---|
| `NotificationLevel` | `execution/live/notification_adapter.py`; manager/config/tools/providers | import and enum construction | Runtime | `notification_adapter.py:14-18`, `:68-75`, `:99-191` |
| `NotificationMessage` | manager, templates, provider test helpers, tools | construction | Runtime and test | `manager.py:388-394`; `templates.py:341-357` |
| `NotificationResult` | base/provider implementations, tools serializer | construction/serialization | Runtime | provider `send()` methods |
| `NotificationConfig` | live adapter; tools | construction/conversion | Runtime and test | `notification_adapter.py:19`, `:57-79`, `:276-316` |
| `NotificationManagerConfig` | live adapter; tools | construction | Runtime and test | `notification_adapter.py:68-79`, `:305-321` |
| `NotificationManager` | live adapter; tools | instantiation | Runtime and test | `notification_adapter.py:78-79`, `:318-321` |
| `EmailConfig` | `NotificationConfig.get_email_config()` | construction | Runtime path | `config.py:453-468` |
| `EmailNotifier` | `NotificationManager._init_email_notifier()` | instantiation | Runtime path | `manager.py:91-103` |
| `TelegramConfig` | `NotificationConfig.get_telegram_config()` | construction | Runtime path | `config.py:470-483` |
| `TelegramNotifier` | `NotificationManager._init_telegram_notifier()` | instantiation | Runtime path | `manager.py:105-117` |
| `DesktopConfig`, `DesktopNotifier` | config/manager; unit test | internal instantiation/direct test | Test-confirmed; runtime configurable | `manager.py:133-145`; desktop unit tests |
| `SMSConfig`, `SMSNotifier` | config/manager | internal instantiation | Possibly runtime-configured | `manager.py:119-131` |
| Manager trading/system/error methods | live adapter | direct method calls | Runtime | `notification_adapter.py:99-216` |
| `send_position_update()` | tool implementation only | direct internal call | Test/example | `tools.py` position implementation |
| `test_all_services()` | live adapter | direct call | Runtime diagnostic | `notification_adapter.py:218-241` |
| Manager control/statistics/template introspection methods | no caller found | n/a | None confirmed | repository-wide symbol searches |
| 11 package-root tool wrappers | unit/usage scripts; README | direct function calls | Test/example only | `test_notification.py`; usage files |
| `_common.__getattr__` | no direct caller found | possible dynamic attribute resolution | Unknown | repository search matched definition only |
| `base.NotificationTemplate` | no import/instantiation found | possible dynamic resolution | Unknown | manager/tools import `.templates.NotificationTemplate` |
| `NotificationPresets` | no caller found | n/a | None confirmed | repository search matched definition only |
| `EmailProviders` | no caller found | n/a | None confirmed | repository search matched definition only |
| Telegram media/lookup methods | no caller found | n/a | None confirmed | repository-wide symbol searches |
| SMS account/history/status/lookup methods | no caller found | n/a | None confirmed | repository-wide symbol searches |

---

## 8. Cross-Domain Surface

### Outbound — this domain depends on

| Depends on (domain/package) | Symbols or capabilities consumed | Where used in this domain | Evidence |
|---|---|---|---|
| `app.services.utils.logger` | Bound and global logging | Every implementation module except `__init__`/`_common` | imports in `base.py`, `config.py`, `manager.py`, `templates.py`, `tools.py` |
| `app.services.utils.settings` | Runtime SMTP/Telegram/general settings | `NotificationConfig.from_settings()` | `config.py:315-365` |
| `app.services.utils.standard` | Standard response specification/building and package export hook | `tools.py`; `__init__.py` | `tools.py:49-81`; `__init__.py:12`, `:79` |
| `app.services` | Dynamic service-module discovery and resolution | `_common.py` | `_common.py:16-30`; `app/services/__init__.py:35-66` |
| SMTP | Email connection and message delivery | `email.py` | `email.py:72-105`, `:204-225` |
| Telegram Bot API | Token test, text/media delivery, lookup | `telegram.py` | `telegram.py:46-369` |
| Twilio REST APIs | Credential test, SMS delivery, account/message/phone lookup | `sms.py` | `sms.py:43-321` |
| Host OS commands | PowerShell, AppleScript, `notify-send` | `desktop.py` | `desktop.py:48-121` |

The package itself does **not** depend directly on the execution or risk domains.

### Inbound — others depend on this domain

| Consuming domain/package | Symbols consumed from this domain | Purpose | Evidence |
|---|---|---|---|
| `app.services.execution.live.notification_adapter` | `NotificationLevel`, `NotificationManager`, `NotificationManagerConfig`, `NotificationConfig` | Convert live-engine events and database/config credentials into Email/Telegram alerts | `notification_adapter.py:14-20`, `:23-328` |
| `app.services.execution.live.engine` | Indirectly consumes the package through `LiveTradingNotifier` | Initializes notifications and emits safety, trade-result, and shutdown alerts | `engine.py:32`, `:330-354`, `:754-829`, `:860-865` |
| `app.services.risk.live.engine` | Inherits `MultiStrategyEngine` | Reuses the same notification integration | `risk/live/engine.py:17`, `:30`, `:47`, `:83` |
| Unit tests | Four tool wrappers plus desktop/core models | Basic envelope and OS-command tests | `tests/unit/app/services/notification/test_notification.py` |
| Usage scripts | All 11 tool wrappers | Demonstration/dry-run examples | `tests/usage/app/services/notification/tools.py`; `tests/usage/app/services/01_utils.py` |
| Potential dynamic service consumers | `_common` resolver and package exports | No concrete caller identified | `_common.py`; placeholder standardization hook |

**Boundary observation:** the live adapter imports `NotificationConfig` from the deep module `app.services.notification.config`, despite the package README stating that external callers must use only the package root.

---

## 9. Duplicate and Overlapping Behaviour

| Item A | Item B | Overlap | Evidence | Risk |
|---|---|---|---|---|
| `base.py::NotificationTemplate` | `templates.py::NotificationTemplate` | Both define template storage, rendering, add/list operations, and four identically named core templates | `base.py:245-341`; `templates.py:20-484`; manager imports the latter | Conflicting behavior and accidental import of the smaller catalogue |
| `EmailProviders.gmail()` | `NotificationPresets.gmail_setup()` | Both build Gmail-oriented configuration | `email.py:239-255`; `config.py` preset section | Two preset surfaces can drift |
| Channel-specific notifier methods | `NotificationManager.send_*()` | Both can be called directly to send; manager adds orchestration, filtering, retry, and stats | provider files; `manager.py` | Direct calls can bypass manager behavior |
| `NotificationManager.send_custom_message()` | `templates.py` `custom_message` template | Both represent custom messages, but manager constructs `NotificationMessage` directly and does not use the template | `manager.py:362-396`; `templates.py:319-320` | Template entry has no role in the manager path |
| `LiveTradingNotifier` adapter | `NotificationManager` convenience methods | Adapter repeats event-specific formatting/routing around manager methods | `notification_adapter.py`; `manager.py` | Compatibility layer is useful, but adds another notification API and hides results |
| Package root exports | `_common` dynamic resolver | Two mechanisms expose notification symbols | `__init__.py`; `_common.py` | Ambiguous official discovery path; `_common` may expose non-root internals |

---

## 10. Unused or Questionable Items

| Item | Finding | Searches performed | Confidence | Evidence |
|---|---|---|---|---|
| `base.NotificationTemplate` and its methods | Duplicate class; manager and tools import `templates.NotificationTemplate` | Definition search, package imports, class instantiation, manager/tools imports, dynamic resolver review | **Medium** | No static caller; dynamic `_common` prevents High confidence |
| `_common.py` | No direct repository caller; dynamic compatibility purpose only | Exact module reference, package import, resolver usage | **Medium** | Search matched only `_common.py` |
| `NotificationPresets` | No caller found | Class name, method names, imports, docs/tests/examples | **Medium** | Definition only; dynamic resolver remains possible |
| `EmailProviders` | No caller found | Class name, provider method names, imports, docs/tests/examples | **Medium** | Definition only |
| `EmailNotifier.send_test_email()` | No caller found | Method call, tests, examples, scripts | **High** within repository | Only definition |
| Telegram chat/test/media/update methods | No caller found | Each method call, imports, tests, examples, scripts | **High** within repository | Only definitions |
| SMS account/test/status/history/lookup methods | No caller found | Each method call, imports, tests, examples, scripts | **High** within repository | Only definitions |
| Most template administration/introspection methods | No caller found beyond internal method-to-method calls | Method calls, manager pass-throughs, tests/examples | **High** within repository | Definitions and internal calls only |
| Manager service controls/statistics/introspection | No production caller found; some are not even tested | Method calls across repository | **High** within repository | Definitions only, except service status tool |
| Package-root send wrappers | Called by README/usage scripts, not production modules | Root imports, exact calls, agent tools, routes, scripts, tests, dynamic registration hook | **High** for no production caller in repository | usage files; standardization hook is placeholder |
| `create_notification_manager()` wrapper | Returns only `"created"` and cannot provide the manager to a subsequent tool call | Call-site and implementation review | **High** | `tools.py` wrapper implementation |
| `REQUIRES_APPROVAL` constant | Declared but not copied into `ToolStandardSpec` | Constant references and response builder | **High** | `tools.py:38-81` |
| `NotificationConfig.is_any_service_enabled()` / `get_enabled_services()` / `print_configuration()` | No caller found | Exact method calls, tests, usage scripts | **High** within repository | definitions only |
| Most of the 20 templates | No runtime selection; only four manager convenience paths use named templates | Template-name searches, manager methods, tools/examples | **Medium** | Generic dynamic render remains possible |
| README dependency and thread-safety claims | `pydantic` is not imported by the package; manager initialization is not protected by a singleton/init lock | Dependency imports and manager implementation | **High** | `README.md:43-45`; package files; `manager.py:54-79` |

No item is labelled dead code because dynamic/external consumers cannot be fully excluded.

---

## 11. Incomplete or Disconnected Workflows

| Workflow / capability | Missing connection | Current impact | Evidence |
|---|---|---|---|
| Startup notification | Engine call to `notify_startup()` is commented out | No startup alert from the live engine | `execution/live/engine.py` run method around lines 611-613 |
| Connection-error notification | `notify_connection_error()` exists only in adapter | MT5/main-loop failures are logged but not routed through this method | exact call search matched adapter definition only |
| Daily summary notification | `notify_daily_summary()` exists only in adapter | No scheduled/end-of-day summary path | exact call search matched adapter definition only |
| Position-update manager/tool workflow | No production caller found | Capability exists only in usage examples | manager/tool call search |
| Rich Telegram media | No manager or runtime route to `send_photo()`/`send_document()` | Media helpers are isolated from main workflows | `telegram.py`; no callers |
| SMS diagnostics/history | No manager or runtime route for account/history/status/lookup helpers | Operational helpers are isolated | `sms.py`; no callers |
| Extended template catalogue | 16 of 20 templates have no manager convenience route or confirmed runtime render call | Large catalogue provides no demonstrated live-system value | `templates.py`; manager methods |
| Agent tool registration | Export hook performs logging only and returns without wrapping or registering exports | No confirmed agent runtime discovery path | `standard.py:1322-1328`; `notification/__init__.py:79` |
| Delivery outcome feedback | Live adapter discards result maps from manager methods | Engine cannot react to notification delivery failure | `notification_adapter.py:88-216` |
| Email delivery | Authentication step is absent from the send path | Authenticated SMTP can fail despite a successful connection test | `email.py:72-105`, `:216-225` |

---

## 12. Structural Problems

| ID | Problem | Location | Impact | Evidence |
|---|---|---|---|---|
| `V1-ISSUE-NOTIFICATION-001` | SMTP send path does not authenticate | `email.py::EmailNotifier.send` | Authenticated providers can reject actual messages; diagnostics can still pass | `email.py:72-105` vs `test_connection():216-225` |
| `V1-ISSUE-NOTIFICATION-002` | Duplicate `NotificationTemplate` implementations | `base.py`, `templates.py` | Conflicting catalogues and accidental wrong imports | `base.py:245-341`; `templates.py:20-484` |
| `V1-ISSUE-NOTIFICATION-003` | Default INFO alerts can become successful no-ops | `config.py`, `manager.py`, `tools.py` | Custom/trading tools can report success with `{}` and no delivery | default levels `config.py:65-69`; filter `manager.py:173-178`; wrappers |
| `V1-ISSUE-NOTIFICATION-004` | Network metadata is false for mutating tools | `tools.py::REQUIRES_NETWORK` | Permission, audit, or agent policy systems receive incorrect capability metadata | `tools.py:38-46`, `:60-81` |
| `V1-ISSUE-NOTIFICATION-005` | Desktop delivery ignores command failure and config enabled flag | `desktop.py` | False-positive success and unexpected local alerts | `desktop.py:24-121` |
| `V1-ISSUE-NOTIFICATION-006` | Naive local time is rendered with a UTC label | `base.py`, `email.py`, `telegram.py`, `sms.py` | Misleading event timestamps | `base.py:53`; channel formatters |
| `V1-ISSUE-NOTIFICATION-007` | Telegram and SMS constructors perform credential-test network calls | `telegram.py::__init__`, `sms.py::__init__` | Manager creation/status inspection can block or fail due to network | `telegram.py:49-67`; `sms.py:46-68` |
| `V1-ISSUE-NOTIFICATION-008` | Provider dispatch is synchronous in live execution path | manager and live adapter | Trading loop can wait on provider timeouts/retries | manager loop `manager.py:180-208`; engine calls |
| `V1-ISSUE-NOTIFICATION-009` | Live adapter discards delivery results | `execution/live/notification_adapter.py` | Failures are not visible to engine control flow | adapter notification methods |
| `V1-ISSUE-NOTIFICATION-010` | Provider partial failures collapse into one success result | `telegram.py::send`, `sms.py::send` | Per-recipient failures are lost to callers | Telegram `:88-120`; SMS `:89-121` |
| `V1-ISSUE-NOTIFICATION-011` | Configuration loaders and writers swallow errors inconsistently | `config.py` | Invalid/missing config can silently become defaults; writes can fail without caller signal | `from_ini`, `from_file`, `save_to_file` |
| `V1-ISSUE-NOTIFICATION-012` | Empty mapping is treated as “use live settings” | `tools.py` validation/manager wrappers | `config={}` does not mean an explicit empty/default config and can activate configured providers | falsy conditional constructions in wrappers |
| `V1-ISSUE-NOTIFICATION-013` | Package root-only import rule is violated by its production consumer | README and live adapter | Documented boundary is not followed | `README.md:9-11`; adapter deep import at line 19 |
| `V1-ISSUE-NOTIFICATION-014` | Export standardization/registration is a placeholder | `utils/standard.py`, notification `__init__.py` | No actual registry or wrapping occurs through the declared hook | `standard.py:1322-1328`; `__init__.py:79` |
| `V1-ISSUE-NOTIFICATION-015` | Startup, connection-error, and daily-summary adapter capabilities are disconnected | live engine/adapter | Intended operational alerts are not emitted | commented startup call; no other callers |
| `V1-ISSUE-NOTIFICATION-016` | Test coverage does not exercise production-critical providers or live integration | test suite | Email defect, level filtering, provider initialization, retry, and adapter failures are undetected | sole unit file covers four tools and desktop |
| `V1-ISSUE-NOTIFICATION-017` | README overstates thread safety and lists unused package dependency | `README.md` | Documentation does not match implementation | README rules/dependencies; manager only locks stats and rate limiter locks requests |
| `V1-ISSUE-NOTIFICATION-018` | `create_notification_manager()` tool does not return a usable manager | `tools.py` | Tool cannot establish reusable state for subsequent calls; each default operation reconstructs a manager | wrapper returns only status |
| `V1-ISSUE-NOTIFICATION-019` | Media sends bypass common retry/rate-limit flow | `telegram.py::send_photo`, `send_document` | Different reliability behavior from text notifications | direct `requests.post()` methods |
| `V1-ISSUE-NOTIFICATION-020` | Rate-limit accounting occurs before each attempt | `base.py::_send_with_retry`, `RateLimiter.can_send` | Retries consume additional quota and can rate-limit their own sequence | `base.py:95-109`, `:169-210` |

---

## 13. V1 Capability Catalogue

| Capability ID | Capability | Current implementation | Workflow(s) | Usage status | Value status | Notes |
|---|---|---|---|---|---|---|
| `V1-CAP-NOTIFICATION-001` | Canonical notification levels | `base.py::NotificationLevel` | All | Used | Essential | Five levels |
| `V1-CAP-NOTIFICATION-002` | Canonical message and result contracts | `NotificationMessage`, `NotificationResult`, `NotificationError` | All | Used | Essential | Naive timestamps |
| `V1-CAP-NOTIFICATION-003` | Per-notifier rate limiting and retry | `RateLimiter`, `BaseNotifier.send_message()` | WF-001, WF-002, WF-004 | Used | Supporting | In-memory; retry consumes quota |
| `V1-CAP-NOTIFICATION-004` | Multi-channel orchestration | `NotificationManager`, `NotificationManagerConfig` | WF-001, WF-002, WF-004 | Used | Essential | Sequential dispatch |
| `V1-CAP-NOTIFICATION-005` | Alert-level filtering | `NotificationManager.send_notification()` | WF-001, WF-002, WF-004 | Used | Supporting | Creates default INFO no-op issue |
| `V1-CAP-NOTIFICATION-006` | Trading alert formatting/delivery | manager + `trading_alert` template | WF-001, WF-004 | Used in live adapter | Essential | Live execution result path |
| `V1-CAP-NOTIFICATION-007` | System/safety/shutdown alert formatting/delivery | manager + `system_alert` template | WF-001, WF-004 | Used | Essential | Startup call disconnected |
| `V1-CAP-NOTIFICATION-008` | Error alert formatting/delivery | manager + `error_alert` template | WF-001, WF-004 | Used | Essential | Trade execution failures |
| `V1-CAP-NOTIFICATION-009` | Position-update alerts | manager + `position_update` template | WF-004 | Test-only | Useful | No production caller |
| `V1-CAP-NOTIFICATION-010` | Custom messages | manager direct message construction | WF-004 | Test-only; adapter method disconnected | Useful | Default INFO can be filtered |
| `V1-CAP-NOTIFICATION-011` | Email notification | `email.py` | WF-001, WF-002 | Used | Essential | Actual authenticated send defective |
| `V1-CAP-NOTIFICATION-012` | Telegram text notification | `telegram.py` | WF-001, WF-002 | Used | Essential | Constructor validates token over network |
| `V1-CAP-NOTIFICATION-013` | Telegram media and chat/update utilities | `send_photo`, `send_document`, `get_chat_info`, `get_updates` | None confirmed | Unused within repo | Questionable | Bypasses manager/retry |
| `V1-CAP-NOTIFICATION-014` | Twilio SMS notification | `sms.py::send` | WF-002, WF-004 candidate | Possibly used | Useful | No production configuration confirmed |
| `V1-CAP-NOTIFICATION-015` | Twilio account/message/phone utilities | `sms.py` lookup methods | None confirmed | Unused within repo | Questionable | Isolated |
| `V1-CAP-NOTIFICATION-016` | Native desktop notification | `desktop.py` | WF-002, WF-004 candidate | Test-only confirmed | Useful | Can report false success |
| `V1-CAP-NOTIFICATION-017` | Configuration from application settings | `NotificationConfig.from_settings()` | WF-003, WF-004 | Test-only confirmed | Useful | Used by default tools |
| `V1-CAP-NOTIFICATION-018` | Configuration from INI/environment/JSON | `NotificationConfig.from_ini/from_env/from_file` | None confirmed | Unused within repo | Questionable | Multiple silent fallback behaviors |
| `V1-CAP-NOTIFICATION-019` | Configuration validation | `NotificationConfig.validate()` and wrapper | WF-003 | Test-only | Useful | Returns string errors |
| `V1-CAP-NOTIFICATION-020` | Configuration persistence | `NotificationConfig.save_to_file()` | None confirmed | Unused within repo | Questionable | Swallows write errors |
| `V1-CAP-NOTIFICATION-021` | Provider/environment presets | `NotificationPresets`, `EmailProviders` | None confirmed | Unused within repo | Questionable | Overlapping preset surfaces |
| `V1-CAP-NOTIFICATION-022` | Predefined template catalogue | `templates.py::NotificationTemplate` | WF-001–WF-004 | Partially used | Supporting | 20 templates; four used by manager routes |
| `V1-CAP-NOTIFICATION-023` | Runtime template administration | add/update/remove/import/export/introspection | None confirmed | Mostly unused | Questionable | In-memory only |
| `V1-CAP-NOTIFICATION-024` | Service enable/disable and status | manager control/status methods | WF-003 | Status test-only; control unused | Useful/Questionable | No runtime management caller |
| `V1-CAP-NOTIFICATION-025` | In-memory delivery statistics | manager statistics methods | WF-002 | Updated internally; never read in production | Supporting/Questionable | Not persisted |
| `V1-CAP-NOTIFICATION-026` | Standard-envelope agent tools | `tools.py` and package exports | WF-003, WF-004 | Test-only | Questionable | No working registry found |
| `V1-CAP-NOTIFICATION-027` | Dynamic lower-level symbol resolution | `_common.py` | None confirmed | Possibly used | Questionable | No caller; exposes internals |
| `V1-CAP-NOTIFICATION-028` | Live execution compatibility adapter | `execution/live/notification_adapter.py` consuming this domain | WF-001 | Used | Essential | DB/config credentials and event mapping |
| `V1-CAP-NOTIFICATION-029` | Live startup notification | adapter `notify_startup()` | Intended WF-001 | Disconnected | No demonstrated value currently | Engine call commented |
| `V1-CAP-NOTIFICATION-030` | Live connection-error notification | adapter `notify_connection_error()` | Intended WF-001 | Unused | No demonstrated value currently | No caller |
| `V1-CAP-NOTIFICATION-031` | Live daily summary | adapter `notify_daily_summary()` | Intended WF-001 | Unused | No demonstrated value currently | No scheduler/caller |

---

## 14. Audit Conclusions

### Valuable behaviour worth preserving

The codebase demonstrates real value in the following existing behavior:

* the canonical notification message/result/level model;
* the manager’s common multi-channel interface;
* template-based trading, system, position, and error alerts;
* per-channel rate limits and retry handling;
* Email and Telegram configuration mapping from the live execution adapter;
* confirmed trade-result, safety-violation, and shutdown alert call paths;
* standardized serializable wrapper responses for tests or possible external agents.

The live execution integration proves that this domain is not wholly isolated. Telegram delivery has a complete static path from live event to external API call. Email has the same call path but contains a blocking implementation defect.

### Behaviour that exists but is disconnected

The following capabilities exist without a confirmed production connection:

* startup alert invocation;
* connection-error and daily-summary adapter methods;
* position-update agent tool;
* rich Telegram media and lookup helpers;
* Twilio account/history/status/phone helpers;
* service enable/disable controls;
* statistics retrieval/reset;
* most template administration methods;
* most of the 20 predefined templates;
* package-root tool use by an actual agent runtime.

### Likely dead weight

No item is formally declared dead code because dynamic/external use cannot be completely excluded. The strongest candidates for removal review are:

* `base.py::NotificationTemplate`;
* `_common.py` dynamic compatibility surface;
* unused provider preset classes;
* unused provider administration methods;
* unused template administration and extended catalogue entries;
* the placeholder package-export standardization hook.

### Duplicated responsibilities

The main duplication is the two template classes. Additional overlap exists between provider presets, manager methods versus direct notifier methods, package-root exports versus `_common` resolution, and the live adapter versus manager convenience methods.

### Important uncertainties

* No provider call was executed.
* No runtime logs were available.
* Notification credentials and active deployment settings were unavailable.
* Tests were not run.
* Repository-external consumers may use symbols that have no caller inside the repository.
* The connector did not provide a recursive file tree, so the package boundary has high but not absolute confidence.

### Areas requiring manual confirmation

* Whether production relies primarily on Telegram, Email, or both.
* Whether SMTP servers in use permit unauthenticated sending after connection; the configured providers and `test_connection()` imply authentication is expected.
* Whether external agent infrastructure imports package-root tools directly despite the placeholder standardization hook.
* Whether SMS and desktop channels are enabled in any deployed settings.
* Whether `_common.py` is consumed by external reflection code.
* Whether any deployment depends on the isolated template/provider administration methods.

---

## Final Validation

* Every identified Python file in `app/services/notification` is represented.
* All 25 package-root `__all__` exports were checked against code.
* `__init__.py` exports and the standardization hook were inspected.
* Imports, calls, inheritance, dynamic resolution, tests, examples, configuration paths, and live-engine integration were searched.
* Production usage is separated from test/example-only usage.
* Inbound and outbound dependency surfaces are summarized.
* Workflows are based on actual static call paths.
* Uncertainty is explicitly labelled.
* No Version 2 requirements or redesign were introduced.
* No repository code was modified.
