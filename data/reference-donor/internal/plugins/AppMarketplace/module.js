//product:SQUANT
angular.module('app.marketplace', ['sqplugin']).config(function (sqPluginProvider) {

    sqPluginProvider.plugin("NavigationPlugin", 100, {
        title: Ltsq('Marketplace'),
        appCode: 'MARKETPLACE',
        url: '../MARKETPLACE/index.html',
        iconClass: 'fa-shopping-bag',
        section: 1,
        iframeId: 'marketplace-frame',
        linkId: 'marketplace-link'
    });

});
