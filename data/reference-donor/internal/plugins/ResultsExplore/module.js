angular.module('app.resultstabs.explore', ['sqplugin']).config(function(sqPluginProvider) {

    sqPluginProvider.plugin("ResultsTab", 99, {
        title: Ltsq('Explore'),
        dataItem: 'explore',
        dataTestid: 'results-tab-explore',
        templateUrl: '../../../plugins/ResultsExplore/explore.html',
        controller: 'ExploreCtrl',
        hideAfterInit: true
    });
});
