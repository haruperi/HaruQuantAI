angular.module("sqplugin", ['ui.router']).provider("sqPlugin", function ($stateProvider, $urlRouterProvider) {
    var plugins = [];
    var popups = [];
    var instance = this;
    
    function createState(state){
        var stateName = state.name;
        $stateProvider.state(stateName, state);
    };
    
    function createComboStructure(plugin, combos, titles){
        var currentArray = combos;

        for(var i=0; i<titles.length; i++){
            var title = titles[i];
            if(!title.length) break;

            var end = i == titles.length - 1;
            var item = null;

            for(var a=0; a<currentArray.length; a++){
                if(currentArray[a].title == title){
                    item = currentArray[a];
                    break;
                }
            }

            if(item == null){
                item = { title : title };
                currentArray.push(item);
            }

            if(end){
                var correctTitle = item.title;
                angular.merge(item, plugin);
                item.title = correctTitle;
            }
            else {
                item.options = item.options || [];
                currentArray = item.options;
            }
        }
    }

    this.plugin = function(extensionPoint, position, plugin) {
        plugin.extensionPoint = extensionPoint;
        plugin.position = position;
        
        if(plugin.uiState){
            createState(plugin.uiState);
            console.log("Navigation plugin added", plugin);
        }
        plugins.push(plugin);
    };
    
    this.addPopupWindow = function(templateUrl, controller, product){
        popups.push({
            templateUrl: templateUrl,
            controller: controller,
            product: product
        })
    };

    this.getPlugins = function(extensionPoint){
        var tmp = [];
                
        for(var i=0; i<plugins.length; i++){
            if(plugins[i].extensionPoint == extensionPoint) {
                
                if(plugins[i].product){
                    try {
                        var products = plugins[i].product.split(',');
                        if(products.indexOf(window.appConfig.product) < 0) continue;
                    } catch(err){
                        console.error("Cannot parse popup products.", popup);
                    }
                }

                tmp.push(plugins[i]);
            }
        }

        // sort plugins by their position
        tmp.sort(function(a, b) {
            return a.position - b.position;
        });
        
        return tmp;
    };

    this.$get = function() {
        return {
            getPlugins: instance.getPlugins,
            getPopups: function() {
                var productPopups = [];

                for(var i=0; i<popups.length; i++) {
                    var popup = popups[i];

                    if(popup.product){
                        try {
                            var products = popup.product.split(',');
                            if(products.indexOf(window.appConfig.product) < 0) continue;
                        } catch(err){
                            console.error("Cannot parse popup products.", popup);
                        }
                    }

                    productPopups.push(popup);
                }

                return productPopups;
            },
            getButtons: function(extensionPoint){
                var actionPlugins = instance.getPlugins(extensionPoint);
                var buttons = [];
                
                for(var i=0; i<actionPlugins.length; i++){
                    var plugin = actionPlugins[i];
                    var index = plugin.title.indexOf(':');
                    
                    if(index < 0){
                        buttons.push(plugin);
                    }
                }
                return buttons;
            },
            getCombos: function(extensionPoint){
                var actionPlugins = instance.getPlugins(extensionPoint);
                var combos = [];
        
                for(var i=0; i<actionPlugins.length; i++){
                    var plugin = angular.copy(actionPlugins[i]);
                    var titles = plugin.title.split(':');
        
                    if(titles.length < 2) continue;

                    if(plugin.title.substr(plugin.title.length - 1, 1) == ':'){
                        titles.splice(titles.length - 1, 1);
                    }
        
                    createComboStructure(plugin, combos, titles);
                }
                
                return combos;
            },
            addPlugin: function(extensionPoint, position, plugin){
                instance.plugin(extensionPoint, position, plugin);  
            }
        }
    };
});
