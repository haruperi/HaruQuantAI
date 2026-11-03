angular.module('app.resultstabs.resultsprofilechart', ['sqplugin', 'app.resultstabs.resultsplugins'])
    .config(function(sqPluginProvider) {
        sqPluginProvider.plugin("ResultsTab", 55, {
            title: 'Profile chart',
            dataItem: 'profileChart',
            dataTestid: 'results-tab-profileChart',
            templateUrl: '../../../plugins/ResultsProfileChart/profileChart.html',
            controller: 'ProfileChartCtrl'
        });
    });
