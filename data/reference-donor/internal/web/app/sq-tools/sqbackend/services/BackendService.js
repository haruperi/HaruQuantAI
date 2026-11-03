angular.module("app").service("BackendService", [
    "$http",
    "$q",
    "$rootScope",
    "$injector",
    function($http, $q, $rootScope, $injector) {

        this.getPromise = function(url, data, method, disableGZIP) {
            var deferred = $q.defer();

            url = (url.indexOf("/") == 0 ? "" : "/") + url;

            //For AlgoWizard modify the URL to address the target node
            url = checkURL(url);

            if (isCloud() && url == -1) {
                console.log("Node url not found, cancelling request");
                deferred.resolve({
                    success: false,
                    error: "Node url not found",
                    data: "Node url not found",
                });
                return deferred.promise;
            }

            let headers = {};

            if (window.top.auth_token) {
                headers = {
                    "sq-auth-token": window.top.auth_token,
                };
            } else if (window.top.cognitoToken) {
                headers = {
                    "Authorization": "Bearer " + window.top.cognitoToken,
                };
            }

            //fixed SQX remote access
            if(token && !headers['sq-auth-token']) {
                headers['sq-auth-token'] = token;
            }

            var req = {
                url: url,
                headers: headers,
            };

            if (isCloud()) {
                disableGZIP = true;
            }

            if (method == "POST") {
                req.method = "POST";

                if (isCloud() || disableGZIP) {
                    req.data = $.param(data);
                    req.headers["Content-Type"] = "application/x-www-form-urlencoded";
                } 
                else {
                    req.data = new Blob([pako.gzip($.param(data))]);
                    req.headers["Content-Type"] =
                        "application/json; charset=x-user-defined-binary";
                    req.headers["Content-Encoding"] = "gzip";
                }
            } 
            else {
                req.method = "GET";
                req.params = data;
                req.paramSerializer = "$httpParamSerializerJQLike";
            }

            console.log(
                "Http request - url: " + url + ", data: ",
                data,
                ", method: " + req.method + ", token: " + token
            );

            $http(req).then(
                function(response) {
                    console.log("Http response -", url, response);

                    deferred.resolve({
                        success: response.data.success,
                        error: response.data.error,
                        data: response.data,
                    });
                },
                function(response) {
                    console.log("Http response failed - ", url, response);

                    var defaultErrorMsg = translate(
                        "Http request failed - url: %s, status code: %d, statusText: %s", [url, response.status, response.statusText]
                    );
                    if (response.status == -1) {
                        $rootScope.showError(defaultErrorMsg);
                    }

                    deferred.resolve({
                        success: false,
                        error: response.data ? response.data.error : defaultErrorMsg,
                        data: response.data || defaultErrorMsg,
                    });
                }
            );

            return deferred.promise;
        };

        this.setToken = function(_token) {
            token = _token;
            window.sqAuthToken = _token;
        };

        this.getToken = function() {
            return token;
        };

        this.sendRequest = function(
            url,
            data,
            callback,
            method,
            forceCallback,
            disableGZIP,
            dontCheckResult
        ) {
            if (!data) {
                data = {};
            }

            this.getPromise(url, data, method, disableGZIP).then(function(result) {
                if(dontCheckResult) {
                    callback(result.data);

                } else {
                    if (result.success) {
                        if (callback) {
                            callback(result.data);
                        }
                    } else {
                        var text = result.error || translate("Unknown communication error") + " - " + url;
    
                        if (
                            $rootScope.showError &&
                            text.indexOf("RecordNotFoundException") == -1
                        ) {
                            $rootScope.showError(text);
                            console.error("HTTP request failed - Unknown communication error", url, result);
                        }
    
                        if (forceCallback && callback) {
                            callback(result.data);
                        }
                    }
                }                
            });
        };

        this.httpRequest = async function(
            url,
            data,
            method,
            disableGZIP,
            dontCheckResult
        ) {
            if (!data) {
                data = {};
            }

            let result = await this.getPromise(url, data, method, disableGZIP);

            if (!dontCheckResult && !result.success) {
                var text = result.error || translate("Unknown communication error") + " - " + url;

                if (
                    $rootScope.showError &&
                    text.indexOf("RecordNotFoundException") == -1
                ) {
                    $rootScope.showError(text);
                    console.error("HTTP request failed - Unknown communication error", url, result);
                }
            }

            return result.data;
        }

        //cannot import L beacause of circular dependency
        function translate(text, params) {
            if (!text) return "";

            var L = $injector.get("L");
            if (L) {
                return L.tsq(text, params);
            } else {
                return text.format(params);
            }
        }

        function checkURL(url) {
            if (
                window.top.requestsPrefix
            ) {
                url = (window.top.requestsPrefix + url).replace("//", "/");
            }

            return url;
        }

        function isCloud() {
            return window?.top?.isCloudVersion;
        }

        var instance = this;
        var token;
    },
]);
