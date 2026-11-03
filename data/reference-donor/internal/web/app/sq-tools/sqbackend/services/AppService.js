angular.module('app').service('AppService', function ($rootScope, $q, $timeout, $injector, BackendService, SQEvents, SQConstants, sqPlugin, SQWebSocketService, L) {

    if (("Chart" in window) && ("ChartDataLabels" in window)) {
        Chart.plugins.unregister(ChartDataLabels);
        
        Chart.helpers.merge(Chart.defaults.global.plugins.datalabels, {
            display: 'auto',
            font: {
                size: 11
            }
        });

        const verticalLinePlugin = {
            getLinePosition: function (chart, pointIndex) {
                const meta = chart.getDatasetMeta(0); // first dataset is used to discover X coordinate of a point
                const data = meta.data;
                return data[pointIndex] ? data[pointIndex]._model.x : -1;
            },
            renderVerticalLine: function (chartInstance, pointIndex) {
                const lineLeftOffset = this.getLinePosition(chartInstance, pointIndex);
                if(lineLeftOffset==-1) return;
                
                const scale = chartInstance.scales['y-axis-0'];
                const context = chartInstance.chart.ctx;

                // render vertical line
                context.beginPath();
                context.strokeStyle = '#ff0000';
                context.moveTo(lineLeftOffset, scale.top);
                context.lineTo(lineLeftOffset, scale.bottom);
                context.stroke();
            },

            afterDatasetsDraw: function (chart, easing) {
                if (chart.config.lineAtIndex) {
                    chart.config.lineAtIndex.forEach(pointIndex => this.renderVerticalLine(chart, pointIndex));
                }
            }
        };

        Chart.plugins.register(verticalLinePlugin);
    }

    this.setFirstTask = function(){
        let elTasks = getChildElement(instance.xmlConfig.find("Project")[0], "Tasks");
        let elTask = getChildElement(elTasks, "Task");
        
        let taskType = getAttrStringValue(elTask, "type");
        let taskTypeOrig = null;
        if(taskType=='OptimizeConfigurable') {
            taskType = "Optimize";
            taskTypeOrig = 'OptimizeConfigurable';
        }

        let taskName = getAttrStringValue(elTask, "name");
        let taskXMLFile = getAttrStringValue(elTask, "taskXMLFile");

        instance.setTask(taskType, taskName, null, taskTypeOrig, taskXMLFile);
    }

    this.setTask = function (taskType, taskName, taskTitle, taskTypeOrig, taskXMLFile) {
        window.appConfig.task.type = taskType;
        window.appConfig.task.typeOrig = taskTypeOrig;
        
        window.appConfig.task.name = taskName;
        window.appConfig.task.title = taskTitle || taskName;
        window.appConfig.task.taskXMLFile = taskXMLFile;

        let taskXML = SQConstants.getTaskConfig(instance.getProject(), taskXMLFile, false);
        instance.taskXMLConfig = xmlToObject(taskXML);
        instance.taskXMLDoc = getXMLDoc(taskXML);

        if (window.appConfig.product != 'SQUANT') {       //broadcast change to SQUANT'S AppService
            window.parent.broadcastEvent(SQEvents.get('SETTINGS_TASK_CHANGED'), window.appConfig.task);
        }

        SQEvents.notifyListeners(SQEvents.get('SETTINGS_TASK_CHANGED'));
        publishSelection();

        $timeout(function () {
            if (taskType) SQEvents.notifyListeners(SQEvents.get('SETTINGS_TAB_RELOAD'), 'all');
        }, 0, false);
    }

    this.getTask = function () {
        return window.appConfig.task;
    }

    this.setProject = function (projectName, callback) {
        console.log("Setting project to " + projectName);

        instance.projectName = projectName;
        window.appConfig.project = projectName;
        $rootScope.project.name = projectName;
        publishSelection();

        if(!projectName) return;

        loadConfig(function () {
            instance.setFirstTask();

            if (window.appConfig.product != 'SQUANT') {
                window.parent.broadcastEvent(SQEvents.get('APP_PROJECT_CHANGED'), projectName);     //broadcast change to SQUANT'S AppService
                SQEvents.notifyListeners(SQEvents.get('APP_PROJECT_CHANGED'), projectName);
                SQEvents.notifyListeners(SQEvents.get('RELOAD_DATABANKS'), { action: "setProject" });
                registerDbChannelHandler(projectName);
            }

            publishSelection();
            callback();
        });
    }

    this.getProject = function () {
        return instance.projectName;
    }

    this.getAppConfig = function () {
        return window.appConfig;
    }

    this.getProduct = function () {
        return window.appConfig.product;
    }

    this.setDatabank = function (databankTab) {
        instance.databank = databankTab;
        publishSelection();

        if (window.appConfig.product != 'SQUANT') {       //broadcast change to SQUANT'S AppService
            window.parent.broadcastEvent(SQEvents.get('DATABANK_CHANGED'), databankTab);
        }
    }

    this.getDatabank = function (databankTab) {
        return instance.databank;
    }

    this.onAppSwitched = function () {
        publishSelection();
        window.parent.broadcastEvent(SQEvents.get('APP_PROJECT_CHANGED'), instance.getProject());
        window.parent.broadcastEvent(SQEvents.get('DATABANK_CHANGED'), instance.getDatabank());
    }

    this.setSelectedStrategies = function (strategies) {
        instance.strategiesSelected = strategies;
        publishSelection();

        if (window.appConfig.product != 'SQUANT') {       //broadcast change to SQUANT'S AppService
            window.parent.broadcastEvent(SQEvents.get('STRATEGY_SELECTED'), strategies);
        }
    }

    this.getSelectedStrategies = function () {
        return instance.strategiesSelected;
    }

    this.initXMLObjects = function () {
        var product = window.appConfig.product;

        if (product == 'RESULTS' || product == 'SQMANAGER' || product == 'SQUANT' || product == 'HOME' || product == 'QDM') {
            var xml = "<Results></Results>"

            instance.xmlConfig = xmlToObject(xml);
            instance.xmlDoc = getXMLDoc(xml);

            return;
        }

        if(!this.projectName || this.projectName == 'TaskManager') {
            return;
        }

        let projectConfig = SQConstants.getProjectConfig(this.projectName);
        if(!projectConfig){
            console.error("Config for project " + this.projectName + " not found");
            this.xmlConfig = null;
            this.xmlDoc = null;
            return;
        }

        this.xmlConfig = xmlToObject(projectConfig);
        this.xmlDoc = getXMLDoc(projectConfig);

        instance.setFirstTask();
    }

    this.getTaskXMLConfig = function(){
        return instance.xmlConfig;
    }

    this.getProjectConfig = function () {
        if (!instance.xmlConfig) {
            return null;
        }

        return instance.xmlConfig.find("Project")[0];
    }

    this.getTaskConfig = function () {
        if (!instance.taskXMLConfig) {
            return null;
        }
        return instance.taskXMLConfig.find("Settings")[0];
    }

    this.getCurrentTaskTabSettings = function(tabConfigName){
        return getChildElement(instance.getTaskConfig(), tabConfigName);
    }

    this.getTaskTabSettings = function(projectName, taskXMLFile, tabConfigName){
        var settingsObj = SQConstants.getTaskConfig(projectName, taskXMLFile, true);
        return getChildElement(settingsObj, tabConfigName);
    }

    this.reloadConfig = function (callback) {
        loadConfig(callback);
    }

    // The task settings changed backend-side (sqx-project engine / set_task_config sent
    // project/updateTaskXML with notifyUI=true): drop the cached project config, re-fetch it
    // and re-render every settings tab of the CURRENT task - the same effect "Apply config"
    // has, without pushing anything back to the server.
    this.reloadTaskFromServer = function (taskXMLFile, callback) {
        var projectName = instance.getProject();
        if (!projectName) return;

        SQConstants.setProjectConfigObj(projectName, null);
        loadConfig(function () {
            var task = window.appConfig.task || {};
            if (task.taskXMLFile && (!taskXMLFile || task.taskXMLFile === taskXMLFile)) {
                instance.setTask(task.type, task.name, task.title, task.typeOrig, task.taskXMLFile);
            }
            SQEvents.notifyListeners(SQEvents.get('RELOAD_DATABANKS'));
            if (callback) callback();
        });
    }


    function loadConfig(callback) {
        if (!instance.projectName || instance.projectName == 'TaskManager') {
            return;
        }

        var savedConfig = SQConstants.getProjectConfigObj(instance.projectName);
        if(savedConfig){
            setProjectConfig(savedConfig);

            if (callback) {
                callback();
            }
            return;
        }

        return BackendService.sendRequest('/project/getXMLConfig', { projectName: instance.projectName }, function (result) {
            setProjectConfig(result.config);

            if (callback) {
                callback();
            }
        }, 'POST');
    }

    function setProjectConfig(projectConfig){
        instance.xmlConfig = xmlToObject(projectConfig.xml);
        instance.xmlDoc = getXMLDoc(projectConfig.xml);

        var projectElem = instance.xmlConfig.find('Project')[0];
        if (!projectElem) {
            $rootScope.showError("Config XML error", "Corrupted XML - element 'Project' not found");
            console.error("Project XML config is corrupted. No Project element found.");
            return;
        }

        console.log("Loaded XML config of project " + instance.projectName);

        SQConstants.setProjectConfigObj(instance.projectName, projectConfig);
    }

    this.resetTaskXML = function (configName, callback) {
        var args = {
            projectName: instance.projectName,
            taskName: window.appConfig.task.name,
            configName: configName
        }

        BackendService.sendRequest('/project/resetTaskConfig', args, function (result) {
            instance.xmlConfig = xmlToObject(result.xmlConfig);
            instance.xmlDoc = getXMLDoc(result.xmlConfig);

            SQConstants.setProjectConfig(instance.getProject(), result.xmlConfig);

            instance.taskXMLConfig = xmlToObject(result.taskXML);
            instance.taskXMLDoc = getXMLDoc(result.taskXML);

            SQConstants.setTaskConfig(instance.getProject(), result.taskXMLFile, result.taskXML);

            SQEvents.notifyListeners(SQEvents.get('SETTINGS_TAB_RELOAD'), 'all');
            SQEvents.notifyListeners(SQEvents.get("TASK_INFO_UPDATE"), { simpleSettings: result.simpleSettings });

            if (result.success) {
                $rootScope.showSuccess("Task settings reset to default");
            } else {
                $rootScope.showError(result.error);
            }

            if (callback) callback();
        }, 'POST');
    }

    this.loadXMLTemplate = function (fileName, sampleName, callback, dontShowSuccessMessage) {
        var args = {
            taskName: window.appConfig.task.name,
            taskType: window.appConfig.task.type,
            fileName: fileName,
            sampleName: sampleName
        }

        BackendService.sendRequest('/project/getTemplateConfig', args, function (result) {
            $rootScope.resolveResources(result.xmlConfig, result.resourcesXML, SQConstants.getConstants().projectResourceActionTypes.loadTaskConfig, function(data){
                if(data.taskXML){
                    replaceTaskConfig(data.taskXML, callback, dontShowSuccessMessage);
                }
                else if(data.loadAsIs){
                    replaceTaskConfig(result.xmlConfig, callback, dontShowSuccessMessage);
                }
            });
        }, 'POST');
    }

    function replaceTaskConfig(newConfigXML, callback, dontShowSuccessMessage){
        var settingsObj = instance.getTaskConfig();
        var blocksObj = getChildElement(settingsObj, "Blocks");

        var xmlConfig = xmlToObject(newConfigXML);
        var newTaskObj = xmlConfig.find("Task")[0];
        var newBlocksObj = xmlConfig.find("Blocks")[0];

        if (!newTaskObj && !newBlocksObj) {
            $rootScope.showError("Loading failed. Required settings are missing in XML config");
            return;
        }

        var isBlocksConfig = !newTaskObj;

        if(isBlocksConfig){
            blocksObj.parentNode.replaceChild(newBlocksObj, blocksObj);
        }
        else {
            let elTaskCurrent = getTask(instance.getProjectConfig(), instance.getTask());
            elTaskCurrent.setAttribute("templateFile", getAttrStringValue(newTaskObj, "templateFile", ""));
            elTaskCurrent.setAttribute("sampleName", getAttrStringValue(newTaskObj, "sampleName", ""));
            
            instance.updateProjectXML();

            let newTaskXML = xmlToString(getChildElement(newTaskObj, "Settings"));
            instance.taskXMLConfig = xmlToObject(newTaskXML);
            instance.taskXMLDoc = getXMLDoc(newTaskXML);
        }

        instance.updateTaskXML().then(function (result) {
            if(result){     //result may be null if config was not changed
                SQEvents.notifyListeners(SQEvents.get('SETTINGS_TAB_RELOAD'), isBlocksConfig ? 'Building blocks' : 'all');
                SQEvents.notifyListeners(SQEvents.get("TASK_INFO_UPDATE"), { simpleSettings: result.data.simpleSettings });

                if (result.success) {
                    if (!dontShowSuccessMessage) {
                        $rootScope.showSuccess("Template config loaded");
                        let awEditor = $injector.get("AlgoWizardService");
                        if(awEditor){
                            awEditor.reloadCustomBlocks();
                        }
                    }
                } else {
                    $rootScope.showError(result.data.error);
                }
            }

            if (callback) callback();
        });
    }

    this.updateTemplateConfig = function () {
        let elTask = xmlToObject(xmlToString(getTask(instance.getProjectConfig(), instance.getTask()))).find("Task")[0];    //clone task element
        elTask.appendChild(xmlToObject(xmlToString(instance.getTaskConfig())).find("Settings")[0]); //append cloned settings element
        
        var xmlConfig = xmlToString(elTask);

        BackendService.sendRequest('/project/updateTemplateConfig', {
            xmlConfig: xmlConfig
        }, function (result) {
            $rootScope.showSuccess(result.success);
        }, 'POST');
    }

    this.getTaskTemplateName = function () {
        var taskConfig = instance.getTaskConfig();
        if(!taskConfig) return null;

        var sampleName = getAttrStringValue(taskConfig, 'sampleName', 'Custom');
        if (sampleName == 'Custom') {
            return getAttrStringValue(taskConfig, 'templateFile', 'Custom');
        } else return sampleName;
    }

    this.updateProjectXML = function(){
        let projectXML = xmlToString(instance.getProjectConfig());
        let newHash = MurmurHash3(projectXML).result();
    
        if (instance.lastConfigHash != null && instance.lastConfigHash === newHash) {
            console.debug("Project XML settings hashes match, update canceled");
            var deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        }

        instance.lastConfigHash = newHash;
        
        SQConstants.setProjectConfig(instance.getProject(), projectXML);

        instance.xmlUpdatePromise = BackendService.getPromise('/project/updateProjectXML', {
            projectName: instance.projectName,
            xmlConfig: projectXML
        }, 'POST', false);

        instance.xmlUpdatePromise.then(function (result) {
            if (result.data.error) {
                $rootScope.showError(result.data.error);
            }
        });

        return instance.xmlUpdatePromise;
    }

    this.updateTaskXML = function(taskXMLFile, taskConfig) {
        let configObject = taskConfig || instance.getTaskConfig();
        if(!configObject || $rootScope.project.state == SQConstants.getConstants().runningStatuses.running) {
            console.log("Cannot update settings of task, project '"+instance.projectName+"'is running...")
            let deferred = $q.defer();
            deferred.resolve();
            return deferred.promise;
        }

        let taskXML = xmlToString(configObject);

        taskXMLFile = taskXMLFile || instance.getTask().taskXMLFile;

        if(taskXMLFile === instance.getTask().taskXMLFile){
            let newHash = MurmurHash3(taskXML).result();

            if (instance.lastTaskConfigHash != null && instance.lastTaskConfigHash === newHash) {
                console.debug("Task XML settings hashes match, update canceled");
                let deferred = $q.defer();
                deferred.resolve();
                return deferred.promise;
            }

            instance.lastTaskConfigHash = newHash;
        }

        SQConstants.setTaskConfig(instance.projectName, taskXMLFile, taskXML);

        instance.xmlUpdatePromise = BackendService.getPromise('/project/updateTaskXML', {
            projectName: instance.projectName,
            taskXMLFile,
            xmlConfig: taskXML
        }, 'POST', false);

        instance.xmlUpdatePromise.then(function (result) {
            let simpleSettings = result.data.simpleSettings;

            if(simpleSettings){
                let elTask = getTask(instance.getProjectConfig(), instance.getTask());
                elTask.setAttribute("sampleName", simpleSettings.strategyType);
            }

            if (result.data.error) {
                $rootScope.showError(result.data.error);
            }
        });

        return instance.xmlUpdatePromise;
    }

    this.createFile = function (filePath, fileContent, callback) {
        BackendService.sendRequest('/main/createFile', {
            filePath: filePath,
            fileContent: fileContent
        }, callback, 'POST');
    }

    this.loadFile = function (filePath, callback) {
        BackendService.sendRequest('/main/loadFile', {
            filePath: filePath
        }, function (result) {
            callback(result.fileContent);
        }, 'GET');
    }

    this.chooseFile = function (actionType, currentDirectory, fileName, extension, multiSelectionEnabled, showFiles, callback) {
        console.error("chooseFile - Not implemented.");
    }

    this.saveFileUsingJavaDialog = function (fileContent, fileName, extension, actionType, currentDirectory) {
        console.error("saveFileUsingJavaDialog - Not implemented.");
    }

    this.saveSetting = function (key, value, callback) {
        SQConstants.getSettings()[key] = value;

        BackendService.sendRequest("/main/saveSetting", {
            key: key,
            value: value
        }, function () {
            if (callback) callback();
        }, "POST");
    }

    this.regenerate = function () {
        var deferred = $q.defer();

        BackendService.getPromise('/main/regenerate', null, 'GET').then(function(result){
            if(result.success){
                window.parent.preloadedTemplates = null;
            }

            deferred.resolve(result);
        });

        return deferred.promise;
    }

    this.toggleFullscreen = function () {
        return BackendService.getPromise('/main/toggleFullscreen', null, 'GET');
    }

    this.minimize = function () {
        return BackendService.getPromise('/main/minimize', null, 'GET');
    }

    this.exit = function () {
        return BackendService.getPromise('/main/exit', null, 'GET');
    }

    this.notifyAppLoaded = function () {
        if (!mainAppExists()) return;

        getApp(window.appConfig.product).loaded = true;

        if (!isMainApp() && !isAlgoWizard()) {
            L.setFont();
        }

        if (appsPreloaded()) {
            if (!isQuantDataManager()) {
                preloadAWEditor();
            }

            $timeout(function () {
                $('#main-load-screen', window.parent.document).fadeOut('fast');
                console.log("GUI loaded");
                BackendService.sendRequest('/main/appLoaded');
            }, 3000, false);
        }

        window.parent.onAppLoaded();
    }

    this.showPopup = function (popupId) {
        $timeout(function () {
            showPopup(popupId);
        }, 0, false);
    }

    this.hidePopup = function (popupId) {
        hidePopup(popupId);
    }

    this.openBrowser = function (url, callback) {
        BackendService.sendRequest("/main/openbrowser", {
            url: url
        }, callback);
    }

    this.openHelp = function (topic) {
        BackendService.sendRequest("/main/openhelp", {
            topic: topic
        });
    }

    this.openDocument = function (fileName, extension) {
        BackendService.sendRequest("/main/opendocument", {
            fileName: fileName,
            extension: extension
        });
    }

    this.getRemoteAccessSettings = function (callback) {
        BackendService.getPromise('/main/getremoteaccess', null).then(function (result) {
            callback(result.data.settings);
        });
    }

    this.isTaskManager = function () {
        return (window.appConfig.product == 'TASKMANAGER');
    }

    this.isPortfolioMaster = function () {
        return (window.appConfig.product == 'PORTFOLIOMASTER');
    }

    this.confirm = function (confirmed, callback) {
        BackendService.sendRequest("/project/confirm", {
            projectName: instance.getProject(),
            confirmed: confirmed
        }, callback);
    }

    function preloadAWEditor() {
        try {
            console.log("Preloading AlgoWizard ...");

            var awFrame = $("#algowizard-frame", window.parent.document);
            if(!awFrame.attr('src')) {
                let awEditor = $injector.get("AlgoWizardService");
                if(awEditor) {
                    awEditor.initEditor().then((value) => {
                        awFrame.attr('src', '../AlgoWizard/index.html?nocache='+Date.now());

                        awEditor.waitForInternalEventHandlerAttached().then(() => {
                            getApp("AlgoWizard").loaded = true;
                            
                            console.info("AlgoWizard editor loaded");

                            if(SQConstants.getSettings().skin) {
                                console.log("AlgoWizard applying skin...", SQConstants.getSettings().skin)
                                awEditor.editorAction("changeSkin", { theme: SQConstants.getSettings().skin });
                            }
                        });
                    });
                }
            }
        } catch(err) {
            console.error("Failed to load AlgoWizard editor", err);
        }
    }

    function getPanels() {
        var panels = [];

        var availablePanels = sqPlugin.getPlugins("AppPanel");
        for (var i = 0; i < availablePanels.length; i++) {
            var panel = availablePanels[i];

            if (panel.product && panel.product != window.appConfig.product) {
                continue;
            }

            panels.push(panel);
        }

        return panels;
    }

    this.switchToPanel = function (panel) {
        if (activePanel != panel) {
            var switchToResults = (panel == 'results');
            showResults(switchToResults);

            activePanel = panel
            publishSelection();

            instance.sendActionRequest('RESULTS', 'showResultsPanel', { product: window.appConfig.product, displayed: switchToResults });
            setTimeout(function () { window.dispatchEvent(new Event('resize')); }, 0);
        }
        else {
            instance.sendActionRequest('RESULTS', 'showResultsPanel', { product: window.appConfig.product, displayed: false });
        }

        return instance.appPanels && instance.appPanels.selectTab ? instance.appPanels.selectTab(panel) : null;
    }

    this.getActivePanel = function () {
        var panel = instance.appPanels.getActiveTab();
        return panel ? panel.dataItem : null;
    }

    this.sendActionRequest = function (targetProductCode, actionName, params, callback) {
        var args = {
            productCode: targetProductCode,
            action: {
                name: actionName,
                params: params || {}
            }
        }

        window.parent.broadcastEvent(SQEvents.get("ACTION_REQUEST"), args);
    }

    this.checkSettingsSaved = function () {
        if (!instance.settingsSavePromise) {
            var deferred = $q.defer();
            deferred.resolve();
            instance.settingsSavePromise = deferred.promise;
        }
        return instance.settingsSavePromise;
    }

    this.copyToClipboard = function (data) {
        BackendService.sendRequest('/main/copyToClipboard', { data: data }, null, 'POST');
    }

    this.printToLog = function(message, isError){
        BackendService.sendRequest('/project/printToLog', { message : message, isError : isError }, null, 'POST');
    }

    this.isProVersion = function() {
        return $rootScope.license.isProVersion;
    }

    this.isTrial = function() {
        return $rootScope.license.isTrial;
    }

    this.getLicense = function() {
        return $rootScope.license;
    }

    this.getSelectedLanguage = function() {
        let lang = "English";

        if($rootScope.selectedLanguage) {
            lang = $rootScope.selectedLanguage.title;
        }

        return lang;
    }

    function onWebSocketData(data) {
        if (data.appSwitched && window.appConfig.product != 'RESULTS') {
            instance.switchToPanel(activePanel);
        }

        // task settings changed backend-side (project/updateTaskXML with notifyUI=true)
        if (data.taskConfigChanged && data.taskConfigChanged.projectName == instance.getProject()) {
            instance.reloadTaskFromServer(data.taskConfigChanged.taskXMLFile);
        }

        if (data.confirmation) {
            if (data.confirmation.projectName == instance.getProject()) {
                $rootScope.showConfirm(data.confirmation.title, data.confirmation.message, instance.confirm, true, function () {
                    instance.confirm(false);
                });
            }
        }

        if (data.LicenseInfo) {
            $rootScope.license.email = data.LicenseInfo.email;
            $rootScope.license.code = data.LicenseInfo.code;
            $rootScope.license.isUltimateVersion = data.LicenseInfo.isUltimateVersion;
            $rootScope.license.isProVersion = data.LicenseInfo.isProVersion;
            $rootScope.license.isTrial = data.LicenseInfo.isTrial;
            $rootScope.license.isSpecialTrial = data.LicenseInfo.isSpecialTrial;
            $rootScope.license.sq4bAllowed = data.LicenseInfo.sq4bAllowed;
            $rootScope.license.marketplace = data.LicenseInfo.marketplace !== false;
            $rootScope.license.volumeProfile = data.LicenseInfo.volumeProfile;
            $rootScope.$evalAsync();

            SQEvents.notifyListeners(SQEvents.get('LICENSE_CHANGED'), data.LicenseInfo);
        }

        if (data.AppConfigsChanged) {
            SQEvents.notifyListeners(SQEvents.get('APP_CONFIGS_CHANGED'), data.AppConfigsChanged);
        }

        if (data.UpdateProject && instance.isTaskManager()) {
           let projectConfig = JSON.parse(data.UpdateProject.projectConfig)

           setProjectConfig(projectConfig);

           let currentTask = instance.getTask();           
           if(projectConfig.tasks && projectConfig.tasks[currentTask.taskXMLFile]) {
                instance.setTask(currentTask.type, currentTask.name, currentTask.title, currentTask.typeOrig, currentTask.taskXMLFile);
           }
        }

        if(data.TemplatePathChange){
            let taskXMLFile = data.TemplatePathChange.taskXMLFile;
            let templatePath = data.TemplatePathChange.templateFile;
            updateTemplateFile(taskXMLFile, templatePath);
        }

        if(data.ReloadUI) {
            location.reload();
        }
    }

    function updateTemplateFile(taskXMLFile, templatePath){
        let elSettings = SQConstants.getTaskConfig(instance.getProject(), taskXMLFile, true);
        let elWhatToBuild = getChildElement(elSettings, "WhatToBuild");
        let elStrategyType = getChildElement(elWhatToBuild, "StrategyType");
        elStrategyType.setAttribute("templateFile", templatePath);

        let updatedConfigStr = xmlToString(elSettings);
        SQConstants.setTaskConfig(instance.getProject(), taskXMLFile, updatedConfigStr);

        if(taskXMLFile === instance.getTask().taskXMLFile){
            instance.taskXMLConfig = xmlToObject(updatedConfigStr);
            instance.taskXMLDoc = getXMLDoc(updatedConfigStr);
        }

        SQEvents.notifyListeners(SQEvents.get('SETTINGS_TAB_RELOAD'), 'What to build');
    }

    function registerDbChannelHandler(curProjectName) {
        var databankChannel = SQConstants.getConstants().channels.databanks;

        SQWebSocketService.removeListener(instance.projectName, databankChannel, listenerId);

        SQWebSocketService.subscribe(curProjectName, databankChannel, listenerId, function (data) {
            var params = {
                projectName: instance.projectName,
                databankName: instance.databank ? instance.databank.title : null,
                changes: data[0] ? data[0].changes : null,
                product: instance.getProduct()
            }
            window.parent.broadcastEvent(SQEvents.get("STRATEGIES_UPDATED"), params);
        });
    }

    function isAppLoaded(productCode) {
        for (var i = 0; i < window.parent.apps.length; i++) {
            var appData = window.parent.apps[i];
            if (appData.appCode == productCode) {
                return appData.loaded;
            }
        }
        return false;
    }

    this.performAction = function(productCode, actionName, actionData) {
        window.parent.switchToApp(productCode);
        window.parent.broadcastEvent(SQEvents.get('APP_SWITCHED'), productCode);

        if (isAppLoaded(productCode)) {
            instance.sendActionRequest(productCode, actionName, actionData);
        }
        else {
            var intervalHandle = setInterval(function () {
                if (isAppLoaded(productCode)) {
                    clearInterval(intervalHandle);
                    instance.sendActionRequest(productCode, actionName, actionData);
                }
            }, 500);
        }
    }

    var instance = this;

    var listenerId = "AppService-SQUANT";

    // Current selection on window.top for non-Angular readers; module stamp marks it stale.
    function publishSelection() {
        try {
            if (window.appConfig.product == 'SQUANT') return;
            var db = instance.databank;
            window.top.sqSelection = {
                module: window.appConfig.product,
                project: instance.projectName || null,
                task: window.appConfig.task || null,
                databank: !db ? null
                    : (typeof db === 'string' ? db : (db.title || db.name || db.databankName || null)),
                activePanel: activePanel || null,
                selectedStrategies: instance.strategiesSelected || null
            };
        } catch (e) {}
    }

    this.publishSelection = publishSelection;

    this.appPanels = {
        tabs: getPanels(),
        onSelectTab: function (panel) {
            SQEvents.notifyListeners(SQEvents.get('APP_PANEL_CHANGED'), panel.dataItem);

            activePanel = panel.dataItem;
            publishSelection();

            if(panel === "tmprojects"){
                instance.setProject(null);
            }
        },
        afterInit: null
    }

    var activePanel = null;

    this.lastConfigHash = null;
    this.lastTaskConfigHash = null;

    this.settingsOpen = false;
    this.xmlUpdatePromise = null;     //used when saving xml config

    this.projectName = window.appConfig.project;

    this.initXMLObjects();

    $rootScope.project = {
        state: 0,
        name: instance.projectName
    };

    $rootScope.license = {
        isProVersion: window.appConfig.product != 'SQMANAGER',
        isTrial: false,
        marketplace: true
    }

    SQWebSocketService.subscribeGeneral("AppService-" + window.appConfig.appCode, onWebSocketData);

    this.getCurrentEngine = function() {
        let engine = null;

        var dataElem = instance.getCurrentTaskTabSettings("Data");
        if (dataElem) {
            var setupsElem = getChildElement(dataElem, 'Setups', true);
            if (setupsElem) {
                var setupElems = getChildElements(setupsElem, 'Setup');
                if (setupElems.length > 0) {
                    engine = getAttrValue(setupElems[0], 'engine');
                }
            }
        } 

        return engine;
    }

    this.getCurrentEngineKey = function() {
        let engine = instance.getCurrentEngine();
        
        return SQConstants.getEngineKey(engine);
    }

    //- cross iframe communication interface --------------------------

    SQEvents.add("STRATEGIES_UPDATED", "strategies-changed");       //notification that strategy data has changed
    SQEvents.add("APP_SWITCHED", "app-switched");                   //called after clicking app icon in left menu
    SQEvents.add("STRATEGY_DBLCLICK", "strategy-dblclick");         //called after double-clicking strategy inside databank (results loading)
    SQEvents.add("HIDE_LOADING_ICON", "hide-loading-icon");         //called after double-clicking strategy inside databank (results loading)
    SQEvents.add("ACTION_REQUEST", "action-request");
    SQEvents.add("LICENSE_CHANGED", "license-changed");
    SQEvents.add("APP_CONFIGS_CHANGED", "app-configs-changed");     //remote app config urls (license token) changed; data = {codes, configs}

    if (window.appConfig.product == 'SQUANT') {
        window.getLicenseInfo = function(){
            return $rootScope.license;
        };

        SQEvents.addListener(listenerId, [
            SQEvents.get('APP_PROJECT_CHANGED'),
            SQEvents.get('SETTINGS_TASK_CHANGED'),
            SQEvents.get('DATABANK_CHANGED'),
            SQEvents.get('STRATEGY_SELECTED'),
            SQEvents.get('SKIN_CHANGED'),
            SQEvents.get('LANGUAGE_CHANGED')
        ], function (event, data) {
            if (event == SQEvents.get('APP_PROJECT_CHANGED')) {
                instance.projectName = data;
                instance.lastConfigHash = null;
            }
            else if (event == SQEvents.get('SETTINGS_TASK_CHANGED')) {
                window.appConfig.task = data;
                instance.lastTaskConfigHash = null;
            }
            else if (event == SQEvents.get('DATABANK_CHANGED')) {
                instance.databank = data;
            }
            else if (event == SQEvents.get('STRATEGY_SELECTED')) {
                instance.strategiesSelected = data;

            }
            else if (event == SQEvents.get('SKIN_CHANGED')) {
                let awEditor = $injector.get("AlgoWizardService");
                if(awEditor) {
                    awEditor.editorAction("changeSkin", { theme: data.skin.name });
                }
            }
            else if (event == SQEvents.get('LANGUAGE_CHANGED')) {
                if(!window.top.commonData || !window.top.commonData.translations) {
                    console.log("Lang not loaded...")
                    return;
                }
                
                let awEditor = $injector.get("AlgoWizardService");
                if(awEditor) {
                    let lang = {
                        language: data.title, 
                        translations: window.top.commonData.translations
                    }

                    if (lang.translations instanceof Map) {
                        lang.translations = Array.from(window.top.commonData.translations);
                    }

                    if (!lang.language) {
                        lang.language = $rootScope.selectedLanguage;
                    }
                    
                    awEditor.editorAction("changeLanguage", lang);
                }
            }
        });
    }
    else if (!isAlgoWizard() && !isCodeEditor()) {

        if (productHasDatabank()) {
            registerDbChannelHandler(instance.projectName);
        }

        if (window.appConfig.product != 'QDM') {
            window.parent.addListener(listenerId, [
                SQEvents.get('LICENSE_CHANGED')
            ], function (event, data) {
                if (event == SQEvents.get('LICENSE_CHANGED')) {
                    $rootScope.license.email = data.email;
                    $rootScope.license.code = data.code;
                    $rootScope.license.isProVersion = data.isProVersion;
                    $rootScope.license.isUltimateVersion = data.isUltimateVersion;
                    $rootScope.license.isTrial = data.isTrial;
                    $rootScope.license.sq4bAllowed = data.sq4bAllowed;
                    $rootScope.license.isSpecialTrial = data.isSpecialTrial;
                    $rootScope.license.marketplace = data.marketplace !== false;
                    $rootScope.license.volumeProfile = data.volumeProfile;

                    $timeout(function () {
                        SQEvents.notifyListeners(SQEvents.get("LICENSE_CHANGED"), data);    //broadcast event across this app
                    });
                }
            });
        }
    }
});
