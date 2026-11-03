angular.module('app.resultsdatabankactions.portfolio', ['sqplugin']).config(function(sqPluginProvider) {
    
    sqPluginProvider.plugin("ResultsDatabankAction", 60, {
        title: Ltsq("Portfolio") + ":",
        dataTestid: "databank-action-portfolio-menu",
        id: "databank-action-portfolio-menu"
    });
    
});
