angular.module('app.dmhome').service('DMHomeService', function($rootScope, $q, BackendService, SQEvents) {
        
        // home page url comes from the license token (app config "homepage"), the core builds the link
        this.link = function (callOnSuccess) {
            BackendService.sendRequest('/main/appconfig', {
                code: 'homepage',
                payload: 'qdm',
                offline: '/plugins/DataManagerHome/offline/index.html'
            }, callOnSuccess);
        }
});
