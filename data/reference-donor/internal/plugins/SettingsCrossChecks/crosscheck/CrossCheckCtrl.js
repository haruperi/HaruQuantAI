angular.module('app.settings').controller('CrossCheckCtrl', function ($scope, $rootScope, SQEvents, UniqueIdGenerator) {
    console.log("CrossCheck controller initialized");

    // kebab-cased crosscheck class name for stable data-testids (crosscheck-settings-btn-<kebab>)
    $scope.kebab = toKebabCase;

    $scope.settingsChanged = function () {
        $scope.crosscheck.settingsChanged();
    }

    $scope.openSettings = function (acceptanceTab) {
        $scope.crosscheck.openSettings($scope.crosscheck, acceptanceTab);
    }

    $scope.$on("$destroy", function () {
        UniqueIdGenerator.removeId($scope.modalId);
    });

    $scope.modalId = UniqueIdGenerator.generateId();
});
