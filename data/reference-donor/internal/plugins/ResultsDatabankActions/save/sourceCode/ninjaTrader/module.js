//product:BUILDER
//product:OPTIMIZER
//product:RETESTER
//product:TASKMANAGER
// Poradie 45: za obchodnymi platformami (mc 10, mt4 20, mt5 30, mt5br 31, jforex 40) a pred
// genericky XML (50) / pseudo kod (60). Nazov musi presne sedet s <name> v Main.tpl generatora
// (internal/extend/Code/NinjaTrader/Main.tpl) - podla neho servlet vybera generator.
angular.module('app.resultsdatabankactions.save.sourceCode.ninjaTrader', ['sqplugin']).config(function(sqPluginProvider) {

    sqPluginProvider.plugin("ResultsDatabankAction", 45, {
        title: Ltsq("Save")+":"+Ltsq("Source code")+":"+Ltsq("NinjaTrader8 (*.cs)"),
        extension : {
            name : "cs",
            description : Ltsq("NinjaTrader8 Strategy (.CS)")
        },
        controller: function($scope, SaveButtonService){
            $scope.onClick = function(item){
                SaveButtonService.onItemClick(item);
            }
        },
        dataTestid: "databank-action-sourcecode-ninjatrader",
        id: "databank-action-sourcecode-ninjatrader"
    });
});
