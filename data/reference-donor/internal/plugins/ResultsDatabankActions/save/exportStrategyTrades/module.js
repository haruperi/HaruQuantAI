angular.module('app.resultsdatabankactions.save.trades', ['sqplugin']).config(function(sqPluginProvider) {
    
    sqPluginProvider.plugin("ResultsDatabankAction", 100, {
        title: Ltsq("Save")+":"+Ltsq("Export strategy trades to CSV/XLSX"),
        action: 'ExportStrategyTrades',
        extension : {
            name : "csv",
            description : Ltsq("Comma separated files (.csv)")
        },
        controller: function($scope, SaveButtonService){
            $scope.onClick = function(item){
                SaveButtonService.onItemClick(item);
            }
        },
        dataTestid: "databank-action-save-trades",
        id: "databank-action-save-trades",
        icon: "fa fa-floppy-o",
    });
});
