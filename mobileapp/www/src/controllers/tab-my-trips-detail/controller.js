document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-trips/:tripId';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-trips-detail', {
      url: ROUTE_URL,
      views: {
        'tab-my-trips': {
          templateUrl: TEMPLATE_URL,
          controller: CONTROLLER_NAME
        }
      }
    });
  })
  .controller(CONTROLLER_NAME, function($scope, $stateParams, $state, $timeout, tripSearchService, userService, CLIENT_SETTINGS) {
      $scope.trip = {};
      $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;

      $scope.$on('$ionicView.beforeEnter', function(){
        tripSearchService.getTrip($stateParams.tripId).then(function(trip) {
          $scope.trip = trip;
        });
      });

      $scope.$on('$ionicView.beforeLeave', function(){
        $scope.trip = {};
      });

      $scope.goRouteDetail = function(routeId) {
        $timeout(function() {
          $state.go('tab.my-routes-detail', {routeId: routeId});
          console.log('lolwut');
        }, 10);
        $state.go('tab.my-routes');
      }
    
  })

  
})();

