angular.module('app.resultstabs.stockpicker', ['sqplugin']).config(function(sqPluginProvider) {

    sqPluginProvider.plugin("ResultsTab", 99, {
        title: Ltsq('Stockpicker log'),
        dataItem: 'stockpicker',
        dataTestid: 'results-tab-stockpicker',
        templateUrl: '../../../plugins/ResultsStockpicker/stockpicker.html',
        controller: 'StockpickerCtrl',
        hideAfterInit: true
    });
});
