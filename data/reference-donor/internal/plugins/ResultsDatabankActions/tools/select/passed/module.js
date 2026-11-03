angular.module('app.resultsdatabankactions.tools.select.passed', ['sqplugin']).config(function(sqPluginProvider) {
    
    sqPluginProvider.plugin("ResultsDatabankAction", 102, {
        dataTestid: "databank-action-tools-select-passed",
        title: Ltsq("Tools")+":"+Ltsq("Select:Passed"),
        action: 'selectPassed',
        product: "RETESTER,TASKMANAGER",
        controller: function($scope, DatabankSelectService){

            $scope.onClick = function(item, tab){
                DatabankSelectService.onSelect(tab.getGrid(), true);
            }
            
        }
    });
});
