document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-pledges/:routeId';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic', 'ngCordova'])
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
  .controller(CONTROLLER_NAME, function($scope, $stateParams, tripSearchService, userService, $state, $cordovaSocialSharing, CLIENT_SETTINGS, $timeout) {
      $scope.pledges = {};
      $scope.route = {};
      $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;

      $scope.$on('$ionicView.beforeEnter', function(){
        console.log('stateParams', $stateParams);
        tripSearchService.getRoute($stateParams.routeId).then(function(route) {
          $scope.route = route;
          tripSearchService.getPledges([route.route_id]).then(function(pledges) {
            _.assign($scope.pledges, pledges);
          });
        });
      });

      $scope.$on('$ionicView.beforeLeave', function(){
        $scope.route = {};
      });

      $scope.goRoutePledge = function(route) {
        $timeout(function() {
          $state.go('tab.my-routes-pledge', {routeId: route.route_id});
        }, 10);
        $state.go('tab.my-routes');
      }

      $scope.shareOnFacebook = function () {
        var message = null;
        var image = null;
        var link = $scope.SERVER_URL+'/share/'+$scope.route.route_id;
        
        $cordovaSocialSharing
          .shareViaFacebook(message, image, link)
          .then(function(result) {
            console.log(link, 'shared via facebook!');
          }, function(err) {
            // An error occurred. Show a message to the user
             console.log(link, 'Facebook share failed');
             console.dir(err.toString());
          });
      }

  })


})();

