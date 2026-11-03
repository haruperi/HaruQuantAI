angular.module('app').service('LayoutService', function($rootScope, $q, BackendService) {

    this.loadInitializationData = function() {
        var deferred = $q.defer();

        BackendService.sendRequest('main/loadInitializationData', null, function(data) {
            window.InitializationDataObject = data;

            console.log("Loaded InitializationData", data)

            deferred.resolve();
        });
        
        return deferred.promise;
    } 

    this.openCodeEditor = function(callOnSuccess) {
        BackendService.sendRequest('main/openCodeEditor', null, callOnSuccess);
    } 

    this.openDebugConsole = function(callOnSuccess) {
        BackendService.sendRequest('main/openDebugConsole', null, callOnSuccess);
    } 

    this.openHelpDialog = function(callOnSuccess) {
        BackendService.sendRequest('main/openHelpDialog', null, callOnSuccess);
    } 
});
