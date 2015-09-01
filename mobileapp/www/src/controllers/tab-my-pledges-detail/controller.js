document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-pledges/:pledgeId';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-pledges-detail', {
      url: ROUTE_URL,
      views: {
        'tab-my-pledges': {
          templateUrl: TEMPLATE_URL,
          controller: CONTROLLER_NAME
        }
      }
    });
  })
  .controller(CONTROLLER_NAME, function($scope, $stateParams, tripSearchService, userService, $state) {
      $scope.pledge = {};
      $scope.route = {};

      $scope.$on('$ionicView.beforeEnter', function(){
        tripSearchService.getPledge($stateParams.pledgeId).then(function(pledge) {
          $scope.pledge = pledge;
          var routeId = pledge.routeId
          tripSearchService.getRoute(routeId).then(function(route) {
            $scope.route = route;
          });
        });
      });

      $scope.$on('$ionicView.beforeLeave', function(){
        $scope.route = {};
      });

      $scope.goRoutePledge = function(route) {
        $state.go('tab.my-routes-pledge', {routeId: route.routeId});
      }
  })


})();

