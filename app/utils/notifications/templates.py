"""Thread-safe notification template storage and rendering."""

# Template literals intentionally preserve readable notification layout.
# ruff: noqa: E501

from __future__ import annotations

import html
from collections.abc import Mapping
from string import Formatter
from threading import RLock
from types import MappingProxyType

from app.utils.errors.exceptions import ConfigurationError

_BUILT_INS = MappingProxyType(
    {
        "trading_alert": (
            "Trading Alert: {symbol} {action}",
            "Symbol: {symbol}\nAction: {action}\nPrice: {price}\nReason: {reason}\nTime: {timestamp}\nAccount: {account}\nStrategy: {strategy}\nRisk Level: {risk_level}",
            "<p>Symbol: {symbol}<br>Action: {action}<br>Price: {price}<br>Reason: {reason}<br>Time: {timestamp}<br>Account: {account}<br>Strategy: {strategy}<br>Risk Level: {risk_level}</p>",
        ),
        "trading_signal": (
            "Trading Signal: {symbol} {signal_type}",
            "{signal_type} {symbol} @ {entry_price}\nStop Loss: {stop_loss} ({stop_loss_pips} pips)\nTake Profit: {take_profit} ({take_profit_pips} pips)\nLots: {lots}\nStrategy: {strategy}\nStrength: {strength}\nADR: {adr}\nRange: {range}%\nCurrent VAR: {current_var}\nProposed VAR: {proposed_var}\nVAR Difference: {var_difference}%\nTime: {timestamp}",
            "<p>{signal_type} {symbol} @ {entry_price}<br>Stop Loss: {stop_loss}<br>Take Profit: {take_profit}<br>Lots: {lots}<br>Strategy: {strategy}<br>Strength: {strength}<br>Time: {timestamp}</p>",
        ),
        "position_opened": (
            "Position Opened: {symbol} {direction}",
            "Symbol: {symbol}\nDirection: {direction}\nSize: {size}\nEntry: {entry_price}\nStop Loss: {stop_loss}\nTake Profit: {take_profit}\nTime: {timestamp}\nAccount: {account}\nStrategy: {strategy}\nRisk: {risk_amount}",
            "<p>Position opened: {symbol} {direction}<br>Size: {size}<br>Entry: {entry_price}</p>",
        ),
        "position_closed": (
            "Position Closed: {symbol} {direction}",
            "Symbol: {symbol}\nDirection: {direction}\nSize: {size}\nEntry: {entry_price}\nExit: {exit_price}\nP&amp;L: {pnl}\nP&amp;L %: {pnl_percent}\nDuration: {duration}\nTime: {timestamp}\nAccount: {account}\nStrategy: {strategy}",
            "<p>Position closed: {symbol} {direction}<br>P&amp;L: {pnl}<br>Duration: {duration}</p>",
        ),
        "position_update": (
            "Position Update: {symbol}",
            "Symbol: {symbol}\nType: {position_type}\nSize: {size}\nEntry: {entry_price}\nCurrent: {current_price}\nP&amp;L: {pnl}\nP&amp;L %: {pnl_percent}\nTime: {timestamp}",
            "<p>Position update: {symbol}<br>Current: {current_price}<br>P&amp;L: {pnl}</p>",
        ),
        "system_alert": (
            "System Alert: {level} - {message}",
            "Level: {level}\nMessage: {message}\nDetails: {details}\nTime: {timestamp}\nComponent: {component}\nStatus: {status}",
            "<p><strong>{level}</strong>: {message}<br>{details}<br>{component}: {status}</p>",
        ),
        "system_startup": (
            "System Startup: HaruQuantAI",
            "Started: {timestamp}\nVersion: {version}\nEnvironment: {environment}\nAccount: {account}\nMT5: {mt5_status}\nData Feed: {data_feed_status}\nStrategy: {strategy_status}\nRisk Manager: {risk_manager_status}",
            "<p>HaruQuantAI started at {timestamp}<br>Environment: {environment}</p>",
        ),
        "system_shutdown": (
            "System Shutdown: HaruQuantAI",
            "Shutdown: {timestamp}\nReason: {reason}\nDuration: {duration}\nOpen Positions: {open_positions}\nBalance: {account_balance}\nDaily P&amp;L: {daily_pnl}",
            "<p>HaruQuantAI shutdown at {timestamp}<br>Reason: {reason}</p>",
        ),
        "connection_lost": (
            "Connection Lost: {service}",
            "Service: {service}\nLost: {timestamp}\nError: {error_message}\nRetry: {retry_count}\nNext Retry: {next_retry}",
            "<p>Connection lost: {service}<br>Error: {error_message}</p>",
        ),
        "connection_restored": (
            "Connection Restored: {service}",
            "Service: {service}\nRestored: {timestamp}\nDowntime: {downtime}\nStatus: Active",
            "<p>Connection restored: {service}<br>Downtime: {downtime}</p>",
        ),
        "error_alert": (
            "Error Alert: {error_type}",
            "Type: {error_type}\nMessage: {message}\nComponent: {component}\nTime: {timestamp}\nStack Trace: {stack_trace}",
            "<p>Error: {error_type}<br>{message}<br>Component: {component}</p>",
        ),
        "strategy_error": (
            "Strategy Error: {strategy_name}",
            "Strategy: {strategy_name}\nError: {error_message}\nSymbol: {symbol}\nTime: {timestamp}\nAction: {action}\nStatus: {status}",
            "<p>Strategy error: {strategy_name}<br>{error_message}</p>",
        ),
        "performance_alert": (
            "Performance Alert: {alert_type}",
            "Type: {alert_type}\nMetric: {metric}\nValue: {value}\nThreshold: {threshold}\nTime: {timestamp}\nPeriod: {period}\nAccount: {account}",
            "<p>{metric}: {value}<br>Threshold: {threshold}</p>",
        ),
        "drawdown_alert": (
            "Drawdown Alert: {drawdown_type}",
            "Type: {drawdown_type}\nCurrent: {current_drawdown}%\nPeak: {peak_drawdown}%\nDuration: {duration}\nTime: {timestamp}\nAccount: {account}\nBalance: {balance}\nEquity: {equity}",
            "<p>Drawdown: {current_drawdown}%<br>Peak: {peak_drawdown}%</p>",
        ),
        "market_alert": (
            "Market Alert: {symbol}",
            "Symbol: {symbol}\nEvent: {event}\nPrice: {price}\nTime: {timestamp}\nImpact: {impact}\nDetails: {details}",
            "<p>Market alert: {symbol}<br>{event}<br>Impact: {impact}</p>",
        ),
        "news_alert": (
            "News Alert: {headline}",
            "Headline: {headline}\nSource: {source}\nTime: {timestamp}\nImpact: {impact}\nSummary: {summary}\nSymbols: {symbols}",
            "<p>{headline}<br>Source: {source}<br>{summary}</p>",
        ),
        "risk_alert": (
            "Risk Alert: {risk_type}",
            "Type: {risk_type}\nSeverity: {severity}\nMessage: {message}\nTime: {timestamp}\nAccount: {account}\nCurrent Risk: {current_risk}\nMax Risk: {max_risk}\nAction: {action}",
            "<p>Risk: {risk_type} ({severity})<br>{message}<br>Action: {action}</p>",
        ),
        "margin_alert": (
            "Margin Alert: {account}",
            "Account: {account}\nMargin Level: {margin_level}%\nFree Margin: {free_margin}\nUsed Margin: {used_margin}\nTime: {timestamp}\nWarning Level: {warning_level}%\nAction: {action}",
            "<p>Margin level: {margin_level}%<br>Action: {action}</p>",
        ),
        "custom_message": ("{title}", "{body}", "<p>{body}</p>"),
        "test_message": (
            "Test Message: {service}",
            "Service: {service}\nTime: {timestamp}\nStatus: {status}\nThis is a notification configuration test.",
            "<p>Test: {service}<br>Time: {timestamp}<br>Status: {status}</p>",
        ),
        "info": ("Information", "{message}", "<p>{message}</p>"),
        "warning": (
            "Warning",
            "{message}",
            "<p><strong>Warning:</strong> {message}</p>",
        ),
        "error": ("Error", "{message}", "<p><strong>Error:</strong> {message}</p>"),
        "critical": (
            "Critical alert",
            "{message}",
            "<p><strong>Critical:</strong> {message}</p>",
        ),
        "trading": (
            "Trading alert",
            "{message}",
            "<p><strong>Trading:</strong> {message}</p>",
        ),
        "risk": ("Risk alert", "{message}", "<p><strong>Risk:</strong> {message}</p>"),
        "system_health": (
            "System health",
            "{message}",
            "<p><strong>System health:</strong> {message}</p>",
        ),
    }
)


class TemplateRegistry:
    """Own built-in and session-local custom notification templates."""

    def __init__(self) -> None:
        """Initialize an isolated registry.

        Args:
            None.

        Raises:
            None.
        """
        self._lock = RLock()
        self._templates = dict(_BUILT_INS)

    def names(self) -> tuple[str, ...]:
        """Return registered names in deterministic order.

        Returns:
            Tuple of registered template names.
        """
        with self._lock:
            return tuple(sorted(self._templates))

    def register(self, name: str, title: str, text: str, html_body: str) -> None:
        """Register or replace a custom template.

        Args:
            name: Custom template name.
            title: Title format string.
            text: Plain-text format string.
            html_body: HTML format string.

        Raises:
            ConfigurationError: If the custom template is invalid.
        """
        normalized = name.strip().lower()
        if (
            not normalized
            or normalized in _BUILT_INS
            or not title.strip()
            or not text.strip()
        ):
            raise ConfigurationError("NOTIFICATION_TEMPLATE_INVALID")
        with self._lock:
            self._templates[normalized] = (title, text, html_body)

    def render(self, name: str, values: Mapping[str, object]) -> Mapping[str, str]:
        """Render one template with complete, escaped values.

        Args:
            name: Registered template name.
            values: Complete rendering values.

        Returns:
            Immutable rendered title, text, and HTML mapping.

        Raises:
            ConfigurationError: If the template or a required value is missing.
        """
        with self._lock:
            template = self._templates.get(name.strip().lower())
        if template is None:
            raise ConfigurationError("NOTIFICATION_TEMPLATE_UNKNOWN")
        fields = {
            field_name
            for part in template
            for _, field_name, _, _ in Formatter().parse(part)
            if field_name
        }
        if not fields.issubset(values):
            raise ConfigurationError("NOTIFICATION_TEMPLATE_VALUE_MISSING")
        plain = {key: str(value) for key, value in values.items()}
        escaped = {key: html.escape(value) for key, value in plain.items()}
        return MappingProxyType(
            {
                "title": template[0].format_map(plain),
                "text": template[1].format_map(plain),
                "html": template[2].format_map(escaped),
            }
        )


__all__ = ("TemplateRegistry",)
