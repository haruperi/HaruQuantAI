angular.module('app.resultsdatabankactions.tools', ['sqplugin']).config(function(sqPluginProvider) {
    
    sqPluginProvider.plugin("ResultsDatabankAction", 70, {
        title: Ltsq("Tools")+":",
        dataTestid: "databank-action-tools-menu",
        id: "databank-action-tools-menu",
    });

});
