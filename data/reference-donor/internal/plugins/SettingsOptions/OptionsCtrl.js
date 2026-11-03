angular.module('app.settings').controller('OptionsCtrl', function ($rootScope, $scope, $q, $timeout, $element, SQConstants, OptionsService, SQEvents, AppService) {
    function init(){
        $scope.isAutoRetestTask = AppService.getTask().type == 'AutomaticRetest';

        $q.all([pgInitDeferred.promise, OptionsService.list()]).then(function(){
            $scope.config.propertyGridInstance.createFromXML(OptionsService.parameters, function() {
                OptionsService.applySettings($scope.config);

                //enable/disable session option according to the engine used
                var dataElem = AppService.getCurrentTaskTabSettings("Data");
                if (dataElem) {
                    var setupsElem = getChildElement(dataElem, 'Setups', true);
                    if (setupsElem) {
                        var setupElems = getChildElements(setupsElem, 'Setup');
                        if (setupElems.length > 0) {
                            let engine = getAttrValue(setupElems[0], 'engine');
                            enableOptionsBasedOnEngine(engine);
                        }
                    }
                }
                
                if(sessionsUpdatedBeforInit) {
                    onSessionsChanged(sessionsUpdatedBeforInit);
                }

                $timeout(function() { 
                    loaded = true;
                    oldSession = getSession();
                }, 0, false);
            }); 
        });
    }

    function getSession(){
        return $scope.config.propertyGridInstance.getPropertyValueByKey("Session");
    }

    $scope.afterPGInit = function() {
        pgInitDeferred.resolve();
    }
    
    $scope.onPGChange = function(data){
        if(!loaded){
            return;
        }
        
        onSettingsChange();

        var newSession = getSession();
        if(newSession != oldSession){
            SQEvents.notifyListeners(SQEvents.get('SETTINGS_SESSION_CHANGED'), newSession);
            oldSession = newSession;
        }
    }

    $scope.getName = function(){
        return $scope.config.separatedSettings ? "SL" : "SL/PT";
    }

    function onSessionsChanged(newSessions) {
        _onSessionsChanged(newSessions, "Session");
        _onSessionsChanged(newSessions, "MarketOpenSession");
    }

    function _onSessionsChanged(newSessions, propertyName) {
        if(propertyName === "Session") {
            sessionsUpdatedBeforInit = newSessions;
        }

        if(!$scope.config.propertyGridInstance.getValues) return;

        var sessionOption = $scope.config.propertyGridInstance.getPropertyByKey(propertyName);
        if(!sessionOption){
            return;
        }

        sessionOption.options.length = 0;
        var curOptionExists = false;
        
        for(var i=0; i<newSessions.length; i++){
            var sessionName = newSessions[i].name;

            sessionOption.options.push({ name : sessionName, value : sessionName });

            if(sessionOption.value == sessionName){
                curOptionExists = true;
            }
        }

        if(!curOptionExists){
            sessionOption.value = newSessions[0] ? newSessions[0].name : "";
        }

        $scope.config.propertyGridInstance.setPropertyByKey(propertyName, sessionOption);
    }

    function enableOptionsBasedOnEngine(engine) {
        if(!$scope.config.propertyGridInstance.getValues) return;

        var engineKey = SQConstants.getEngineKey(engine);

        let properties = $scope.config.propertyGridInstance.getProperties();
        for (let i = 0; i < properties.length; i++) {
            if(engineKey == "SP" || engineKey === "SA") {
                properties[i].hidden = !properties[i].key.startsWith("Picker") && properties[i].key!="StoreChartData" && properties[i].key!="LimitOver";

                if(engineKey === "SA" && STOCKPICKER_ONLY_KEYS.indexOf(properties[i].key) >= 0) {
                    properties[i].hidden = true;

                    // a broker filter left over from a Stockpicker setup could drop the one symbol a single-asset test runs on
                    if(properties[i].key === "PickerBroker") {
                        properties[i].value = NO_BROKER_FILTER;
                    }
                }

                //V Builderu bude pro kazdou z techto volem ta volba navyse Randomly generated, a v ostatnich tascich tam bude volba navyse "From strategy".
                if(properties[i].options && properties[i].options.length>0 && properties[i].key.startsWith("Picker")) {
                    if(AppService.getTask().type == 'Build') {
                        for (let o = 0; o < properties[i].options.length; o++) {
                            let option = properties[i].options[o];

                            if(option.name==1) {//From strategy
                                properties[i].options.splice(o, 1);
                                break;
                            }
                        }
                    } else {
                        for (let o = 0; o < properties[i].options.length; o++) {
                            let option = properties[i].options[o];

                            if(option.name==0) {//Randomly generated
                                properties[i].options.splice(o, 1);
                                break;
                            }
                        }
                    }
                }
            } else {
                properties[i].hidden = properties[i].key.startsWith("Picker") || properties[i].key=="LimitOver";
            }
        }

        if(engine != "Stockpicker" && engine != "Single-asset cloud strategy") {
            checkOption(engine, engineKey, "Session", "No Session");
            checkOption(engine, engineKey, "MarketOpenSession", "No Session");
            checkOption(engine, engineKey, "ReservedBars", 50);
            checkOption(engine, engineKey, "RealisticGapsHandling", false);
            checkOption(engine, engineKey, "UseInitialSLPT", false);
        }
    }

    // Engines that offer Session / Reserved bars / Use initial SL & PT, by engine KEY.
    // Keys rather than display names on purpose: the Java side gates these same three options with
    // @ForEngine("MC,TS,NT") and the two gates must agree. NinjaTrader8 was added to both for issue #162
    // - Trading Hours templates are its sessions, BarsRequiredToTrade is its reserved bars, and it is the
    // one engine besides EasyLanguage shipping UseInitialSLPT_code.tpl (GEN-55 fixed the annotation in
    // 2026-08 but not this list, so the option stayed unreachable here until #162).
    // Adding an engine here without adding it to @ForEngine - or the reverse - either hides an option
    // that is honoured or offers one that is not.
    var SESSION_AND_WARMUP_ENGINE_KEYS = ["TS", "MC", "NT"];

    // Engines that offer Realistic gaps handling, by engine KEY - the Java side gates it with
    // @ForEngine("MT4,MT5"). Only the MetaTrader simulators fill at the requested price over a gap;
    // JForex fills at the real price anyway and the bar-close engines never read the option.
    var REALISTIC_GAPS_ENGINE_KEYS = ["MT4", "MT5"];

    // Picker options the Single-asset engine does not offer - the Java side gates them with
    // @ForEngine("SP"). A single-asset strategy always holds at most one position per direction
    // (the engine sets the limit to 1 whatever is stored here) and it tests one given symbol, so
    // there is no universe for a broker to filter.
    var STOCKPICKER_ONLY_KEYS = ["PickerMaxOpenPositionsLong", "PickerMaxOpenPositionsShort", "PickerBroker"];

    // BrokerManager.NO_BROKER on the Java side
    var NO_BROKER_FILTER = "No filter";

     function checkOption(engine, engineKey, propertyName, value){
        var option = $scope.config.propertyGridInstance.getPropertyByKey(propertyName);
        if(!option){
            return;
        }
        
        //-----------------------------------------------
        if(propertyName === "MarketOpenSession") {
            if(engine.startsWith("MetaTrader5")) {
                option.hidden = false;
            } else {
                option.hidden = true;
                option.value = value;
            }

        //-----------------------------------------------
        } else if(propertyName === "RealisticGapsHandling") {
            if(REALISTIC_GAPS_ENGINE_KEYS.indexOf(engineKey) >= 0){
                option.hidden = false;
            } else {
                option.hidden = true;
                option.value = value;
            }

        //-----------------------------------------------
        } else {
            if(SESSION_AND_WARMUP_ENGINE_KEYS.indexOf(engineKey) >= 0){
                option.hidden = false;
            } else {
                option.hidden = true;
                option.value = value;
            }
        }
    }

    $scope.onCustomSettingsChange = function(){
        onSettingsChange();
    }

    //- Event Handlers --------------------------------------------------------------

    $scope.tab.shouldSaveSettings = function(){
        var shouldSaveSettings = settingsChanged;
        settingsChanged = false;
        return shouldSaveSettings;
    }

    function onSettingsChange(){
        settingsChanged = true;
        OptionsService.saveConfig($scope.config);
    }

    var destroyConfigWatch = $scope.$watch('config', function(newValue, oldValue){
        if(loaded) {
            onSettingsChange();
        }
    }, true);
    
    function onEvent(event, data){
        if(event == SQEvents.get('SETTINGS_TAB_RELOAD')) {
            if($scope.tab.display && (data == $scope.tab.title || data == 'all')) {
                loaded = false;
                init();
            }
        }
        else if(event == SQEvents.get('SETTINGS_TAB_ACTIVE')){
            var active = data.title == $scope.tab.title;
            if(active && !loaded){
                init();
            }
    
            watchersHandler.onActivated(active);
        }
        else if(event == SQEvents.get('SESSIONS_CHANGED')){
            onSessionsChanged(data);
            OptionsService.list(true);
        }
        else if(event == SQEvents.get('MAIN_SETUP_CHANGED')){
            enableOptionsBasedOnEngine(data.engine);
        }
        else if(event == SQEvents.get('TRADING_OPTIONS_RELOAD')) {
            if(loaded) {
                //console.log('Reloading trading options'); 
                loaded = false;
                init();
            }
        }
        else return;
        
        try { $scope.$digest(); } catch(er) {}
    }
    
    $scope.$on('$destroy', function(){
        destroyConfigWatch();
        SQEvents.removeListener(listenerId);
    });

    var loaded = false;
    var pgInitDeferred = $q.defer();
    var oldSession;
    var engines = SQConstants.getConstants().engines;
    var sessionsUpdatedBeforInit = null;

    var settingsChanged = false;

    $scope.valueTypes = OptionsService.valueTypes;

    $scope.config = {
        propertyGridInstance : {},
        useCustomSettings: false  
    };
    
    $scope.isAutoRetestTask = AppService.getTask().type == 'AutomaticRetest';

    var listenerId = "OptionsCtrl";
    SQEvents.addListener(listenerId, [
        SQEvents.get('SETTINGS_TAB_ACTIVE'), 
        SQEvents.get('SETTINGS_TAB_RELOAD'), 
        SQEvents.get('SESSIONS_CHANGED'), 
        SQEvents.get('MAIN_SETUP_CHANGED'),
        SQEvents.get('TRADING_OPTIONS_RELOAD')
    ], onEvent);

    var watchersHandler = new WatchersHandler($($element));
    $timeout(function(){ watchersHandler.onActivated(false); }, 0, false);

});
