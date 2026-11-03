"use strict";

angular.module('app.layout', ['ui.router', 'ui.bootstrap'])

.config(function ($stateProvider, $urlRouterProvider, $locationProvider, SQEventsProvider) {

    SQEventsProvider.add("SKIN_CHANGED", "skin-changed");
    SQEventsProvider.add("APP_PANEL_CHANGED", "app-panel-changed");
    SQEventsProvider.add("OPEN_ABOUT_DIALOG", "open-about-dialog");
    SQEventsProvider.add("CUSTOMIZATION_CHANGED", "customization-changed");

    $stateProvider
        .state('app', {
            abstract: false,
            url: '/',
            views: {
                root: {
                    templateUrl: '../SQUANT/layout/views/layout.html',
                    controller: 'LayoutCtrl'
                }
            },
            resolve: {
                connectWebSocket: function(SQWebSocketService){
                    return SQWebSocketService.connectWebSocket(location.port);
                },
                loadInitializationData: function(LayoutService){
                    return LayoutService.loadInitializationData();
                },
                loadConstants: function(SQConstants, L, SkinService, $q){
                    var deferred = $q.defer();

                    SQConstants.loadAll().then(function () {
                        var promises = [
                            L.downloadLanguage(),
                            SkinService.loadSkins()
                        ];
    
                        $q.all(promises).then(function () {
                            deferred.resolve();
                        });
                        
                    });
                    
                    return deferred.promise;
                }
            }
        });
        
    $urlRouterProvider.otherwise(window.appConfig.defaultURL);

})
