document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-pledges';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-pledges', {
        url: ROUTE_URL,
        views: {
          'tab-my-pledges': {
            templateUrl: TEMPLATE_URL,
            controller: CONTROLLER_NAME
          }
        }
      });
  })
  .controller(CONTROLLER_NAME, function($scope, tripSearchService, $state, CLIENT_SETTINGS) {
    console.log("Instantiating controller", CONTROLLER_NAME);

    $scope.my_pledges = [];
    $scope.friend_pledges = [];
    $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;


    $scope.refreshPledges = function() {
      tripSearchService.getPledges().then(function(pledges) {
        $scope.my_pledges = [];
        $scope.friend_pledges = [];
        _.forOwn(pledges, function(pledge) {
          if(pledge.mine) {
            $scope.my_pledges.push(pledge);
          }
          else if(pledge.has_friends) {
            $scope.friend_pledges.push(pledge);
          }
        });
      });
    }

    $scope.$on('$ionicView.beforeEnter', function(){
      $scope.refreshPledges();
    });

    $scope.goPledgeDetail = function(pledge) {
      $state.go('tab.my-pledges-detail', {routeId: pledge.route_id});
    }

    $scope.goMyRoutes = function() {
      $state.go('tab.my-routes');
    }


  })
})();

