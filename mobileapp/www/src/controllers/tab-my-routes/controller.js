document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-routes';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-routes', {
        url: ROUTE_URL,
        views: {
          'tab-my-routes': {
            templateUrl: TEMPLATE_URL,
            controller: CONTROLLER_NAME
          }
        }
      });
  })
  .controller(CONTROLLER_NAME, function($scope, tripSearchService, $state, CLIENT_SETTINGS) {
    console.log("Instantiating controller", CONTROLLER_NAME);

    $scope.myRoutes = [];
    $scope.popularRoutes = [];
    $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;
    $scope.pledges = {};
    $scope.routeTripCounts = {};

    $scope.refreshRoutes = function() {
      tripSearchService.getMyRoutes().then(function(routes) {
        $scope.myRoutes = routes;
        console.log('routes', routes);
        var routeIds = _.map(routes, function(route) { return route.route_id; });
        tripSearchService.getPledges(routeIds).then(function(pledges) {
          _.assign($scope.pledges, pledges);
        });
        tripSearchService.getRouteTripCounts(routeIds).then(function(routeTripCounts) {
          _.assign($scope.routeTripCounts, routeTripCounts);
        });
      });
      tripSearchService.getPopularRoutes().then(function(routes) {
        $scope.popularRoutes = routes;
        var routeIds = _.map(routes, function(route) { return route.route_id; });
        tripSearchService.getPledges(routeIds).then(function(pledges) {
          _.assign($scope.pledges, pledges);
        });
        tripSearchService.getRouteTripCounts(routeIds).then(function(routeTripCounts) {
          _.assign($scope.routeTripCounts, routeTripCounts);
        });
      });
    }

    $scope.$on('$ionicView.beforeEnter', function(){
      $scope.refreshRoutes();
    });

    $scope.goRouteDetail = function(routeId) {
      $state.go('tab.my-routes-detail', {routeId: routeId});
    }

    $scope.goRoutePledgeDetail = function(routeId) {
      $state.go('tab.my-routes-pledge', {routeId: routeId});
    }


  })

  
})();

