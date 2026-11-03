angular.module('app.portfoliocomposer').controller('PCSettingsCtrl', function ($scope, L) {
    console.log("PortfolioComposer - Settings controller initialized");

    $scope.mainTabs = {
        tabs: [{
                title: L.tsq('Portfolio composition'),
                dataItem: 'composition',
                dataTestid: 'pcomposer-tab-composition',
                templateUrl: '../../../plugins/PortfolioComposer/settings/composition/composition.html',
                controller: 'CompositionCtrl',
            },
            {
                title: L.tsq('Configuration - account, MM'),
                dataItem: 'configuration',
                dataTestid: 'pcomposer-tab-configuration',
                templateUrl: '../../../plugins/PortfolioComposer/settings/configuration/configuration.html',
                controller: 'ConfigurationCtrl',
            },
            {
                title: L.tsq('Automatic computation'),
                dataItem: 'autocomputation',
                dataTestid: 'pcomposer-tab-autocomputation',
                templateUrl: '../../../plugins/PortfolioComposer/settings/autocomputation/autocomputation.html',
                controller: 'AutocomputationCtrl',
            }
        ],
        onSelectTab: onTabChange,
    }

    function onTabChange(tab) {
    }

    function init() {
    }

    init();
});
