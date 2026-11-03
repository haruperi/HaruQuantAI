angular.module('app.data').controller('CustomDataCotCtrl', function ($rootScope, $scope, DMCustomDataService) {
    console.log("CustomDataCot controller initialized");

    $scope.action.onSelect = function (symbols2, grid2) {
        showPopup('#customDataCotModal');
    }

    $scope.onUpdateCot = function () {
        hidePopup('#customDataCotModal');

        DMCustomDataService.updateCot(function (result) {
            if (result && result.success) {
                $rootScope.showSuccess(result.success);
            }
        });
    }

    $scope.openHelp = function () {
        $rootScope.openLink('https://strategyquant.com/doc/strategyquant/cot');
    }
});
