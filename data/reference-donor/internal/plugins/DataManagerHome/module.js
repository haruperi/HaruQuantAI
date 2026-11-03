angular.module('app.dmhome', ['sqplugin']).config(function (sqPluginProvider, SQEventsProvider) {
	
	sqPluginProvider.plugin("MainTab", 0, {
        title: Ltsq('Home'),
        dataItem: 'dm-home',
        dataTestid: 'dm-tab-home',
        templateUrl: '../../../plugins/DataManagerHome/home.html',
        controller: 'DMHomeCtrl',
    });
});
