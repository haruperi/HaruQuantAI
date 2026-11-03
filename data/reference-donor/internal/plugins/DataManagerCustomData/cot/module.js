angular.module('app.data').config(function(sqPluginProvider) {

    sqPluginProvider.plugin('DataManagerActionCustomData', 80, {
        title: Ltsq('Update COT'),
        templateUrl: '../../../plugins/DataManagerCustomData/cot/customDataCot.html',
        controller: 'CustomDataCotCtrl',
        source: 'custom-da-ta',
        class: 'custom-data',
        id: "datamanager-custom-data-cot",
        key: "updateCot"
    });
});
