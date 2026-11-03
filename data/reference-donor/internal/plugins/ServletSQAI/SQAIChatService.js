angular.module('app.sqaichat').service('SQAIChatService', function ($rootScope, $injector, BackendService, SQConstants, SQEvents, AppService, SQWebSocketService, AlgoCloudService, L) {
    console.log("Initializing SQAIChatService");

    /*
     * Host bridge for the AI chat — window.top.aichatInterface.
     *
     * The chat is a standalone app in the SQX side panel (#sq-ai-frame -> /SQAI/chat/, built
     * from the strategyquantsro/ai-chat repo). This service is the entire SQX side of its
     * contract: aichatInterface is the only SQX object the chat repo knows about.
     *
     * It deliberately does not ride on awEditorInterface. Skin, language and license have
     * nothing to do with the AlgoWizard editor, and hanging them off the editor bridge meant
     * the chat only got a license if and when AlgoWizard finished preloading — which happens
     * after the WebSocket has already delivered it, and does not happen at all if the preload
     * is skipped or fails. Only the editor-bound requests reach the editor, and only when the
     * chat actually makes one.
     *
     *   getConfig()            what the app is        — resolves independently of AlgoWizard
     *   getState()             current app state      — snapshot, for a late subscriber
     *   registerHandler(fn)    state changes          — replays the last of each event
     *   request(action, args)  chat -> host           — editor calls, notices, links
     */

    // The plugin bundle loads in every module iframe; only the shell owns the panel and the
    // window.top object. Same guard AlgoWizardService uses for its event listener. Two shells
    // host the panel: SQX (SQUANT) and QuantDataManager (QDM).
    var SHELLS = { SQUANT: 'SQX', QDM: 'QDM' };
    var hostApp = SHELLS[window.appConfig.product];
    if (!hostApp) return;
    var isSqx = hostApp === 'SQX';

    // State events, and the last payload of each. The chat iframe mounts long after startup
    // and the license arrives over a WebSocket before that, so a fire-and-forget notification
    // would leave a freshly mounted chat with nothing — registerHandler replays instead.
    var STATE_EVENTS = ['skin', 'language', 'license', 'symbols', 'backtestFinished', 'features'];
    var lastState = {};
    var handlers = [];
    var configPromise = null;
    // app config codes (license token) the chat config carries: the introduction video and the pages it links to
    var INTRO_VIDEO_CONFIG = 'ai_intro_video';
    var LINK_CONFIGS = { introduction: 'ai_introduction', pricing: 'ai_pricing', terms: 'ai_terms', privacy: 'ai_privacy_policy' };
    var CHAT_CONFIG_CODES = [INTRO_VIDEO_CONFIG, LINK_CONFIGS.introduction, LINK_CONFIGS.pricing, LINK_CONFIGS.terms, LINK_CONFIGS.privacy];

    function emit(eventName, payload) {
        if (STATE_EVENTS.indexOf(eventName) >= 0) {
            lastState[eventName] = payload;
        }

        handlers.forEach(function (handler) {
            try {
                handler(eventName, payload);
            } catch (e) {
                console.error("[aichat] handler failed for '" + eventName + "'", e);
            }
        });
    }

    //- Skin ------------------------------------------------------------------------

    /*
     * What the chat needs to look like the app it sits in.
     *
     * The chat is an iframe with its own stylesheet, so none of the shell's skin reaches
     * it - the colors have to travel as data. Three things go over:
     *
     *   theme       the skin's name, as before
     *   dark        read from the shell's real background, not from the name, so a
     *               user-installed Skin plugin called anything at all still lands on the
     *               right side
     *   brEdition   the Brazilian edition repaints the app green with gradients, which
     *               cannot be sampled as a color - it is reported as a fact and the chat
     *               switches to its green theme pair
     *   palette     the shell's accent, sampled from a throwaway .btn-primary, so a custom
     *               skin's own color reaches the chat too
     */

    function parseRgb(value) {
        var match = /rgba?\(\s*(\d+)[\s,]+(\d+)[\s,]+(\d+)(?:[\s,/]+([\d.]+))?/.exec(String(value || ''));
        if (!match) return null;
        var alpha = match[4] === undefined ? 1 : parseFloat(match[4]);
        if (!(alpha > 0.1)) return null;   // transparent - tells us nothing
        return { r: +match[1], g: +match[2], b: +match[3] };
    }

    function toHex(rgb) {
        function pair(n) { return ('0' + Math.max(0, Math.min(255, n | 0)).toString(16)).slice(-2); }
        return '#' + pair(rgb.r) + pair(rgb.g) + pair(rgb.b);
    }

    function luminance(rgb) {
        return (0.2126 * rgb.r + 0.7152 * rgb.g + 0.0722 * rgb.b) / 255;
    }

    /* A gradient has no background-color; its first color stop is the accent. */
    function colorOf(style) {
        return parseRgb(style.backgroundColor) || parseRgb(style.backgroundImage);
    }

    /*
     * Measure a class the way the shell would render it. The probe is appended inside the
     * .br-edition wrapper when there is one, because that is where the edition's overrides
     * are scoped - a probe on <body> would measure the stock blue in a green app.
     */
    function measure(className, read) {
        var doc, host, probe;
        try {
            doc = window.top.document;
            host = doc.querySelector('.br-edition') || doc.body;
            if (!host) return null;

            probe = doc.createElement('div');
            probe.className = className;
            probe.style.position = 'absolute';
            probe.style.left = '-9999px';
            probe.style.top = '0';
            probe.style.width = '10px';
            probe.style.height = '10px';
            host.appendChild(probe);

            return read(window.getComputedStyle(probe));
        } catch (e) {
            return null;
        } finally {
            if (probe && probe.parentNode) probe.parentNode.removeChild(probe);
        }
    }

    /* The page's own background, for the light/dark verdict. First opaque one wins. */
    function shellBackground() {
        try {
            var doc = window.top.document;
            var candidates = [doc.querySelector('#main'), doc.body, doc.documentElement];
            for (var i = 0; i < candidates.length; i++) {
                if (!candidates[i]) continue;
                var rgb = parseRgb(window.getComputedStyle(candidates[i]).backgroundColor);
                if (rgb) return rgb;
            }
        } catch (e) { /* no shell document - fall back to the skin name */ }
        return null;
    }

    /*
     * A white-label edition can set its own accent for the whole app: CustomizationService
     * reads /main/customizations, picks the entry for the active language and injects
     * edition_color over everything (SQUANT/layout/CustomizationService.js). Its CSS names
     * #aw-editor explicitly but knows nothing about the chat, so the color is taken from the
     * source here instead of being read back out of a stylesheet.
     */
    function editionColor() {
        var customization = $rootScope.currentEditionCustomization;
        var color = customization && customization.edition_color;
        return typeof color === 'string' && color ? color : null;
    }

    function skinPayload(skinName) {
        var background = shellBackground();
        // The edition's own accent wins; without one, whatever the skin paints a primary
        // button - which is what a user-installed Skin plugin repaints.
        var custom = editionColor();
        var measured = custom ? null : measure('btn btn-primary', colorOf);
        var primary = custom || (measured ? toHex(measured) : null);

        return {
            theme: skinName,
            dark: background ? luminance(background) < 0.5
                             : String(skinName || '').toLowerCase().indexOf('light') < 0,
            brEdition: !!commonData(SQConstants.getConstants).isBrazilianEdition,
            palette: primary ? { primary: primary } : undefined
        };
    }

    /*
     * The skin's stylesheet is injected as a <link> at the moment SKIN_CHANGED fires, so
     * measuring right away can still read the outgoing skin. Emit at once so the chat is
     * never left waiting, then measure again once the sheet has applied; the chat replaces
     * the payload and the state replay keeps the later one.
     */
    function emitSkin(skinName) {
        emit('skin', skinPayload(skinName));
        setTimeout(function () { emit('skin', skinPayload(skinName)); }, 400);
    }

    //- State -----------------------------------------------------------------------

    function licensePayload(data) {
        var license = data || $rootScope.license || {};

        return {
            code: license.code,
            email: license.email,
            isProVersion: license.isProVersion,
            isUltimateVersion: license.isUltimateVersion,
            isTrial: license.isTrial,
            isSpecialTrial: license.isSpecialTrial,
            sq4bAllowed: license.sq4bAllowed,
            volumeProfile: license.volumeProfile
        };
    }

    /*
     * The chat ships its own translations and picks them by locale code, so the code is
     * what it needs — the display title ("Cesky", "Chinese(Simplified)") is a file name,
     * not a locale. Both go over: `language` is the title the bridge has always sent and
     * other consumers may rely on, `languageCode` is the #flag short code from the top of
     * internal/langs/<title>.csv, which is what the chat resolves against.
     */
    function languagePayload(data) {
        var translations = window.top.commonData ? window.top.commonData.translations : null;
        if (translations instanceof Map) {
            translations = Array.from(translations);
        }

        var language = data || $rootScope.selectedLanguage || {};

        return {
            language: language.title || "English",
            // "cz" for Czech - the flag is not always the ISO code, the chat maps it.
            languageCode: language.flag || "en",
            translations: translations || []
        };
    }

    /*
     * SQConstants reads window.commonData, which the shell fills asynchronously — and this
     * service runs before that. Reading through here means a not-yet-loaded shell is an empty
     * object rather than a TypeError.
     */
    function commonData(getter) {
        try {
            return getter() || {};
        } catch (e) {
            return {};
        }
    }

    /*
     * Symbols the chat offers for a backtest. Mirrors AlgoWizardService.getSymbols() — its
     * first filter is dead code, the effective one is the second.
     */
    function getSymbols() {
        var data = commonData(SQConstants.getConstants).data;
        if (!data) return [];

        return data.filter(function (item) {
            return item.rows > 0 && item.show;
        });
    }

    /*
     * The license is the chat's identity — the AI backend authorises on the code carried in
     * every request. It arrives once, over the WebSocket, and AppService writes it to
     * $rootScope.license before it broadcasts LICENSE_CHANGED. Watching the scope rather than
     * only listening for the event means a license that landed before this service existed is
     * still picked up.
     */
    $rootScope.$watch('license.code', function (code) {
        if (code) emit('license', licensePayload());
    });

    SQEvents.addListener('SQAIChatIntegration', [
        SQEvents.get('LICENSE_CHANGED'),
        SQEvents.get('SKIN_CHANGED'),
        SQEvents.get('LANGUAGE_CHANGED'),
        SQEvents.get('DATA_CHANGED'),
        SQEvents.get('AW_BACKTEST_FINISHED'),
        SQEvents.get('APP_CONFIGS_CHANGED')
    ], function (event, data) {
        if (event == SQEvents.get('LICENSE_CHANGED')) {
            emit('license', licensePayload(data));

        } else if (event == SQEvents.get('APP_CONFIGS_CHANGED')) {
            // the intro video and link urls live in the license token; a chat mounted after this gets the new ones
            var codes = (data && data.codes) || [];
            if (CHAT_CONFIG_CODES.some(function (code) { return codes.indexOf(code) !== -1; })) {
                configPromise = null;
            }

        } else if (event == SQEvents.get('SKIN_CHANGED')) {
            lastSkinName = data.skin ? data.skin.name : null;
            emitSkin(lastSkinName);

        } else if (event == SQEvents.get('LANGUAGE_CHANGED')) {
            if (!window.top.commonData || !window.top.commonData.translations) {
                console.log("[aichat] Lang not loaded...");
                return;
            }

            emit('language', languagePayload(data));

            // The tiles and starters are translated in the catalog files, not in the chat, so
            // the new language needs its own file sent over.
            emitFeatures(featureLocale());

        } else if (event == SQEvents.get('DATA_CHANGED')) {
            emit('symbols', { symbols: getSymbols() });

        } else if (event == SQEvents.get('AW_BACKTEST_FINISHED')) {
            // AlgoWizard finished a backtest ({strategyName, backtestID}) — the chat
            // shows its "load backtest results" offer. Replayed like the other state
            // events, so a chat opened after the backtest still learns about it.
            emit('backtestFinished', data);
        }
    });

    /*
     * Live chat progress. The Java agent loop pushes one entry per tool call / result / interim note
     * over the common-message WebSocket (WebSocketConst.SQAI_PROGRESS, batched as an array). Every
     * raw message reaches a general listener, so we tap that and forward each step to the chat as a
     * 'progress' event. It is deliberately NOT a STATE_EVENT: progress is ephemeral, so it is
     * forwarded live and never replayed to a late subscriber.
     */
    SQWebSocketService.subscribeGeneral('sqaiChatProgress', function (msg) {
        var steps = msg && msg.sqaiProgress;
        if (!steps || !steps.length) return;
        for (var i = 0; i < steps.length; i++) {
            // The get_ui_context tool's request — internal plumbing between the server and this
            // window, not a chat step. squi gathers what the user is looking at (active module,
            // open project, Results-overlay strategy, selection) and POSTs it to /sqai/ui-context,
            // completing the future the blocked tool handler waits on. Never forwarded to the chat.
            if (steps[i] && steps[i].type === 'ui_context_request') {
                if (window.top.squi && window.top.squi.answerUiContext) {
                    window.top.squi.answerUiContext(steps[i].requestId);
                } else {
                    console.warn('[aichat] ui_context_request but window.squi.answerUiContext is missing');
                }
                continue;
            }
            // The get_algowizard_strategy tool's request - same plumbing as ui_context_request.
            if (steps[i] && steps[i].type === 'aw_strategy_request') {
                answerAlgoWizardStrategy(steps[i].requestId);
                continue;
            }
            emit('progress', steps[i]);
        }
    });

    //- Config ----------------------------------------------------------------------

    /*
     * The home-screen catalog: capability tiles + their conversation starters. Plain static
     * files (internal/web/SQAI/features/<product>/<locale>.json) rather than chat code, so the team can
     * add or reword features without touching the ai-chat build — edit, reload the panel, done.
     * They must not live under SQAI/chat/: copy-to-sqx.mjs wipes that folder on every deploy.
     *
     * One file per language, en.json the master. The chat carries no translations of the
     * catalog any more — what goes over the bridge is what the user reads — so the catalog is
     * reloaded and sent again whenever the app language changes ('features' state event).
     */

    // The chat's locale codes by the #flag short code of internal/langs/<title>.csv. Only Czech
    // differs: the flag is "cz", the locale "cs". An unknown flag reads the catalog in English.
    var FEATURE_LOCALES = {
        en: 'en', cz: 'cs', cs: 'cs', de: 'de', es: 'es', fr: 'fr', id: 'id',
        it: 'it', pl: 'pl', pt: 'pt', ru: 'ru', 'zh-CN': 'zh-CN', 'zh-TW': 'zh-TW'
    };

    // locale -> promise of the parsed file (null when it is missing or broken)
    var featureFiles = {};

    // One catalog folder per product, features/sqx/ and features/qdm/ (QProduct.featuresDir); the release ZIP ships only its own.
    var FEATURES_DIR = isSqx ? '/SQAI/features/sqx/' : '/SQAI/features/qdm/';

    function featureFile(locale) {
        if (!featureFiles[locale]) {
            featureFiles[locale] = fetch(FEATURES_DIR + locale + '.json', { cache: 'no-store' })  // the files change without redeploys - never serve them from HTTP cache
                .then(function (response) { return response.ok ? response.json() : null; })
                .catch(function () { return null; });
        }

        return featureFiles[locale];
    }

    function featureLocale() {
        var language = $rootScope.selectedLanguage || {};
        return FEATURE_LOCALES[String(language.flag || 'en')] || 'en';
    }

    /*
     * en.json owns the catalog — which tiles exist, in what order, with which icon, backend and
     * starter actions; a language file only has a say over the texts. So a tile or a starter
     * added to en.json and not yet translated shows in English instead of vanishing from that
     * language, and a translation left behind after a tile was removed cannot resurrect it.
     */
    var TEXT_FIELDS = ['title', 'shortDescription', 'description', 'inputPlaceholder'];

    function withTranslation(english, translation, fields) {
        var merged = angular.extend({}, english);

        if (translation) {
            fields.forEach(function (field) {
                var text = translation[field];
                if (typeof text === 'string' && text.trim()) merged[field] = text;
            });
        }

        return merged;
    }

    function indexBy(list, property) {
        var table = {};

        (list || []).forEach(function (item) {
            if (item && item[property]) table[item[property]] = item;
        });

        return table;
    }

    function mergeCatalog(english, translation) {
        var translatedFeatures = indexBy(translation, 'id');

        return (english || []).map(function (feature) {
            var other = translatedFeatures[feature.id];
            var merged = withTranslation(feature, other, TEXT_FIELDS);
            var translatedStarters = indexBy(other && other.starters, 'key');

            if (feature.starters) {
                merged.starters = feature.starters.map(function (starter) {
                    // A starter without a key cannot be matched across files, so it stays as
                    // en.json wrote it.
                    if (!starter || !starter.key) return starter;
                    return withTranslation(starter, translatedStarters[starter.key], ['label', 'prompt']);
                });
            }

            return merged;
        });
    }

    /* The catalog in one language, English filling every gap. Null when no file is readable. */
    function loadFeatures(locale) {
        return Promise.all([featureFile('en'), locale === 'en' ? null : featureFile(locale)])
            .then(function (files) {
                var english = files[0];
                var translation = files[1];

                if (!english) return translation || null;

                return {
                    features: mergeCatalog(english.features, translation && translation.features)
                };
            });
    }

    /*
     * Load the catalog for `locale` and push it to the chat. A state event, so a chat that
     * mounts later has the last one replayed to it, and a language switch simply sends another.
     */
    function emitFeatures(locale) {
        return loadFeatures(locale).then(function (catalog) {
            if (catalog && catalog.features && catalog.features.length) {
                emit('features', {
                    language: locale,
                    features: catalog.features
                });
            }

            return catalog;
        });
    }

    /*
     * Only what the chat reads: platformType, backendUrls, development and symbols in the
     * library, wizardConfig for the strategy form. Not the editor's config object — the chat
     * has no use for money-management methods or block tag clouds, and copying them over
     * would tie its contract to the editor's again.
     */
    // A failed side request must not take the whole config down: the chat opens without it.
    function optional(request) {
        return Promise.resolve(request).then(null, function (e) {
            console.warn('[aichat] optional config request failed', e);
            return {};
        });
    }

    // The AlgoWizard route exists in SQX only; QDM has no editor and no wizard form.
    function loadAlgoWizardConfig() {
        if (!isSqx) return Promise.resolve({});
        return optional(BackendService.httpRequest('/algowizard/getConfig', null));
    }

    function loadConfig() {
        if (!configPromise) {
            configPromise = Promise.all([
                loadAlgoWizardConfig(),
                emitFeatures(featureLocale()),
                BackendService.httpRequest('/main/appconfigs', null),
                // the aichat-* backend urls, served by the Q backend itself so both shells have them
                optional(BackendService.httpRequest('/sqai/config', null))
            ]).then(function (results) {
                var awConfig = results[0] || {};
                var featuresJson = results[1];
                var appConfigs = (results[2] && results[2].configs) || {};
                var sqaiConfig = results[3] || {};

                return {
                    // The chat's platform family stays SQ in both shells (CT is AlgoCloud);
                    // hostApp tells a wrapper which shell it is in.
                    platformType: "SQ",
                    hostApp: hostApp,
                    development: !!window.top.developmentMode,
                    wizardConfig: awConfig.wizardConfig,
                    backendUrls: awConfig.aiChatBackendUrls || sqaiConfig.backendUrls || undefined,
                    volumeProfile: awConfig.volumeProfile || undefined,
                    symbols: getSymbols(),
                    // Missing or unreadable files -> undefined; the chat falls back to its
                    // built-in defaults instead of an empty home screen. The same catalog goes
                    // over as a 'features' state event, which is what a language switch updates
                    // — this is only the one the chat opens with.
                    features: (featuresJson && featuresJson.features) || undefined,
                    // The AI introduction video the home screen shows above the tiles: the
                    // ai_intro_video app config of the license token (a YouTube link), none
                    // when the token has no such code. The terms of use gate is driven by
                    // GET/POST /sqai/terms, not by the catalog.
                    introVideoUrl: appConfigs[INTRO_VIDEO_CONFIG] || undefined,
                    // The quick introduction, pricing and terms of use pages of the chat's home
                    // screen and footers - app configs too; a missing one has no link in the chat.
                    links: {
                        introduction: appConfigs[LINK_CONFIGS.introduction] || undefined,
                        pricing: appConfigs[LINK_CONFIGS.pricing] || undefined,
                        terms: appConfigs[LINK_CONFIGS.terms] || undefined,
                        privacy: appConfigs[LINK_CONFIGS.privacy] || undefined
                    }
                };
            });
        }

        return configPromise;
    }

    //- Requests from the chat ------------------------------------------------------

    /*
     * The one place SQX hands a chat request to the AlgoWizard editor. The editor answers
     * internal events with a value, and returns its errors in the payload instead of throwing,
     * because the call crosses an iframe boundary — so unpack that into a rejection here and
     * let the chat see one kind of failure.
     */
    function editorRequest(action, args) {
        var editorInterface = window.top.awEditorInterface;
        var handler = editorInterface && editorInterface.internalEventHandler;

        if (typeof handler !== 'function') {
            return Promise.reject(new Error(L.tsq("The AlgoWizard editor is not loaded yet.")));
        }

        return Promise.resolve(handler(action, args || {})).then(function (result) {
            if (result && result.error) throw new Error(result.error);
            return result;
        });
    }

    /* Bring the AlgoWizard module to the front — the editor iframe only exists once the
     * module has been opened, so an editor request made from another tab must switch first
     * (the user also SEES the strategy they are loading from). Resolves when the editor
     * bridge is up; the poll covers a cold iframe that is still booting. */
    function openAlgoWizard() {
        if (getApp("AlgoWizard") == null) {
            return Promise.reject(new Error(L.tsq("The AlgoWizard module is not available.")));
        }
        switchToApp("AlgoWizard");
        broadcastEvent(SQEvents.get('APP_SWITCHED'), "AlgoWizard");
        showResults(false);

        return new Promise(function (resolve, reject) {
            var deadline = Date.now() + 8000;
            (function poll() {
                var iface = window.top.awEditorInterface;
                if (iface && typeof iface.internalEventHandler === 'function') return resolve();
                if (Date.now() > deadline) {
                    return reject(new Error(L.tsq("The AlgoWizard editor is not loaded yet.")));
                }
                setTimeout(poll, 200);
            })();
        });
    }

    /* Open the strategy the chat built in AlgoWizard. Same sequence as the databank's
     * "Edit strategy" action (ResultsDatabankActions/tools/edit/editStrategy). */
    function sendToAlgoWizard(args) {
        if (!args.strategyXML) {
            return Promise.reject(new Error(L.tsq("There is no strategy to send to AlgoWizard.")));
        }

        if (getApp("AlgoWizard") == null) {
            return Promise.reject(new Error(L.tsq("The AlgoWizard module is not available.")));
        }

        switchToApp("AlgoWizard");
        broadcastEvent(SQEvents.get('APP_SWITCHED'), "AlgoWizard");
        showResults(false);

        $injector.get("AlgoWizardService").editorAction("loadStrategy", {
            strategyXML: args.strategyXML,
            lastSettings: args.lastSettingsXML,
            lastSettingsXML: args.lastSettingsXML,
            fileName: args.fileName,
            // The editor asks the user to name (or overwrite) the strategy before
            // loading. Editors older than 2.0.1 ignore the flag and load directly.
            askName: true
        });

        return Promise.resolve({ success: true });
    }

    // The strategy in the editor's selected tab, for the get_algowizard_strategy tool. No picker
    // (a dialog would outlive the tool's wait) and no module switch (an editor that was never
    // opened holds no strategy). getStrategySource answers with pseudocode only; the exact XML
    // is captured from the /sourcecode/print call it makes through AlgoWizardService.
    function readAlgoWizardStrategy() {
        if (!isSqx || getApp("AlgoWizard") == null) {
            return Promise.reject(new Error("AlgoWizard is not available in this application."));
        }
        var iface = window.top.awEditorInterface;
        if (!iface || typeof iface.internalEventHandler !== 'function') {
            return Promise.reject(new Error("the AlgoWizard editor is not loaded - no strategy is open in it. "
                + "Ask the user to open the strategy in AlgoWizard first."));
        }
        var aw = $injector.get("AlgoWizardService");
        var capture = aw.captureStrategyXML();
        return editorRequest("getStrategySource", {}).then(function (res) {
            capture.stop();
            var name = (res && res.strategyName) || "";
            return {
                strategyName: name,
                pseudoCode: (res && res.pseudoCode) || "",
                lastSettingsXML: (res && res.lastSettingsXML) || "",
                strategyXML: capture.get() || "",
                backtestID: aw.getLastBacktestID(name) || ""
            };
        }, function (e) {
            capture.stop();
            throw e;
        });
    }

    function answerAlgoWizardStrategy(requestId) {
        readAlgoWizardStrategy().then(null, function (e) {
            return { error: (e && e.message) || String(e) };
        }).then(function (answer) {
            return BackendService.httpRequest('/sqai/ui-context',
                { requestId: requestId, context: JSON.stringify(answer) }, 'POST');
        }).catch(function (e) {
            console.error('[aichat] answering aw_strategy_request failed', e);
        });
    }

    function request(action, args) {
        args = args || {};

        try {
            return dispatch(action, args);
        } catch (e) {
            // A synchronous throw would cross the iframe boundary as an exception in the
            // chat's own frame; the chat only handles rejections.
            console.error("[aichat] request '" + action + "' failed", e);
            return Promise.reject(e instanceof Error ? e : new Error(String(e)));
        }
    }

    // The editor and AlgoCloud requests need SQX; in QDM they reject with one message.
    var SQX_ONLY_REQUESTS = ['getStrategySource', 'sendToAlgoWizard', 'getBacktestResults', 'openInAlgoCloud'];

    function dispatch(action, args) {
        if (!isSqx && SQX_ONLY_REQUESTS.indexOf(action) >= 0) {
            return Promise.reject(new Error(L.tsq("This is available in StrategyQuant X only.")));
        }

        switch (action) {
            // Pseudocode + settings of a strategy in the editor; askWhich lets the
            // editor show its picker dialog when more strategies are open. Switches the
            // app to the AlgoWizard tab first — the editor iframe may not exist yet, and
            // the user should see the strategy they are loading from.
            case "getStrategySource": return openAlgoWizard().then(function () {
                return editorRequest("getStrategySource", { askWhich: true });
            });

            case "sendToAlgoWizard": return sendToAlgoWizard(args);

            // Raw backtest results; the editor's picker dialog chooses which backtest.
            case "getBacktestResults": return editorRequest("getBacktestResults", { askWhich: true });

            case "showNotification":
                window.top.sqNotices.addNotice(args.type || "info", args.message);
                return Promise.resolve();

            case "openLink":
                AppService.openBrowser(args.link);
                return Promise.resolve();

            // The report view's "Open in AlgoCloud": args is the report's strategy locator
            // ({file} or {name, databank, strategy}) or a raw {strategyXML, lastSettingsXML,
            // strategyName}. The host uploads, confirms the warnings and opens the browser; a
            // refusal is shown as an SQX error here and resolves as {error}, so the chat does
            // not toast it a second time.
            case "openInAlgoCloud":
                return AlgoCloudService.open(args);

            default:
                console.error("[aichat] Unknown request '" + action + "'", args);
                return Promise.reject(new Error("Unknown aichatInterface request '" + action + "'"));
        }
    }

    //- The interface ---------------------------------------------------------------

    window.top.aichatInterface = {
        version: 1,

        /** What the app is. Resolves once, independently of the AlgoWizard editor. */
        getConfig: function () {
            return new Promise(function (resolve, reject) {
                loadConfig().then(resolve, reject);
            });
        },

        /** Everything the chat has missed, for a subscriber that is only interested once. */
        getState: function () {
            return angular.copy(lastState);
        },

        /**
         * Subscribe to skin / language / license / symbols / backtestFinished. The last
         * payload of each is replayed synchronously on registration. Returns the
         * unsubscribe function.
         */
        registerHandler: function (handler) {
            if (typeof handler !== 'function') return angular.noop;

            handlers.push(handler);

            STATE_EVENTS.forEach(function (eventName) {
                if (lastState[eventName] !== undefined) {
                    try {
                        handler(eventName, lastState[eventName]);
                    } catch (e) {
                        console.error("[aichat] replay failed for '" + eventName + "'", e);
                    }
                }
            });

            return function () {
                var index = handlers.indexOf(handler);
                if (index >= 0) handlers.splice(index, 1);
            };
        },

        /** Ask SQX to do something. Always a promise; failures reject with a message. */
        request: request
    };

    // Seed whatever is already known — the chat may register after all of these happened.
    if ($rootScope.license && $rootScope.license.code) emit('license', licensePayload());
    if ($rootScope.selectedLanguage) emit('language', languagePayload());

    /*
     * The saved skin is in SQConstants.getSettings(), which loads asynchronously — at service
     * init it is usually still empty, and SKIN_CHANGED only fires when the user changes skin.
     * A one-shot read here would therefore never deliver the startup skin and the chat would
     * fall back to its dark default even in a light SQX. Watch the settings until the skin
     * appears instead; SKIN_CHANGED keeps handling the changes after that.
     */
    var lastSkinName = null;

    var unwatchSkin = $rootScope.$watch(function () {
        return commonData(SQConstants.getSettings).skin;
    }, function (skin) {
        if (!skin) return;
        lastSkinName = skin;
        emitSkin(skin);
        unwatchSkin();
    });

    /*
     * The edition's accent arrives asynchronously (/main/customizations) and changes again
     * whenever the user switches language, because the customization is chosen per language.
     * Watching the value covers both, and the CUSTOMIZATION_CHANGED broadcast as well - it is
     * the same $rootScope field that every path writes.
     */
    $rootScope.$watch(function () {
        return $rootScope.currentEditionCustomization && $rootScope.currentEditionCustomization.edition_color;
    }, function (color, previous) {
        if (color === previous) return;   // the initial call, nothing has changed yet
        emitSkin(lastSkinName || commonData(SQConstants.getSettings).skin);
    });
});
