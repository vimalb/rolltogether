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
  .controller(CONTROLLER_NAME, function($scope, $stateParams, $state, tripSearchService, userService, CLIENT_SETTINGS) {
      $scope.route = {};
      $scope.currentPledge = 0;
      $scope.pledgeTotal = 20;
      $scope.selectedIndex = 1;
      $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;

      // XXX should probably be moved elsewhere
      $scope.pledgeLevels = [
        {
          index: 0,
          name: "One Trip",
          price: 5.00,
          description: "Be one of the pioneers of Sao Paulo's new subway! Guarantee your spot by buying a ticket on YOUR ROUTE now"
        },
        {
          index: 1,
          name: "Five Pack",
          price: 20.00,
          description: "Good things come in bulk. Give more support to Sao Paulo's subway system and save! Buy four train tickets and get one free!"
        },
        {
          index: 2,
          name: "Supporter of the Cause",
          price: 100.00,
          description: "Be the good samaritan your mom always told you to be. Do your best to make this happen and be rewarded with your first monthly pass!"
        }
      ];

      $scope.$on('$ionicView.beforeEnter', function(){
        tripSearchService.getRoute($stateParams.routeId).then(function(route) {
          $scope.route = route;
          tripSearchService.getPledge(route).then(function(pledge) {
            console.log('pledge', pledge);
            $scope.currentPledge = pledge.amount;
            _.each($scope.pledgeLevels, function(level) {
              console.log(level.price, pledge.amount);
              if(level.price == pledge.amount) {
                $scope.selectedIndex = level.index;
              }
            });
          });
        });
      });

      $scope.$on('$ionicView.beforeLeave', function(){
        $scope.route = {};
        $scope.pledges = [];
      });

      $scope.selectPledge = function(pledge) {
        $scope.pledgeTotal = pledge.price;
        $scope.selectedIndex = pledge.index;
      }

      $scope.makePledge = function() {
        tripSearchService.makePledge($scope.route, $scope.pledgeTotal).then(function() {
          $scope.currentPledge = $scope.pledgeTotal;

        });
      }

      $scope.goToRoutes = function() {
        $state.go('tab.my-routes');
      }

  })

})();

