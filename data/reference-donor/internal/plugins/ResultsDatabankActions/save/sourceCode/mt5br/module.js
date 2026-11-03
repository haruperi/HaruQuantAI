//product:BUILDER
//product:OPTIMIZER
//product:RETESTER
//product:TASKMANAGER
angular.module('app.resultsdatabankactions.save.sourceCode.mt5br', ['sqplugin']).config(function(sqPluginProvider) {
    
    sqPluginProvider.plugin("ResultsDatabankAction", 31, {
        title: Ltsq("Save")+":"+Ltsq("Source code")+":"+Ltsq("Expert Advisor for MetaTrader5 (Brazil) (*.MQ5)"),
        extension : {
            name : "mq5",
            description : Ltsq("MetaTrader 5 Expert Advisor (Brazil) (.MQ5)"),
        },
        controller: function($scope, SaveButtonService){
            $scope.onClick = function(item){
                SaveButtonService.onItemClick(item);
            }
        },
        dataTestid: "databank-action-sourcecode-mt5-br",
        id: "databank-action-sourcecode-mt5-br"
    });
});
