angular.module("app").directive("settingsTabs", function ($rootScope, $timeout, AppService, L, SQConstants, SQEvents, SQWebSocketService) {
    return {
        restrict: 'E',
        replace: true,
        templateUrl: "../app/directives/settingsTabs/settingsTabs.html",
        scope: {
            instance: '=',
        },
        link: function (scope, element, attrs) {

            scope.instance.clear = function () {
                scope.onClose();
                scope.instance.tabs.length = 0;
            }

            scope.instance.selectTab = function (dataItem) {
                var tabs = scope.instance.tabs;

                someSettingsChanged = someSettingsChanged || (activeTab && activeTab.shouldSaveSettings && activeTab.shouldSaveSettings());

                activeTab = null;

                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].dataItem == dataItem) {
                        tabs[i].active = true;

                        activeTab = tabs[i];
                    } else {
                        tabs[i].active = false;
                    }
                }

                setSaveTimer();
                updateButtons();

                if (scope.instance.onSelectTab) {
                    scope.instance.onSelectTab(activeTab);
                }
            }

            scope.instance.getActiveTab = function () {
                var tabs = scope.instance.tabs;

                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].active) {
                        return tabs[i];
                    }
                }
            }

            scope.instance.switchToNextTab = function () {
                var tabs = scope.instance.tabs;

                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].active && i < tabs.length - 1) {
                        scope.onSelectTab(tabs[i + 1]);
                        return;
                    }
                }
            }

            scope.instance.switchToPrevTab = function () {
                var tabs = scope.instance.tabs;

                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i].active && i > 0) {
                        scope.onSelectTab(tabs[i - 1]);
                        return;
                    }
                }
            }

            scope.instance.switchToTab = function (tabTitle) {
                var tab = getItem(scope.instance.tabs, 'title', tabTitle);
                if (tab) {
                    scope.onSelectTab(tab);
                } else {
                    console.error("Tab '" + tabTitle + "' doesn't exist");
                }
            }

            scope.onSelectTab = function (tab) {
                var tabs = scope.instance.tabs;

                someSettingsChanged = someSettingsChanged || (activeTab && activeTab.shouldSaveSettings && activeTab.shouldSaveSettings());

                activeTab = tab;

                if (tab) {
                    tab.active = true;
                    tab.currentText = tab.help.replace(/<br\/?>/gm, '\r\n');
                }

                for (var i = 0; i < tabs.length; i++) {
                    if (tabs[i] != tab) {
                        tabs[i].active = false;
                    }
                }

                setSaveTimer();
                updateButtons();

                if (scope.instance.onSelectTab) {
                    scope.instance.onSelectTab(activeTab);
                }
            }

            scope.onClose = function () {
                SQEvents.notifyListeners(SQEvents.get('SETTINGS_CLOSE'));
            }

            scope.onHelp = function (tab) {
                if (!tab.helpURL) {
                    return;
                }

                AppService.openHelp(tab.helpURL);
            }

            function waitUntilInitialized() {
                if (scope.$$phase) { //$digest or $apply running
                    $timeout(function () {
                        waitUntilInitialized();
                    }, 0, false);
                } else {
                    if (scope.instance.afterInit) {
                        scope.instance.afterInit();
                    }
                }
            }

            function getProgressInfo(data) {
                if (arrayEmpty(data.ProjectStatuses)) {
                    return;
                }

                for (var i = 0; i < data.ProjectStatuses.length; i++) {
                    var projectStatus = data.ProjectStatuses[i];

                    if (projectStatus.projectName == AppService.getProject()) {
                        return projectStatus;
                    }
                }
            }

            function getSettingNames(errorString) {
                var settingNames = [];
                var errors = errorString.split("\n");

                for (var i = 0; i < errors.length; i++) {
                    var error = errors[i];

                    var endIndex = error.indexOf(", Field: ");
                    var endIndex2 = error.indexOf(", Error: ");

                    if (error.indexOf("Setting: ") == 0 && (endIndex > 0 || endIndex2 > 0)) {
                        var settingName = error.substr(9, endIndex > 0 ? endIndex - 9 : endIndex2 - 9);
                        settingNames.push(settingName);
                    }
                }

                return settingNames;
            }

            function updateButtons() {
                if (activeTab) {
                    for (var i = 0; i < tabs.length; i++) {
                        var tab = tabs[i];

                        if (tab.title == activeTab.title) {
                            scope.prevButtonLabel = i > 0 ? ("< " + tabs[i - 1].title) : null;
                            scope.nextButtonLabel = i < tabs.length - 1 ? (tabs[i + 1].title + " >") : null;
                            break;
                        }
                    }
                } else {
                    scope.nextButtonLabel = null;
                    scope.prevButtonLabel = null;
                }
            }

            function onWebSocketData(data) {
                var progressInfo = getProgressInfo(data);

                if (progressInfo && progressInfo.error) {
                    if (progressInfo.errorType == 50) { //fatal error
                        var settingNames = getSettingNames(progressInfo.error);

                        if (settingNames && settingNames.length > 0) {
                            for (var i = 0; i < settingNames.length; i++) {
                                var settingName = settingNames[i];

                                for (var t = 0; t < scope.instance.tabs.length; t++) {
                                    var tab = scope.instance.tabs[t];

                                    if (tab.title == settingName) {
                                        tab.hasErrors = true;
                                    }
                                }
                            }
                        }
                    }
                }
            }

            var destroyStatusWatch = scope.$watch(function () {
                return $rootScope.project.state;
            }, function (newValue, oldValue) {
                if (newValue == scope.projectStates.running) {
                    for (var t = 0; t < scope.instance.tabs.length; t++) {
                        var tab = scope.instance.tabs[t];
                        tab.hasErrors = false;
                    }
                }
            });

            function getDisplayedTabs() {
                var tabs = [];
                for (var i = 0; i < scope.instance.tabs.length; i++) {
                    if (scope.instance.tabs[i].display) {
                        tabs.push(scope.instance.tabs[i]);
                    }
                }


                return tabs;
            }

            function onEvent(event, data) {
                if (event == SQEvents.get('SETTINGS_TAB_RELOAD')) {
                    if (data == 'all') {
                        scope.template = AppService.getTaskTemplateName();
                    }
                } else if (event == SQEvents.get('SETTINGS_CLOSE')) {
                    closeSettings(data);
                } else if (event == SQEvents.get('APP_PANEL_CHANGED')) {
                    if (data != 'settings') {
                        return;
                    }

                    var tabs = getDisplayedTabs();
                    if (!activeTab || (activeTab && !getItem(tabs, 'dataItem', activeTab.dataItem))) {
                        scope.onSelectTab(tabs[0]);
                    }
                } else if (event == SQEvents.get('LANGUAGE_CHANGED')) {
                    translateHeaders();
                } else if (event == SQEvents.get('PROJECT_STARTED')) {
                    //dont send next XML update request, everything is saved already
                    if (activeTab && activeTab.onSettingsSaved) {
                        activeTab.onSettingsSaved();
                    }

                    dontSaveOnClose = true;

                    setSaveTimer();
                } else return;

                try {
                    scope.$digest();
                } catch (err) {}
            }

            function translateHeaders() {
                for (var i = 0; i < scope.instance.tabs.length; i++) {
                    scope.instance.tabs[i].translatedTitle = L.tsq(scope.instance.tabs[i].title);
                }
            }

            function closeSettings(callback) {
                if (dontSaveOnClose) {
                    dontSaveOnClose = false;
                    return;
                }

                someSettingsChanged = someSettingsChanged || (activeTab && activeTab.shouldSaveSettings && activeTab.shouldSaveSettings());

                $('.sqn-settings-body').fadeOut('fast');
                $('.sqn-dashboard').removeClass('settings-pane-shown');

                AppService.settingsOpen = false;

                resetSaveTimer();
                saveSettings();
                setSaveTimer();
            }

            function saveSettings(callback) {
                if (someSettingsChanged) {
                    AppService.updateTaskXML().then(function(result) {
                        if(result && result.data && result.data.simpleSettings){
                            SQEvents.notifyListeners(SQEvents.get("TASK_INFO_UPDATE"), {
                                simpleSettings: result.data.simpleSettings
                            });
                        } else {
                            SQEvents.notifyListeners(SQEvents.get("TASK_INFO_UPDATE"));
                        }

                        for (var i = 0; i < scope.instance.tabs.length; i++) {
                            var tab = scope.instance.tabs[i];
                            if (tab && tab.onSettingsSaved) {
                                tab.onSettingsSaved();
                            }
                        }

                        someSettingsChanged = false;

                        if (callback) callback();
                    });
                } else {
                    if (callback) callback();
                }
            }

            function resetSaveTimer() {
                if (saveTimer) {
                    clearTimeout(saveTimer);
                }
            }

            function setSaveTimer() {
                resetSaveTimer();

                saveTimer = setTimeout(function () {
                    saveSettings();
                    setSaveTimer();
                }, 10000);
            }

            scope.$on('$destroy', function () {
                destroyStatusWatch();
                SQEvents.removeListener(listenerId);
            });

            scope.instance.taskChanged = function () {
                scope.taskName = AppService.getTask().title;

                try {
                    scope.$digest();
                } catch (err) {}
            }


            //init tabs
            var activeTab = false;
            var tabs = scope.instance.tabs;
            var saveTimer;
            var dontSaveOnClose = false;
            var someSettingsChanged = false;

            scope.isTaskManager = AppService.isTaskManager();
            scope.taskName = AppService.getTask().title;

            scope.projectConfigs = SQConstants.getConstants().projectConfigs;
            scope.projectStates = SQConstants.getConstants().runningStatuses;
            scope.template = AppService.getTaskTemplateName();

            scope.prevButtonLabel = '';
            scope.nextButtonLabel = '';

            waitUntilInitialized();

            $('.sqn-settings-body').on('setting-closed', function () {
                scope.onClose();
            });

            SQWebSocketService.subscribeGeneral("SettingsTabs-" + window.appConfig.appCode, onWebSocketData);

            var listenerId = "SettingsTabs";
            SQEvents.addListener(listenerId, [
                SQEvents.get('SETTINGS_TAB_RELOAD'),
                SQEvents.get('SETTINGS_CLOSE'),
                SQEvents.get('APP_PANEL_CHANGED'),
                SQEvents.get('LANGUAGE_CHANGED'),
                SQEvents.get('PROJECT_STARTED')
            ], onEvent);
        }
    };
});
