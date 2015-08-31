document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-routes/:routeId/pledge';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-routes-pledge', {
      url: ROUTE_URL,
      views: {
        'tab-my-routes': {
          templateUrl: TEMPLATE_URL,
          controller: CONTROLLER_NAME
        }
      }
    });
  })
  .controller(CONTROLLER_NAME, function($scope, $stateParams, tripSearchService, userService) {
      $scope.route = {};
      $scope.pledgeTotal = 0;
      $scope.selectedIndex = 1;

      $scope.pledges = [
        {
          index: 0,
          name: "One Trip",
          price: 5.00,
          description: "Be one of the pioneers of Sao Paolo's new subway! Guarantee your spot by buying a ticket on YOUR ROUTE now"
        },
        {
          index: 1,
          name: "Five Pack",
          price: 20.00,
          description: "Good things come in bulk. Give more support to Sao Paolo's subway system and save! Buy four train tickets and get one free!"
        }
      ];

      $scope.$on('$ionicView.beforeEnter', function(){
        tripSearchService.getRoute($stateParams.routeId).then(function(route) {
          $scope.route = route;
        });
      });

      $scope.$on('$ionicView.beforeLeave', function(){
        $scope.route = {};
        $scope.pledges = [];
      });

      $scope.selectPledge = function(pledge) {
        $scope.pledgeTotal = $scope.pledgeTotal + pledge.price;
        $scope.selectedIndex = pledge.index;
      }
  })

})();

