angular.module("sqevents", []).provider("SQEvents", function(){
    
    this.add = function(eventName, eventValue){
        var value = events[eventName];
        if(value){
            console.error("Error: Event '"+eventName+"' already exists.");
        }
        else {
            events[eventName] = eventValue;
        }
    };
    
    this.$get = function() {
        var iface = {
            get: function(eventName){
                var value = events[eventName];
                if(value){
                    return value;
                }
                else {
                    console.error("Error: Event '"+eventName+"' doesn't exist.");
                }
            },
            add: function(eventName, eventValue){
                instance.add(eventName, eventValue);
            },
            has: function(eventName){
                if(events[eventName]) return true;
                else return false;
            }
        }

        new ListenersHandler(iface);

        if(window.appConfig.product == 'SQUANT' || window.appConfig.product == 'QDM' || window.appConfig.product == 'PORTFOLIOCOMPOSER'){
            window.broadcastEvent = iface.notifyListeners;
            window.addListener = iface.addListener;
            window.removeListener = iface.removeListener;
        }

        return iface;
    };

    var instance = this;
    var events = [];

});
