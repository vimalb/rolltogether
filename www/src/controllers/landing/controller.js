document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');

var ROUTE_URL = '/landing';
var MODULE_NAME = 'mainApp'+URI(CONTROLLER_URL).path().replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ngRoute'])
  .config(function($routeProvider) {
    $routeProvider.when(ROUTE_URL, {
      templateUrl: TEMPLATE_URL,
      controller: CONTROLLER_NAME
    });
  })
  .controller(CONTROLLER_NAME, function($scope, CLIENT_SETTINGS, $http) {
    console.log("Loading controller", CONTROLLER_NAME);
    var SERVER_URL = CLIENT_SETTINGS.SERVER_URL;

    $scope.SERVER_URL = SERVER_URL;
    $scope.routes = [];
    $scope.selected_route = {}
    $scope.summary = {};
    $scope.trip_chart = {};
    $scope.pledge_chart = {};
    $scope.route_trip_chart = {};
    $scope.route_pledge_chart = {};

    $scope.setSelectedRoute = function(route) {
      $scope.selected_route = route;

      $http.get(SERVER_URL+'/api/dashboard/trip_chart/'+route.route_id).then(function(resp){
        $scope.route_trip_chart = resp.data;
      });

      $http.get(SERVER_URL+'/api/dashboard/pledge_chart/'+route.route_id).then(function(resp){
        $scope.route_pledge_chart = resp.data;
      });

    }

    $http.get(SERVER_URL+'/api/dashboard/routes').then(function(resp){
      $scope.routes = resp.data;
      $scope.setSelectedRoute($scope.routes[0]);
    });

    $http.get(SERVER_URL+'/api/dashboard/summary').then(function(resp){
      $scope.summary = resp.data;
    });

    $http.get(SERVER_URL+'/api/dashboard/trip_chart').then(function(resp){
      $scope.trip_chart = resp.data;
    });

    $http.get(SERVER_URL+'/api/dashboard/pledge_chart').then(function(resp){
      $scope.pledge_chart = resp.data;
    });
    

    
  });
  
  
})();