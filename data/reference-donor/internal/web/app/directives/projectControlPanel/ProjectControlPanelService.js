angular.module('app').service('ProjectControlPanelService', function ($rootScope, $timeout, $q, BackendService, sqPlugin, SQEvents, SQConstants, AppService, SQWebSocketService, DatabankService, L) {
    this.start = function (projectName, callback, data) {
        if (startPromise !== null) return;

        startPromise = $timeout(function () {          //wait for last xml modifications
            var task = AppService.getTask();
            if (task && (task.type == "Retest" || task.type == "AutomaticPortfolioBuilder")) {
                saveSelectedStrategiesIntoXML();
            }

            start(projectName, callback, data);

        }, 100, false);
    }

    function start(projectName, callback, data) {
        var startData = { 'projectName': projectName };

        if(projectName === AppService.getProject()){
            let projectConfig = AppService.getProjectConfig();

            if(projectConfig){
                startData.projectXML = xmlToString(projectConfig);

                if(AppService.getTask().type){
                    startData.taskXMLFile = AppService.getTask().taskXMLFile;
                    startData.taskXML = xmlToString(AppService.getTaskConfig());
                }
            }
        }
        
        angular.extend(startData, data);

        BackendService.sendRequest('project/start', startData, callback, 'POST');
        startPromise = null;
    }

    function saveSelectedStrategiesIntoXML() {
        var settingsObj = AppService.getTaskConfig();
        var selectedStrategiesObj = createChild(settingsObj, "SelectedStrategies", AppService.xmlDoc);

        removeAllChildren(selectedStrategiesObj);

        if (DatabankService.getRetestSelected()) {
            var selectedStrategies = DatabankService.getStrategiesToRetest();
            if (selectedStrategies == null) {
                return;
            }

            for (var i = 0; i < selectedStrategies.length; i++) {
                var strategyName = selectedStrategies[i];
                if (!strategyName) continue;

                var elStrategy = createChild(selectedStrategiesObj, "Strategy", AppService.xmlDoc, true);
                setNodeValue(elStrategy, strategyName, AppService.xmlDoc);
            }
        }
    }

    this.stop = function (projectName, inProjectList) {
        BackendService.sendRequest('project/stop', { 'projectName': projectName });

        if (!inProjectList) {
            showEngine(projectName);
        }
    }

    this.pause = function (projectName, inProjectList) {
        BackendService.sendRequest('project/pause', { 'projectName': projectName });

        if (!inProjectList) {
            showEngine(projectName);
        }
    }

    this.resume = function (projectName, inProjectList) {
        BackendService.sendRequest('project/resume', { 'projectName': projectName });

        if (!inProjectList) {
            showEngine(projectName);
        }
    }

    this.setEngineData = function (data) {
        engineData = data;

        for (var i = 0; i < listeners.length; i++) {
            listeners[i].callback(data);
        }
    }

    this.getEngineData = function () {
        return engineData;
    }

    this.addListener = function (id, callback) {
        var listener = getItem(listeners, 'id', id);
        if (!listener) {
            listener = { id: id, callback: callback };
            listeners.push(listener);
        }
        else {
            console.error("Engine status listener with id '" + id + "' already exists");
        }
    }

    this.removeListener = function (id) {
        removeItem(listeners, 'id', id);
    }

    function showEngine(projectName) {
        if (AppService.getActivePanel() == "dashboard") {
            return;
        }

        if (projectName != AppService.getProject()) {
            AppService.setProject(projectName, function () {
                AppService.switchToPanel('dashboard');
            });
        } else {
            AppService.switchToPanel('dashboard');
        }
    }

    function onEvent(event, data) {
        if (event == SQEvents.get('START_PROJECT')) {
            instance.start(AppService.getProject(), null, data);
        }
    }
    $(document).on('keydown', function (e) {
        if (window.appConfig.product == window.top.activeApp) {
            if (e.ctrlKey && e.keyCode == 32) {
                e.preventDefault();
                var appObj = getItem(window.parent.apps, "appCode", window.appConfig.product);
                if (appObj.running) {
                    instance.stop(AppService.getProject(), false);
                    sqNotices.addNotice('success', L.tsq("Stopping project."));
                } else {
                    instance.start(AppService.getProject(), null, null);
                    sqNotices.addNotice('success', L.tsq("Starting project."));
                }

                return false;
            }
        }
    });

    var instance = this;

    var engineData;
    var listeners = [];
    var startPromise = null;

    this.projectsStatuses = [];
    this.projectStates = SQConstants.getConstants().runningStatuses;

    var listenerId = "ProjectControlPanelService";
    SQEvents.addListener(listenerId, [SQEvents.get('START_PROJECT')], onEvent);
});
