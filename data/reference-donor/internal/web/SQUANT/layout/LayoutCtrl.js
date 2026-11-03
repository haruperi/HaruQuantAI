angular.module('app.layout').controller('LayoutCtrl', function($rootScope, $scope, $timeout, $state, sqPlugin, AppService, SQEvents, SQConstants, SQWebSocketService, L, SkinService, BackendService, LayoutService, Results2Service, CustomizationService) {

    $rootScope.allCustomizations = $rootScope.allCustomizations || [];
    $rootScope.currentEditionCustomization = $rootScope.currentEditionCustomization || null;
    $scope.currentEditionCustomization = $rootScope.currentEditionCustomization;

    CustomizationService.reload($scope);
    CustomizationService.initFrameInjection();

    /*
     * ========================================================================
     * ============= Communication interface with Results2 ===================
     * ========================================================================
     */
    //If it is true, then the Results2 is displayed
    $scope.results2 = SQConstants.getSettings().results2;
    if($scope.results2) {
        Results2Service.initCommunicationInterface();
    }

    //=========================================================================

    $scope.openBrowser = AppService.openBrowser;

    $scope.getScreenName = function() {
        return $state.current.data.title;
    }

    function loadMenuItems() {
        for (var i = 0; i < $scope.apps.length; i++) {
            var navigationItem = $scope.apps[i];

            addApp(navigationItem);

            if (navigationItem.menu == 'top') { //apps on top menu
                $scope.topMenuItems.push(navigationItem);

            } else { //apps on left menu

                var sectionIndex = navigationItem.section;

                if (!$scope.itemSections[sectionIndex]) {
                    while ($scope.itemSections.length <= sectionIndex) {
                        $scope.itemSections.push({
                            position: $scope.itemSections.length,
                            navigationItems: []
                        });
                    }
                }

                $scope.itemSections[sectionIndex].navigationItems.push(navigationItem);
            }
        }
        
        try {
            $scope.$digest();
        } catch (err) {}
    }

    $scope.switchToApp = function(navigationItem) {
        if (navigationItem.onlyInPro && !$rootScope.license.isProVersion) {
            return;
        }

        if (navigationItem.appCode == 'SQEDITOR') {
            LayoutService.openCodeEditor(function(data) {
                if (data.url) {
                    window.open(window.location.protocol + "//" + window.location.hostname + ":" + data.url, '_blank');
                }
            });

            return;

        } else if (navigationItem.appCode == 'DEBUGCONSOLE') {
            LayoutService.openDebugConsole(function(data) {
                if (data.url) {
                    window.open(window.location.protocol + "//" + window.location.hostname + ":" + data.url, '_blank');
                }
            });

            return;
        } else if (navigationItem.appCode == 'HELP') {
            LayoutService.openHelpDialog(function(data) {
                if (data.url) {
                    window.open(window.location.protocol + "//" + window.location.hostname + ":" + data.url, '_blank');
                }
            });

            return;
        }

        var app = getApp(navigationItem.appCode);

        if (!app.loaded) {
            if (navigationItem.url) {
                $('#' + navigationItem.iframeId)[0].src = navigationItem.url;
            }
            if (navigationItem.iframeId == 'algowizard-frame') {
                getApp("AlgoWizard").loaded = true;
            }
            if (navigationItem.iframeId == 'sqxbusiness-frame') {
                getApp("SQXBUSINESS").loaded = true;
            }
        }

        switchToApp(navigationItem.appCode);
    }

    window.sendAppSwitchedEvent = function(appCode) {
        SQEvents.notifyListeners(SQEvents.get('APP_SWITCHED'), appCode);
    }

    $scope.switchToCodeEditor = function() {
        hidePopup('#snippetsErrorModal');
        $scope.switchToApp({ appCode: 'SQEDITOR' });
    }

    $scope.loadNext = function() {
        if (appsPreloaded) return;

        var navigationItem = getNextApp();
        if (!navigationItem) return;

        if (!appsPreloaded && loadIndex == (appsToPreload.length-1)) {
            appsPreloaded = true;
        }

        if(!navigationItem.url) return;

        console.log("Loading app", navigationItem.appCode, navigationItem.url);

        var iframeElem = $('#' + navigationItem.iframeId)[0];
        if (iframeElem) {
            iframeElem.src = navigationItem.url;
        }

        if (appsPreloaded) {
            appsLoaded();
        }
    }

    function appsLoaded() {
        console.log("All apps have been loaded...")

        if (SQConstants.getConstants().isFirstRun && !SQConstants.getConstants().isBrazilianEdition) {
            $scope.initSettings.language = getItem(L.languages, "title", SQConstants.getSettings().language || "English");

            console.debug("First run, displaying init settings dialog...")

            $timeout(function() {
                showPopup("#initSettingsDialog");
            });
        } else {
            // $rootScope.showBenchmark(true); //called from squtils

            console.debug("Applying skin to BUSINESS module...")

            if (window.parent.SQ4BSkinChanged) {
                window.parent.SQ4BSkinChanged(SkinService.selectedSkin);
            }
        }

        if(window.top.dataTrialExpiresSoon) {
            $timeout(function() {
               showPopup("#dataTrialPopup");
            }, 10000, false);
        }
    }

    function getNextApp() {
        return appsPreloaded ? $scope.apps[loadIndex++] : getItem($scope.apps, 'appCode', appsToPreload[loadIndex++]);
    }

    $scope.closeInitSettings = function(save) {
        if (save) {
            L.downloadLanguage($scope.initSettings.language);
            SkinService.changeSkin($scope.initSettings.skin);
        }

        hidePopup("#initSettingsDialog");

        if ($scope.initSettings.IntroWalkthrough) {
            window.parent.broadcastEvent('show-intro-tutorial');
        }
    }

    $scope.onMenuResize = function() {
        $scope.menuSize++;
        if ($scope.menuSize == 3) $scope.menuSize = 0;
    }

    $scope.openLinkDocumentation = function() {
        AppService.openBrowser('https://strategyquant.com/doc/', function() {});
    }

    $scope.openLinkSupport = function() {
        AppService.openBrowser('https://strategyquant.com/contactus/', function() {});
    }

    $scope.openLinkBugs = function() {
        AppService.openBrowser('https://roadmap.strategyquant.com', function() {});
    }

    $scope.onAbout = function() {
        window.parent.broadcastEvent(SQEvents.get('OPEN_ABOUT_DIALOG'));
    }

    $scope.goToCustomProject = function() {
        hidePopup('#customProjectNotifPopup');
        switchToApp('TASKMANAGER');
    }

    $scope.broker = SQConstants.getConstants().broker;
    $scope.isBrazilianEdition = SQConstants.getConstants().isBrazilianEdition;

    $rootScope.brEdition = "";
    if (SQConstants.getConstants().isBrazilianEdition) {
        $rootScope.brEdition = "br-edition";
    }

    window.parent.brEdition = SQConstants.getConstants().isBrazilianEdition;

    //- Event Handlers --------------------------------------------------------------

    function onWebSocketData(args) {
        if (args.SnippetsCompilationFailed) {
            $scope.SnippetsCompilationFailed = args.SnippetsCompilationFailed.errors;

            showPopup('#snippetsErrorModal');
        }

        if (args.customProjectNotification) {
            let data = args.customProjectNotification;

            $scope.customProjectNotification = L.tsq("Project '%s' has reached task '%s'.", [data.projectName, data.taskName]);

            $scope.customProjectName = data.projectName;
            $scope.customTaskName = data.taskName;
            $scope.customProjectPaused = data.projectPaused;

            try {
                $scope.$digest();
            } catch (err) {}

            showPopup('#customProjectNotifPopup');
        }

        if (args.saveAllProgress) {
            var info = "";

            if (args.saveAllProgress.currentCount < 0) {
                info = L.tsq("Loading strategies to save...");
            } else {
                info = L.tsq("Saving strategies... %d/%d", [args.saveAllProgress.currentCount, args.saveAllProgress.totalCount]);
            }

            $rootScope.updateSavingProgress(args.saveAllProgress.progress, info, function() {
                BackendService.sendRequest("main/stopStrategiesSaving");
            }, args.saveAllProgress.isAppExit);

            if (args.saveAllProgress.error) {
                $rootScope.showError(args.saveAllProgress.error);
            } else if (args.saveAllProgress.progress == 100) {
                $rootScope.showSuccess("Strategies saved");
            }
        }

        if (args.notification) {
            let data = args.notification;

            if (data.message) {
                $rootScope.showErrorModal(data.title, data.message);

            } else if (data.error) {
                $rootScope.showError(data.error);

            } else if (data.success) {
                $rootScope.showSuccess(data.success);
            }
        }

        if (args.appStatusChanged) {
            let data = args.appStatusChanged;

            if (data.finished) {
                var element = window.document.getElementById(data.productCode + "-menuprogress");
                if (element) element.style.display = "none";
            }

        }

        if (args.PaymentDialogOrderId) {
            var orderId = args.PaymentDialogOrderId.licenceOrderId;
            console.error("here is order id", orderId);
            $.ajax({
                type: "POST",
                url: "http://api.strategyquant.com/fastspring/order",
                data: { id: orderId },
                success: function(dataReceived) {
                    var dataJson = JSON.parse(dataReceived);
                    if ("license" in dataJson) {
                        window.parent.broadcastEvent(SQEvents.get('OPEN_ABOUT_DIALOG'), { update: true, enterNewLicence: dataJson.license });
                    }
                }
            });
        }
    }

    function tryShowUltimateModules(data) {
        //show SQXBUSINESS
        var app = getItem($scope.apps, 'appCode', "SQXBUSINESS");
        if (app) {
            app.hidden = false; //!data.isUltimateVersion;
            $scope.$evalAsync();
        }

        //hide MARKETPLACE when the license server sent marketplace=0 for this user
        var marketplaceApp = getItem($scope.apps, 'appCode', "MARKETPLACE");
        if (marketplaceApp) {
            marketplaceApp.hidden = !!data && data.marketplace === false;
            $scope.$evalAsync();
        }
    }

    //- Initialization --------------------------------------------------------------

    $scope.customProjectNotification = null;
    $scope.customProjectName = null;
    $scope.customTaskName = null;
    $scope.customProjectPaused = false;

    $scope.footerCustomText = SQConstants.getConstants().global.footerCustomText;

    $scope.onlyInProTitle = SQConstants.ONLY_IN_PRO;

    $scope.apps = sqPlugin.getPlugins("NavigationPlugin");

    var loadIndex = 0;
    var appsPreloaded = false;

    $scope.itemSections = [];
    $scope.topMenuItems = [];
    $scope.menuSize = 0; // 0,1,2: sizes of menu; 0=default

    $scope.skins = SkinService.skins;
    $scope.languages = L.languages;
    $scope.initSettings = {
        skin: $scope.skins[0],
        language: $rootScope.selectedLanguage,
        help: L.tsq('You will be able to change these options later in global menu on top right'),
        IntroWalkthrough: true
    };

    window.onAppLoaded = $scope.loadNext;

    loadMenuItems();

    $timeout(function() {
        if ($scope.apps.length) {
            switchToApp($scope.apps[0].appCode);
        }

        //delayed by timeout, because angular breaks while creating all iframes at once on init
        tryShowUltimateModules($rootScope.license);
    });

    $timeout(function() {
        $('.sq4-mainmenu>ul li a.disabled').tooltip({
            "trigger": "hover",
        });
        $('ul.icons-system li a.disabled').tooltip({
            "trigger": "hover",
        });
    }, 0, false);


    $scope.fullscreen = function() {
        if ($rootScope.chromiumBrowser) {
            BackendService.sendRequest("main/maximize");
        } else {
            var elem = document.documentElement;

            if (elem.requestFullscreen) {
                elem.requestFullscreen();
            } else if (elem.mozRequestFullScreen) { /* Firefox */
                elem.mozRequestFullScreen();
            } else if (elem.webkitRequestFullscreen) { /* Chrome, Safari and Opera */
                elem.webkitRequestFullscreen();
            } else if (elem.msRequestFullscreen) { /* IE/Edge */
                elem.msRequestFullscreen();
            }
        }
    }

    function updateFbIconOccurence() {
        if (navigator.onLine) {
            $(".fb-like").show();
            setTimeout(function() {
                $(".fb-like").attr('src', function(i, val) {
                    return val;
                });
            }, 1000);
        } else {
            $(".fb-like").hide();
        }
    }

    window.addEventListener('online', updateFbIconOccurence);
    window.addEventListener('offline', updateFbIconOccurence);
    updateFbIconOccurence();

    window.showTutorialPopup = function(url) {
        $('#home-iframe-modal iframe').attr('src', url)
        showPopup("#home-iframe-modal");
    }

    window.top.showPurchaseDialog = function(productString) {
        window.open("https://strategyquant.com/pricing/", '_blank');
    }

    SQEvents.addListener("LayoutCtrl-" + window.appConfig.appCode, [SQEvents.get('LICENSE_CHANGED')], function(event, data) {
        tryShowUltimateModules(data);
        CustomizationService.reload($scope);
    });
    SQEvents.addListener("LayoutCtrl-" + window.appConfig.appCode, [SQEvents.get('LANGUAGE_CHANGED')], function(event, data) {
        CustomizationService.updateCurrentCustomization($scope);
    });

    SQWebSocketService.subscribeGeneral("LayoutCtrl-" + window.appConfig.appCode, onWebSocketData);

});
