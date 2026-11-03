angular.module('app.sessions').service('SessionService', function($rootScope, $q, BackendService, SQEvents) {
        
        this.addSession = function(template){
            return BackendService.getPromise('/sessions/addSession', template);
        }

        this.removeSession = function(names){
            return BackendService.sendRequest('/sessions/removeSession', {names : names}, function(result){
                if(!result.success){
                    $rootScope.showError(result.error);
                }
            },'POST');
        }

        this.updateSession = function(template){
            return BackendService.getPromise('/sessions/updateSession', template);
        }

        this.save = function (data) {
            BackendService.sendRequest('/sessions/save', data, function (result) {
                if (result.success) {
                    $rootScope.showSuccess(result.success);
                }
            }, 'POST');
        }

        this.load = function (data) {
            BackendService.sendRequest('/sessions/load', data, function (result) {
                if (result.success) {
                    $rootScope.showSuccess(result.success);
                }
            });
        }

        // NinjaTrader 8 Trading Hours import (plan 138).
        //
        // `path` is optional - without it the backend uses the NinjaTrader templates folder, which
        // sits at a fixed location. `overwrite` is opt-in: re-importing the folder is the normal way
        // to use this and must never replace a session the user has edited by hand.
        // forceCallback, because BackendService only invokes the callback when result.success is
        // truthy otherwise - so a failed listing (an empty or missing folder) would never reach the
        // caller and the button would appear to do nothing at all.
        this.listNinjaTraderTemplates = function (data, callback) {
            BackendService.sendRequest('/sessions/listNinjaTraderTemplates', data || {}, function (result) {
                if (!result || result.error) {
                    return;
                }
                if (callback) {
                    callback(result);
                }
            }, 'GET', false, true);
        }

        this.importNinjaTraderTemplates = function (data, callback) {
            BackendService.sendRequest('/sessions/importNinjaTraderTemplates', data || {}, function (result) {
                if (!result || result.error) {
                    if (callback) {
                        callback(null);
                    }
                    return;
                }

                // The summary carries the dropped-holiday count. SQX has no holiday model, so an
                // imported session lets a backtest trade days the exchange was closed - shown, not
                // buried.
                $rootScope.showSuccess(result.success);

                // A template that fails is named, not just counted. The commonest cause is a time
                // zone outside the reader's mapping, and "3 failed" gives the user no way to find
                // out which three.
                if (result.failed && result.failed.length > 0) {
                    var names = [];
                    for (var i = 0; i < result.failed.length; i++) {
                        names.push(result.failed[i].template + ' - ' + result.failed[i].reason);
                    }
                    $rootScope.showError(L.tsq('Not imported') + ': ' + names.join('; '));
                }

                if (callback) {
                    callback(result);
                }
            }, 'POST', false, true);
        }

        this.clone = function (data, callback) {
            BackendService.sendRequest('/sessions/clone', data, function (result) {
                if (result.success) {
                    $rootScope.showSuccess(result.success);
                    callback();
                }
            });
        }
    });
