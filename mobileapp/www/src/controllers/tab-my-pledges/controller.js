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
  .controller(CONTROLLER_NAME, function($scope, tripSearchService, $state) {
    console.log("Instantiating controller", CONTROLLER_NAME);

    $scope.routes = [];
    $scope.pledges = [];

    $scope.refreshRoutes = function() {
      tripSearchService.getAllRoutes().then(function(routes) {
        $scope.routes = routes;
      });
    }

    $scope.refreshPledges = function() {
      $scope.pledges = [
        {
          pledgeId: 0,
          amount: 5.00,
          routeId: 200
        },
        {
          pledgeId: 1, 
          amount: 100.00,
          routeId: 201
        }];
    }

    $scope.$on('$ionicView.beforeEnter', function(){
      $scope.refreshRoutes();
      $scope.refreshPledges();
    });

    $scope.goPledgeDetail = function(pledge) {
      $state.go('tab.my-pledges-detail', {pledgeId: pledge.pledgeId});
    }
  })
})();

