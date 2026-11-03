angular.module('app.dataHelp', ['sqplugin']).config(function (sqPluginProvider, SQEventsProvider) {
	
	sqPluginProvider.plugin("MainTab", 60, {
        title: Ltsq('Help'),
        dataItem: 'dm-help',
        dataTestid: 'dm-tab-help',
        templateUrl: '../../../plugins/DataManagerHelp/help.html',
    });
});
