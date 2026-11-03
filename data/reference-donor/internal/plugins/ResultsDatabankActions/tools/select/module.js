angular.module('app.resultsdatabankactions.tools.select', ['sqplugin']).config(function (sqPluginProvider) {

    sqPluginProvider.plugin("ResultsDatabankAction", 100, {
        dataTestid: "databank-action-tools-select",
        title: Ltsq("Tools")+":"+Ltsq("Select")+":",
        product: "RETESTER,TASKMANAGER",
        class: 'normal-submenu',
    });

});
