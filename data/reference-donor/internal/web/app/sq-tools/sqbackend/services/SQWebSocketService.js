angular.module('app').service('SQWebSocketService', function ($rootScope, $q, BackendService, $timeout, $injector) {

    var instance = this;

    var connected = false;
    var ws;
    var deferred = $q.defer();

    var subscriptions = [];
    var generalListeners = [];

    this.connectWebSocket = function (port) {
        BackendService.sendRequest("/main/getWebSocketPort", null, function (result) {
            if (result.port) {
                connect(result.port);
            } else {
                $rootScope.showError("Web socket error. Cannot connect web socket.");
            }
        });

        return deferred.promise;
    }

    function connect(port) {
        ws = new WebSocket("ws://" + window.location.hostname + ":" + port + "/websocket/updates");

        ws.onopen = function () {
            console.log("Socket has been opened!");
            connected = true;

            var data = {
                action: 'setup',
                app: window.appConfig.product
            }

            ws.send(JSON.stringify(data));

            deferred.resolve();
        };

        ws.onerror = function (ev) {
            deferred.resolve();
            connected = false;
            console.log("Web socket error. Connecting web socket failed.");
        };

        ws.onmessage = function (message) {
            var received_msg = message.data;
            var msg = JSON.parse(received_msg);

            if (angular.equals({}, msg)) { //empty message
                return;
            }

            processMessage(msg);
        };

        ws.onclose = function () {
            console.log("Socket has been closed!");
            connected = false;

            $timeout(function () {
                console.log("Reconnecting to socket.");
                deferred = $q.defer();
                connect(port);
            }, 1000, false);
        }
    }

    this.sendRequest = function (request) {
        ws.send(request);
    }

    this.isConnected = function () {
        return connected;
    }

    function processMessage(message) {
        if (message.projectData) {
            var projectName = message.projectData.name;
            var channelsData = message.projectData.channels;

            var AppService = $injector.get("AppService");
            if(AppService && projectName != AppService.getProject()) return;

            if (arrayNotEmpty(channelsData)) {
                for (var i = 0; i < channelsData.length; i++) {
                    broadcastChannelData(projectName, channelsData[i]);
                }
            }
        }

        //process data with general listeners
        for (var i = 0; i < generalListeners.length; i++) {
            var listener = generalListeners[i];
            listener.callback(message);
        }
    }

    function broadcastChannelData(projectName, channelData) {
        var channelName = channelData.name;

        var subscription = getItem(subscriptions, 'channel', getChannelName(projectName, channelName));
        if (!subscription) {
            console.warn("Cannot broadcast channel data -> No subscriptions for channel '" + getChannelName(projectName, channelName) + "'");
            return;
        }

        for (var i = 0; i < subscription.callbacks.length; i++) {
            var callback = subscription.callbacks[i].callback;
            callback(channelData.data);
        }
    }

    this.subscribe = function (projectName, channel, callbackId, callback) {
        if(projectName=='TaskManager') {
            return;
        }

        var subscription = getItem(subscriptions, 'channel', getChannelName(projectName, channel));
        if (!subscription) {
            subscription = {
                channel: getChannelName(projectName, channel),
                callbacks: []
            };

            subscriptions.push(subscription);
        }

        if(getItem(subscription.callbacks, "id", callbackId)) {
            console.error("Callback '" + callbackId + "' is already registered");
            return;       //callback is already registered
        }

        subscription.callbacks.push({
            id: callbackId,
            callback: callback
        });

        deferred.promise.then(function () {
            var data = {
                action: 'subscribe',
                projectName: projectName,
                channel: channel
            }

            ws.send(JSON.stringify(data));
        });
    }

    this.unsubscribe = function (projectName, channel, callbackId) {
        instance.removeListener(projectName, channel, callbackId);

        deferred.promise.then(function () {
            var data = {
                action: 'unsubscribe',
                projectName: projectName,
                channel: channel
            }

            ws.send(JSON.stringify(data));
        });
    }

    this.removeListener = function (projectName, channel, callbackId) {
        var channelName = getChannelName(projectName, channel);

        var subscription = getItem(subscriptions, 'channel', channelName);
        if (!subscription) {
            console.warn("Cannot Unsubscribe -> Subscription to channel '" + channelName + "' doesn't exist");
            return;
        }

        removeItem(subscription.callbacks, 'id', callbackId);

        if(!subscription.callbacks.length) {
            removeItem(subscriptions, 'channel', channelName);
        }
    }

    this.unsubscribeAll = function (projectName, channel) {
        removeItem(subscriptions, 'channel', getChannelName(projectName, channel));
    }

    function getChannelName(projectName, channel) {
        return projectName + "/" + channel;
    }

    this.subscribeGeneral = function (callbackId, callback) {
        if(getItem(generalListeners, "id", callbackId)) {
            console.error("General callback '" + callbackId + "' is already registered");
            return;       //callback is already registered
        }

        generalListeners.push({
            id: callbackId,
            callback: callback
        });
    }

    this.getSubscriptions = function () {
        return subscriptions;
    }

    this.unsubscribeGeneral = function (callbackId) {
        removeItem(generalListeners, 'id', callbackId);
    }

});
