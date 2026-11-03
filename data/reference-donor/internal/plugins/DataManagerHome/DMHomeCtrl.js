angular.module("app.dmhome").controller("DMHomeCtrl", function($scope, SQEvents, DMHomeService, SkinService, $timeout, AppService) {
           
    $scope.homeLink = "";

    function loadHomeLink() {
        DMHomeService.link(function(response) {
            document.getElementById("qdm-home-iframe").src = response.link;

            $timeout(function () {
                updateSkin();
            }, 500);
        });
    }

    loadHomeLink();

    function updateSkin() {
        let theme = SkinService.selectedSkin.name == "Dark skin" ? 'dark' : 'light';
        console.log(`✓ Updating Home iframe theme to: ${theme}`);

        const iframe = document.getElementById("qdm-home-iframe");
        iframe.contentWindow.postMessage({ type: "SET_THEME", theme }, "*");
    }

    window.addEventListener("message", (e) => {
        if (e.data?.type === "OPEN_LINK") {
            AppService.openBrowser(e.data.link);
        }
    });

    window.parent.addListener("DMHome", [SQEvents.get("SKIN_CHANGED"), SQEvents.get("APP_CONFIGS_CHANGED")], function(event, data) {
        if (event === SQEvents.get("APP_CONFIGS_CHANGED")) {
            if (data && data.codes && data.codes.indexOf("homepage") !== -1) {
                loadHomeLink();
            }
        } else {
            updateSkin();
        }
    });
});
