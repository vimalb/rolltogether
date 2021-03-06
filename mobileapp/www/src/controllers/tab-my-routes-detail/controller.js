document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-routes/:routeId';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-routes-detail', {
      url: ROUTE_URL,
      views: {
        'tab-my-routes': {
          templateUrl: TEMPLATE_URL,
          controller: CONTROLLER_NAME
        }
      }
    });
  })
  .controller(CONTROLLER_NAME, function($scope, $stateParams, tripSearchService, userService, $state, CLIENT_SETTINGS) {
      $scope.route = {};
      $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;

      $scope.trips = [];
      $scope.pledges = {};
      $scope.totalDrivingMin = 0;
      $scope.totalDrivingCost = 0;
      $scope.totalTransitMin = 0;
      $scope.totalTransitCost = 0;
      $scope.profiles = [];

      $scope.$on('$ionicView.beforeEnter', function(){
        generateProfilePics();

        tripSearchService.getRoute($stateParams.routeId).then(function(route) {
          $scope.route = route;
          tripSearchService.getRouteTrips(route).then(function(trips) {
            $scope.trips = trips;
            $scope.totalDrivingMin = _.sum(trips, function(trip) {
              return trip.total_actual_duration_min;
            });
            $scope.totalDrivingCost = _.sum(trips, function(trip) {
              return trip.total_trip_cost_real;
            });
            $scope.totalTransitMin = _.sum(trips, function(trip) {
              return trip.total_transit_duration_min;
            });
            $scope.totalTransitCost = _.sum(trips, function(trip) {
              return trip.transit_trip_cost_real;
            });
          });
          tripSearchService.getPledges([route.route_id]).then(function(pledges) {
            _.assign($scope.pledges, pledges);
          });
        });
      });

      $scope.goRoutePledge = function(route) {
        $state.go('tab.my-routes-pledge', {routeId: route.route_id});
      }

      /*$scope.profilePic = function() {
        var url = $scope.SERVER_URL;

        var i = Math.floor(Math.random() * 50);
        var coinFlip = Math.random();
        if (coinFlip > 0.5) {
          console.log('pushing profile');
          return $scope.SERVER_URL +'/profiles/woman'+str(i%50)+'.jpg';
        } else {
          console.log('pushing profile');
          return $scope.SERVER_URL +'/profiles/man'+str(i%50)+'.jpg';
        }
        
        return 5;
      }*/

      generateProfilePics = function() {
        var numberPics = Math.floor(Math.random()*3) + 2;
        var pics = [];
 
        var i = 0;
        while (i < numberPics) {
          var url = $scope.SERVER_URL;
          var j = Math.floor(Math.random() * 50);
          var coinFlip = Math.random();

          if (coinFlip > 0.5) {
            url = url +'/profiles/woman'+j+'.jpg';
            $scope.profiles.push(url);
          } else {
            url = url +'/profiles/woman'+j+'.jpg';
            $scope.profiles.push(url);
          }
          i += 1;
        }
      }

      $scope.$on('$ionicView.beforeLeave', function(){
        $scope.route = {};
      });
  })


})();

