function ListenersHandler(object){
    
    var listeners = [];
    var generalEvent = 'general';

    object.addGeneralListener = function(listenerId, callback){
        listeners.push({
            id : listenerId,
            events : [generalEvent],
            callback : callback
        });
    }

    object.addListener = function(listenerId, events, callback){
        listeners.push({
            id : listenerId,
            events : events,
            callback : callback
        });
    }

    object.removeListener = function(listenerId){
        removeItem(listeners, 'id', listenerId);
    }

    object.notifyListeners = function(event, data){
        event = event || generalEvent;
        
        for(var i=0; i<listeners.length; i++){
            if(isSubscribed(listeners[i], event) && listeners[i].callback) {
                //one failing listener must not abort the notifier nor the remaining listeners
                try {
                    listeners[i].callback(event, data);
                } catch(err) {
                    console.error("Listener '" + listeners[i].id + "' failed on event '" + event + "'", err);
                }
            }
        }
    }

    object.notifyListener = function(listenerId, event, data){
        event = event || generalEvent;

        var listener = getItem(listeners, 'id', listenerId);
        if(listener && isSubscribed(listener, event) && listener.callback) listener.callback(event, data);
    }

    object.subscribe = function(listenerId, events){
        var listener = getItem(listeners, 'id', listenerId);
        if(!listener) return;

        for(var i=0; i<events.length; i++){
            if(!isSubscribed(listener, events[i])){
                listener.events.push(events[i]);
            }
        }
    }

    object.unsubscribe = function(listenerId, events){
        var listener = getItem(listeners, 'id', listenerId);
        if(!listener) return;

        for(var i=0; i<events.length; i++){
            var index = listener.events.indexOf(events[i]);
            if(index < 0) continue;

            listener.events.splice(index, 1);
        }
    }

    function isSubscribed(listener, event){
        if(!listener.events) {
            return false;
        }

        return listener.events.indexOf(generalEvent) >=0 || listener.events.indexOf(event) >= 0;
    }

}
