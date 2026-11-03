angular.module('app').service('AlgoCloudService', function($rootScope, $injector, BackendService, AppService, L) {

    // "Open in AlgoCloud" - the one host implementation behind every button (AlgoWizard menu,
    // Results source code tab, AI chat). The callers reach it through their bridge:
    //   awEditorInterface.externalEventHandler("openInAlgoCloud", args)   AlgoWizardService.js
    //   resultsInterface.actionHandler("openInAlgoCloud", args)            Results2Service.js
    //   aichatInterface.request("openInAlgoCloud", args)                   SQAIChatService.js
    // args identify the strategy in exactly one way:
    //   {strategyXML, lastSettingsXML|settingsXML, strategyName}   XML already in hand
    //   {file}                                                     .sqx/.sqw/.xml under the data dir
    //   {project|name, databank, strategy}                         a databank row
    //   {backtestID}                                               an AlgoWizard backtest
    // POST /algocloud/import does the pre-flight, the upload and builds the browser URL; the
    // warnings AlgoCloud returns are shown in a confirm dialog first (English sentences generated
    // server-side, displayed verbatim inside a translated lead-in), then the system browser opens
    // the import link. Resolves {success:true} | {cancelled:true} | {error}.
    this.open = function(args) {
        args = args || {};

        var data = {};
        if (args.strategyXML) {
            data.strategyXML = args.strategyXML;
            var settings = args.lastSettingsXML || args.settingsXML;
            if (settings) data.lastSettingsXML = settings;
            if (args.strategyName) data.strategyName = args.strategyName;
        } else if (args.file) {
            data.file = args.file;
        } else if (args.strategy) {
            data.project = args.project || args.name;
            data.databank = args.databank;
            data.strategy = args.strategy;
        } else if (args.backtestID) {
            data.backtestID = args.backtestID;
        } else {
            var missing = L.tsq("There is no strategy to open in AlgoCloud.");
            $rootScope.showError(missing);
            return Promise.resolve({ error: missing });
        }

        // The result is checked here: a refusal is a plain sentence for the user, not a
        // "communication error" toast.
        return BackendService.httpRequest("/algocloud/import", data, "POST", false, true).then(function(result) {
            if (!result || result.error || !result.url) {
                var message = (result && result.error) || L.tsq("AlgoCloud import failed.");
                $rootScope.showError(message);
                return { error: message };
            }

            var warnings = result.warnings || [];
            if (warnings.length === 0) {
                AppService.openBrowser(result.url);
                return { success: true, warnings: [] };
            }

            return new Promise(function(resolve) {
                $rootScope.showConfirm(
                    L.tsq("Open in AlgoCloud"),
                    warningsHtml(warnings),
                    function(confirmed) {
                        if (!confirmed) return resolve({ cancelled: true, warnings: warnings });
                        AppService.openBrowser(result.url);
                        resolve({ success: true, warnings: warnings });
                    },
                    true,
                    function() { resolve({ cancelled: true, warnings: warnings }); },
                    L.tsq("Open")
                );
            });
        });
    };

    // #confirmDialog renders the message as HTML, so the warnings go in as an escaped list.
    function warningsHtml(warnings) {
        var items = warnings.map(function(w) {
            return "<li>" + escapeHtml(w) + "</li>";
        }).join("");
        return "<p>" + escapeHtml(L.tsq("The strategy can be opened and backtested in AlgoCloud, but:")) + "</p>"
            + "<ul>" + items + "</ul>"
            + "<p>" + escapeHtml(L.tsq("Do you want to open it anyway?")) + "</p>";
    }

    function escapeHtml(text) {
        return String(text == null ? "" : text)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;");
    }
});
