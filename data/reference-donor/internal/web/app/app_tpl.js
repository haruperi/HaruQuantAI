angular.module('app', [
    'ui.router',
    'ui.bootstrap',
    //'angular-confirm',
    'ngStorage',
    'ngSanitize',
    'angularSpinner',
    'FBAngular',
    'rzModule',
    'sqevents',
    'sqplugin',
    // App
    'app.layout',
    'app.login'
     #sq-dependencies
]) 
.config(function ($provide, $httpProvider, SQEventsProvider, $compileProvider) {
    $compileProvider.debugInfoEnabled(false);
    $httpProvider.useApplyAsync(true);
    
    // Intercept http calls.
    $provide.factory('ErrorHttpInterceptor', function ($q, $injector) {
        var errorCounter = 0;

        function notifyError(rejection){
            console.error(rejection.status + ' - ' + rejection.statusText);
        }

        return {
            // On request failure
            requestError: function (rejection) {
                // show notification
                notifyError(rejection);
                // Return the promise rejection.
                return $q.reject(rejection);
            },

            // On response failure
            responseError: function (rejection) {
                // show notification
                notifyError(rejection);
                
                if(rejection.status === 401) {
                    window.top.location.href = '/#!/sqlogin';    //redirect main window to login page
                    /*
                    if(rejection.data.disabled != undefined){
                        $injector.get('LoginService').setDisabled(rejection.data.disabled);
                    }
                    $injector.get('$state').transitionTo('sqlogin');
                    */
                }
                // Return the promise rejection.
                return $q.reject(rejection);
            }
        };
    });

    // Add the interceptor to the $httpProvider.
    $httpProvider.interceptors.push('ErrorHttpInterceptor');

})
.constant('APP_CONFIG', window.appConfig)/*
.factory('$templateCache', function($cacheFactory, $http, $injector) {
    var cache = $cacheFactory('templates');
    var templatesPromise;

    return {
        get: function(url) {
            var fromCache = cache.get(url);

            // already have required template in the cache
            if (fromCache) {
                return fromCache;
            }

            if(!templatesPromise){
                // first template request ever - get the all tpl file
                if (!window.parent.TemplatesHTMLPromise) {
                    //var templatesUrl = '/' + window.appConfig.product + '/build/templates.html';
                    var templatesUrl = '/common/templates.html';
                    window.parent.TemplatesHTMLPromise = $http.get(templatesUrl);
                }
                    
                templatesPromise = window.parent.TemplatesHTMLPromise;

                templatesPromise.then(function(response) {
                    $injector.get('$compile')(response.data);
                });
            }

            return templatesPromise.then(function(response) {
                //console.log(url, response, cache.get(url));
                return {
                    status: response.status,
                    data: cache.get(url),
                    headers: response.headers
                };
            });
        },

        put: function(key, value) {
            cache.put(key, value);
        }
    };
})*/
.run(function ($rootScope, $state, $stateParams, LoginService) {
    console.log("app started");
    $rootScope.$state = $state;
    $rootScope.$stateParams = $stateParams;
    
    $rootScope.$on('$stateChangeStart', function(e, toState, toParams, fromState, fromParams) {
        console.log("Going from " + fromState.name + " to " + toState.name);
        
        var isLogin = toState.name === "sqlogin";
        if(isLogin){
            return; // no need to redirect 
        }
        
        // redirect if not authenticated
        LoginService.checkRemoteAccess().then(function(result){
            if(!result.data.success){
                window.top.location.href = '/#/sqlogin';    //redirect main window to login page
                /*
                if(result.data.disabled != undefined){
                    LoginService.setDisabled(result.data.disabled);
                }
                e.preventDefault(); // stop current execution
                $state.go('sqlogin', {redirectTo: toState.name}); // go to login
                */
            }
        });
        
    });
});
