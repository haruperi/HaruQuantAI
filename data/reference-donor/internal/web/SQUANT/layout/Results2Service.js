angular.module('app').service('Results2Service', function($rootScope, $injector, BackendService, SQConstants, AppService, AlgoCloudService, L) {
    
    //-----------------------------------------------------------------------------------
    // Initialization communication interface with Results2
    this.initCommunicationInterface = function() {
        console.log("Results2 initializing communication interface ...");  

        window.top.resultsInterface = window.top.resultsInterface || {};
        
        window.top.resultsInterface.config = {
            constants: SQConstants.getConstants(),
            initializationData: InitializationData(),
            settings: SQConstants.getSettings()
        };

        window.top.resultsInterface.actionHandler = actionHandler;
    }

    //-----------------------------------------------------------------------------------
    // Action handler

    const actionHandler = async(actionName, args) => {
        console.info("Results2 action called (" + actionName + ")", args);

        switch(actionName) {
            case "loadFromFile": return onLoadFromFile(args);
            case "saveToFile": return onSaveToFile(args);
            case "showCSVXLSXExportDialog": return onShowCSVXLSXExportDialog(args);
            case "openLink": return onOpenLink(args);
            case "showSuccess": return onShowSuccess(args);
            case "showError": return onShowError(args);
            case "backToEditor": return onBackToEditor(args);
            case "applyStrategyConfig": return onApplyStrategyConfig(args);
            case "chooseSavePath": return onChooseSavePath(args);
            case "chooseFile": return this.chooseFile(args);
            case "getProjectTasks": return onGetProjectTasks(args);
            case "openInAlgoCloud": return onOpenInAlgoCloud(args);

            default:
                console.error("Unknown Results action " + actionName);
                return { error: "Unknown Results action " + actionName };
        }
    }

    //-----------------------------------------------------------------------------------
    // "Open in AlgoCloud" from the Source code tab: args = the same locator the tab posts
    // to sourcecode/print ({project, databank, strategy} | {backtestID, strategyXML, settingsXML}).
    // AlgoCloudService does the upload, the warnings dialog and opens the browser.

    const onOpenInAlgoCloud = async function(args) {
        return AlgoCloudService.open(args);
    }

    //-----------------------------------------------------------------------------------
    // Task list of a Task Manager project — mirrors StrategyConfigService.loadTasks
    // (Tasks > Task elements of the project config; type == task name in TM mode).
    // args: { projectName }

    const onGetProjectTasks = async function(args) {
        var tasks = [];

        var projectObj = SQConstants.getProjectConfig(args.projectName, true);
        if (projectObj) {
            var tasksObj = getChildElement(projectObj, 'Tasks');
            var taskObjs = getChildElements(tasksObj, 'Task');

            for (var i = 0; i < taskObjs.length; i++) {
                var taskName = getAttrValue(taskObjs[i], "name", null);

                tasks.push({ type: taskName, name: taskName, title: getAttrStringValue(taskObjs[i], "title", taskName) });
            }
        }

        return { tasks: tasks };
    }

    //-----------------------------------------------------------------------------------
    // Opens the save-file dialog and resolves the picked PATH without writing anything —
    // for flows where the node writes the file itself (e.g. the correlation matrix save,
    // legacy CorrelationMatrixCtrl.js $scope.save). args: { actionType, fileName, extension }

    const onChooseSavePath = async function(args) {
        return new Promise(resolve => {
            $rootScope.saveFile(L.tsq("Select file"), args.extension, args.actionType, args.fileName, null, function(targetPath) {
                resolve(targetPath || null);
            });
        });
    }

    //-----------------------------------------------------------------------------------
    // Applies a strategy config loaded by Results2 to the target app.
    // Mirrors the legacy ResultsStrategyConfig flow (StrategyConfigCtrl.js
    // applyStrategyConfig/applyConfig): resolve project resources first when the
    // strategy carries any, then hand the config to the product via loadConfig.
    // args: { product: "BUILDER"|"RETESTER"|"OPTIMIZER"|"TASKMANAGER", taskName, config, resourcesXML?, onApplied? }
    // onApplied travels as the loadConfig params.callback, the slot the legacy tab filled with
    // its refreshContent (StrategyConfigCtrl.js applyStrategyConfig): applyConfigToTask fires
    // it only after updateTaskXML saved the task on the node, and Results2 re-prints the
    // config on it so the diffs reflect what was just applied. Without it the tab kept
    // showing the old diffs after the "applied" toast.

    const onApplyStrategyConfig = async function(args) {
        var apply = function(config) {
            if (args.product === "TASKMANAGER") {
                $rootScope.showSuccess("Strategy config was applied to task '" + args.taskName + "'");
            } else {
                $rootScope.showSuccess("Strategy config was applied to project '" + args.product + "'");
            }
            AppService.sendActionRequest(args.product, "loadConfig", { taskName: args.taskName, config: config, callback: args.onApplied });
        };

        if (args.resourcesXML) {
            $rootScope.resolveResources(args.config, args.resourcesXML, SQConstants.getConstants().projectResourceActionTypes.applyStrategyConfig, function(callbackData) {
                if (callbackData.taskXML) {
                    apply(callbackData.taskXML);
                } else if (callbackData.loadAsIs) {
                    apply(args.config);
                }
                // dialog cancelled: no toast, nothing applied (legacy behaviour)
            });
        } else {
            apply(args.config);
        }

        return null;
    }

    //-----------------------------------------------------------------------------------
    // Displays file picker dialog and saves content to selected file

    const onSaveToFile = async function(data) {
        /*
        //this is how args should look like
        var args = {
            actionType: "saveSourceCode",
            fileName: "Santa Claus rally.mq4",
            fileContent: "rolem ipsum dolor sit amet",
            extension: {
                name: "xml",
                description: "XML Settings Files",
            },
        };*/

        return new Promise(resolve => {
            $rootScope.saveFile(L.tsq("Save file"), data.extension, data.actionType, data.fileName, data.fileContent);
            resolve(null);
        });
    } 

    //-----------------------------------------------------------------------------------
    // Displays file picker dialog and returns content of selected file

    const onLoadFromFile = async(args) =>{
        let data = {
            actionType: args.actionType,
            showFiles: true,
            multiSelectionEnabled: false,
            currentDirectory: "",
            extension: {
                name: "xml",
                description: "XML Settings Files",
            },
        };

        let path = await this.chooseFile(data);
        if(!path) return;

        data = {
            filePath: path,
        };

        result = await BackendService.httpRequest("/main/loadFile", data, "POST");
        if(result.success) {
            let content = result.fileContent;

            result = {
                success: result.success,
                actionType: args.actionType,
                content: content
            }

            this.showSuccess(result.success);
        }

        return result;
    }

    //-----------------------------------------------------------------------------------
    // Displayes file picker dialog and returns selected file path

    this.chooseFile = async function(data) {
        let title = data.title || L.tsq("Select file");

        return new Promise(resolve => {
            $rootScope.showFilePicker(title, data.actionType, data.showFiles, data.multiSelectionEnabled, data.currentDirectory, data.extension, null, function (paths) {
                let path = paths ? paths[0] : null;
                resolve(path);
            });
        });
    }     

    //-----------------------------------------------------------------------------------

    const onShowCSVXLSXExportDialog = async function(data) {
        /*
        //this is how args should look like
        var data = {
            fileName: "TradelistExport",
            pathName: "saveTradelistToCSV",
        };*/
        return new Promise(resolve => {
            $rootScope.showCSVXLSXExportDialog(data.fileName, data.pathName, function (path, useComma) {
                window.parent.hidePopup("#saveFileDialog");
                resolve({
                    path, 
                    useComma
                });
            });
        }); 
    } 
    
    //-----------------------------------------------------------------------------------

    const onOpenLink = async(args) =>{
        AppService.openBrowser(args.link);
    }

    //-----------------------------------------------------------------------------------

    const onShowSuccess = async(message) =>{
        this.showSuccess(message);
    }

    //-----------------------------------------------------------------------------------

    const onShowError = async(message) =>{
        this.showError(message);
    }

    this.showSuccess = function(message) {
        window.top.sqNotices.addNotice("success", message);
    }

    this.showError = function(message) {
        window.top.sqNotices.addNotice("error", message);
    }

    const onBackToEditor = async()=>{
        awShowResults(false, $injector);
    }
});
