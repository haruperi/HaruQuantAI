angular.module('app').provider('$stateManager', function($stateProvider) {
    // runtime dependencies for the service can be injected here, at the provider.$get() function.
    this.$get = function($q, $timeout, $state) { // for example
        return { 
            /**
             * Adds a new state.
             * It also checks if state with the name already exists, 
             * if so, it generates new name which is then returned.
             */
            addState: function(name, state) { 
                var i = 0;
                var tempName = angular.copy(name);
                var tempUrl = angular.copy(state.url);
                
                //if project with the same name exists, return null
                //every project should have a unique name

                var existingState = $state.get(tempName);
                if(existingState){
                    if(!existingState.removed){
                        return null;
                    }
                    else {
                        console.log(state);
                        existingState.removed = false;
                        existingState.data = state.data;
                        if(state.children){
                            existingState.children = state.children;
                        }
                        console.log(existingState);
                        return tempName;
                    }
                } 
                
                state.url = tempUrl;
                
                $stateProvider.state(tempName, state);
                return tempName;
            },
            //returns the names of the direct childs of the specified state
            getChildStates: function(name){
                var states = $state.get();
                var childs = [];
                
                for(var i=0; i<states.length; i++){
                    if(states[i].name.indexOf(name) == 0 && states[i].name.substring(name.length).indexOf(".") == -1){
                        childs.push(states[i].name);
                    }
                }
                
                return childs;
            }
        
        }
    }
});
