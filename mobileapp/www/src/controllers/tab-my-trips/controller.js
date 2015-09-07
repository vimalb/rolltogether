document.APP_MODULES = document.APP_MODULES || [];

(function(){

var CONTROLLER_URL = document.currentScript.src;
var TEMPLATE_URL = CONTROLLER_URL.replace('controller.js','view.html');
var CONTROLLER_PATH = URI(CONTROLLER_URL).path();
CONTROLLER_PATH = CONTROLLER_PATH.substring(CONTROLLER_PATH.indexOf('/src/controllers/'));

var ROUTE_URL = '/my-trips';
var MODULE_NAME = 'mainApp'+CONTROLLER_PATH.replace('/src','').replace('/controller.js','').replace(/\//g,'.');
var CONTROLLER_NAME = MODULE_NAME.replace(/\./g,'_').replace(/-/g,'_');
document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering route", ROUTE_URL);
angular.module(MODULE_NAME, ['ionic', 'ngStorage'])
  .config(function($stateProvider) {
    $stateProvider.state('tab.my-trips', {
        url: ROUTE_URL,
        views: {
          'tab-my-trips': {
            templateUrl: TEMPLATE_URL,
            controller: CONTROLLER_NAME
          }
        }
      });
  })
  .controller(CONTROLLER_NAME, function($scope, tripSearchService, openXCService, $state, $timeout, $localStorage, CLIENT_SETTINGS) {
    console.log("Instantiating controller", CONTROLLER_NAME);

    $scope.feedItems = [];
    $scope.profileData = null;
    $scope.SERVER_URL = CLIENT_SETTINGS.SERVER_URL;

    $scope.init = function() {
      if($localStorage.hasOwnProperty("accessToken") === true) {
        $http.get("https://graph.facebook.com/v2.2/me", { params: { access_token: $localStorage.accessToken, fields: "id,name,gender,location,website,picture,relationship_status", format: "json" }}).then(function(result) {
            $scope.profileData = result.data;
        }, function(error) {
            alert("There was a problem getting your profile.  Check the logs for details.");
            console.log(error);
        });
      } else {
        console.log("Not signed in");
      }
    }

    $scope.refreshFeedItems = function() {
      tripSearchService.getMyFeed().then(function(feedItems) {
        $scope.feedItems = feedItems;
      }).finally(function() {
        $scope.$broadcast('scroll.refreshComplete');
      });
    }

    $scope.goRefresh = function() {
      openXCService.checkForNewTrips().then(function(newTrip) {
        $scope.refreshFeedItems();
      });
    }

    $scope.$on('$ionicView.beforeEnter', function() {
      $scope.refreshFeedItems();
    });

    $scope.goTripDetail = function(tripId) {
      $state.go('tab.my-trips-detail', {tripId: tripId});
    }

    $scope.goRouteDetail = function(feedItem) {
      var routeId = feedItem.item_details.route.route_id;
      $timeout(function() {
        $state.go('tab.my-routes-detail', {routeId: routeId});
      }, 10);
      $state.go('tab.my-routes');
    }

    $scope.goPledgeDetail = function(feedItem) {
      var routeId = feedItem.item_details.pledge.route_id;
      $timeout(function() {
        $state.go('tab.my-pledges-detail', {routeId: routeId});
      }, 10);
      $state.go('tab.my-pledges');
    }

    $scope.goLogin = function() {
      $state.go('tab.login');
    }

  })

})();

