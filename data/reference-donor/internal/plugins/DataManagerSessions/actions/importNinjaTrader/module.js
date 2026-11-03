// Import NinjaTrader 8 Trading Hours templates into SQX sessions (plan 138, issue #175).
//
// A plain toolbar action rather than a modal: the templates live at a fixed path that ships with
// NinjaTrader, so the common case - "bring in the exchange's hours" - needs no input from the user
// at all. A custom file or folder goes through sqcli (`-session action=import path=...`), and so
// does overwriting, which stays a deliberate act.
angular.module('app.sessions').config(function (sqPluginProvider) {

    sqPluginProvider.plugin('DataManagerActionSession', 90, {
        key: 'importNinjaTrader',
        title: Ltsq('Import NinjaTrader sessions'),
        source: 'sessions',
        // toKebabCase("importNinjaTrader") - never hand-picked; the id is also rendered as the
        // data-testid, so a shortened one breaks the UI catalog convention.
        class: 'load',
        id: "datamanager-session-import-ninja-trader"
    });
});
