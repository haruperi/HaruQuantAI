angular.module('app.resultstabs.portfoliocomposer', ['sqplugin']).config(function(sqPluginProvider) {

    sqPluginProvider.plugin("ResultsTab", 99, {
        title: Ltsq('Log'),
        dataItem: 'portfolioComposerLog',
        dataTestid: 'results-tab-portfolioComposerLog',
        templateUrl: '../../../plugins/ResultsPortfolioComposerLog/portfolioComposerLog.html',
        controller: 'PortfolioComposerLogCtrl',
        hideAfterInit: true
    });
});
