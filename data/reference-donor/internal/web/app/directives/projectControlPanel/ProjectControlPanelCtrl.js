angular.module('app').controller('ProjectControlPanelCtrl', function ($scope, $rootScope, $q, ProjectControlPanelService, SQEvents, SQConstants, AppService, SQWebSocketService, L) {
    console.log("ProjectControlPanel controller initialized");

    $scope.isPortfolioMaster = AppService.isPortfolioMaster();

    // Kebab of the project name for per-project data-testids on the Custom Projects list
    // (isolate scope doesn't inherit the global kebab helper). toKebabCase is a global.
    $scope.kebab = function (s) { return toKebabCase(s); };

    $scope.start = function () {
        var beforeStartPromises = [];

        SQEvents.notifyListeners(SQEvents.get('PROJECT_BEFORE_START'), { 
            projectName: $scope.projectName, 
            addPromise : function(promise){
                if(promise) {
                    beforeStartPromises.push(promise);
                }
            } 
        });

        $q.all(beforeStartPromises).then(function(result){
            ProjectControlPanelService.start($scope.projectName, function () {
                SQEvents.notifyListeners(SQEvents.get('PROJECT_STARTED'), { projectName: $scope.projectName });
            });
        });
    }

    $scope.stop = function () {
        ProjectControlPanelService.stop($scope.projectName, $scope.fixedProject);
    }

    $scope.pause = function () {
        if ($scope.pauseBtnTitle == L.tsq("Pause")) {
            ProjectControlPanelService.pause($scope.projectName, $scope.fixedProject);
        } 
        else {
            ProjectControlPanelService.resume($scope.projectName, $scope.fixedProject);
        }
    }

    function updateButtons(status) {
        status = parseInt(status)

        switch (status) {
            case $scope.projectStates.loading:
            case $scope.projectStates.pausing:
            case $scope.projectStates.stopping:
                $scope.startBtnEnabled = false;
                $scope.stopBtnEnabled = false;
                $scope.pauseBtnEnabled = false;
                break;

            case $scope.projectStates.paused:
            case $scope.projectStates.running:
                $scope.startBtnEnabled = false;
                $scope.stopBtnEnabled = true;
                $scope.pauseBtnEnabled = true;
                break;

            case $scope.projectStates.finished:
                if (AppService.isTaskManager()) {
                    return;
                }

                $scope.startBtnEnabled = true;
                $scope.stopBtnEnabled = false;
                $scope.pauseBtnEnabled = false;
                break;

            case $scope.projectStates.beforeStart:
            case $scope.projectStates.stopped:
            case $scope.projectStates.error:
                $scope.startBtnEnabled = true;
                $scope.stopBtnEnabled = false;
                $scope.pauseBtnEnabled = false;
        }
    }

    function changeProjectStatus(status) {
        if (status == $scope.projectStates.paused) {
            $scope.pauseBtnTitle = L.tsq("Resume");
        }
        else if (status == $scope.projectStates.running) {
            $scope.pauseBtnTitle = L.tsq("Pause");
        }

        updateMainWindowAppObj(status); //updates app object on main window (sets running flag)
        updateButtons(status);

        //update $rootScope variable only if this control panel belongs to currently selected project (custom projects fix)
        if ($rootScope.project.state != status && $scope.projectName == AppService.getProject()) {
            $rootScope.project.state = status;
            $rootScope.$applyAsync();
        }
    }

    function updateMainWindowAppObj(status) {
        var appObj = getItem(window.parent.apps, "appCode", window.appConfig.product);
        if (appObj) {
            switch (status) {
                case $scope.projectStates.running:
                case $scope.projectStates.pausing:
                case $scope.projectStates.paused:
                case $scope.projectStates.stopping:
                    appObj.running = true;
                    break;
                default:
                    appObj.running = false;
            }
        }
        else console.error("App obj of product '" + window.appConfig.product + "' not found");
    }

    function getCallbackId() {
        var fixed = $scope.fixedProject ? "-fixed" : "";

        return $scope.projectName + fixed + "-ProjectControlPanel";
    }

    function getProgressTitle(action) {
        switch (action) {
            case "save": return L.tsq("Saving strategies");
            case "delete": return L.tsq("Removing strategies");
            case "type-change": return L.tsq("Changing databank type");
            case "max-strategies-change": return L.tsq("Updating databank");
            case "retest": return L.tsq("Copying strategies to retester");
            case "saveEA": return L.tsq("Saving EA");
            default: return L.tsq("Action - %s", [action]);
        }
    }

    function onProgressUpdate(channelData) {
        if (channelData.action == 'load') return;
        if (channelData.action || channelData.percent != 0) {
            var title = getProgressTitle(channelData.action);
            $rootScope.setProgressInfo(title, title, channelData.percent==-1 ? "infinite" : channelData.percent);
            $rootScope.updateProgress(channelData.percent==-1 ? "infinite" : channelData.percent, channelData.info);
        }

        if (channelData.error) {
            $rootScope.showError(channelData.error);
        }
    }

    function onEngineUpdate(channelData) {
        if (channelData.projectName != $scope.projectName) {
            console.error("Invalid subscription detected. ProjectControlPanel.onEngineUpdate() - different project", channelData.projectName, $scope.projectName);
            return;
        }

        if (channelData.error) {
            if (channelData.errorType == 50) { //fatal error
                if(channelData.errorInfo != "Stopped"){
                    $rootScope.showErrorModal("Error", channelData.errorInfo + "\n" + channelData.error, true);
                    $rootScope.showError(channelData.errorInfo);
                }
            } else {
                $rootScope.showError(channelData.error);
            }
        }

        changeProjectStatus(channelData.runningStatus);

        if (channelData.runningStatus == $scope.projectStates.beforeStart) {
            $scope.progressPercent = 0;
        }
        else {
            $scope.progressPercent = AppService.isTaskManager() || channelData.infiniteProgress ? 100 : channelData.progressPercent;
        }

        $scope.progressInfo = channelData.info;

        try { $scope.$digest(); } catch (err) { }

        ProjectControlPanelService.setEngineData(channelData);

        if (window.appConfig.product != "TASKMANAGER") {      //task manager handles this in TMProjectsCtrl
            displayAppMenuProgress(channelData.runningStatus, channelData.infiniteProgress ? 0 : channelData.progressPercent);
        }
    }

    function displayAppMenuProgress(status, percent) {
        switch (parseInt(status)) {
            case $scope.projectStates.running:
                //case $scope.projectStates.loading:
                window.parent.document.getElementById(window.appConfig.product + "-menuprogress").style.display = "block";
                //window.parent.document.getElementById(window.appConfig.product+"-menuprogress-span").style.width = percent + "%";
                break;
            default:
                window.parent.document.getElementById(window.appConfig.product + "-menuprogress").style.display = "none";
                break;
        }
    }

    function isTMProjectList() {
        return ($scope.fixedProject === true || $scope.fixedProject === "true") && window.appConfig.product == "TASKMANAGER";
    }

    function onEvent(event, data) {
        if (event == SQEvents.get('APP_PROJECT_CHANGED')) {
            if ($scope.fixedProject) { //taskmanager multi project control
                return;
            }

            SQWebSocketService.unsubscribe($scope.projectName, channels.progress, getCallbackId());
            SQWebSocketService.unsubscribe($scope.projectName, channels.engine, getCallbackId());

            $scope.projectName = data;

            if (data != null) {
                SQWebSocketService.subscribe($scope.projectName, channels.progress, getCallbackId(), onProgressUpdate);
                SQWebSocketService.subscribe($scope.projectName, channels.engine, getCallbackId(), onEngineUpdate);
            }
        }
        else if (event == SQEvents.get('PROJECT_DISABLE_START')) {
            $scope.startBtnEnabled = false;
            data.then(function () {
                $scope.startBtnEnabled = true;
            });
        }
        else return;

        try { $scope.$digest(); } catch (er) { }
    }

    $scope.$on("$destroy", function () {
        if (!isTMProjectList()) {
            SQWebSocketService.unsubscribe($scope.projectName, channels.progress, getCallbackId());
            SQWebSocketService.unsubscribe($scope.projectName, channels.engine, getCallbackId());
        }
        SQEvents.removeListener(getCallbackId());
    });

    var channels = SQConstants.getConstants().channels;

    if (!$scope.projectName) {
        $scope.projectName = AppService.getProject();
    }

    $scope.projectStates = ProjectControlPanelService.projectStates;
    $scope.pauseBtnTitle = L.tsq("Pause");
    $scope.progressInfo = "";

    changeProjectStatus($scope.projectStates.beforeStart);

    if (isTMProjectList()) {
        if ($scope.instance) {
            $scope.instance.updateStatus = function (runningStatus) {
                changeProjectStatus(runningStatus);
            }
        }
    }
    else {
        SQWebSocketService.subscribe($scope.projectName, channels.progress, getCallbackId(), onProgressUpdate);
        SQWebSocketService.subscribe($scope.projectName, channels.engine, getCallbackId(), onEngineUpdate);

        SQWebSocketService.subscribeGeneral("ProjectControlPanelCtrl", function (channelData) {
            if(channelData.ExitApp){
                AppService.updateTaskXML();   
            }
        });
    }

    SQEvents.addListener(getCallbackId(), [SQEvents.get('APP_PROJECT_CHANGED'), SQEvents.get('PROJECT_DISABLE_START')], onEvent);
});
