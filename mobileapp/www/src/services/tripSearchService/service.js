document.APP_MODULES = document.APP_MODULES || [];

(function(){

var SERVICE_URL = document.currentScript.src;
var SERVICE_PATH = URI(SERVICE_URL).path();
SERVICE_PATH = SERVICE_PATH.substring(SERVICE_PATH.indexOf('/src/services/'));

var MODULE_NAME = 'mainApp'+SERVICE_PATH.replace('/src','').replace('/service.js','').replace(/\//g,'.');
var SERVICE_NAME = SERVICE_PATH.replace('/src/services/','').replace('/service.js','').replace(/\//g,'');

document.APP_MODULES.push(MODULE_NAME);

console.log(MODULE_NAME, "Registering service", SERVICE_NAME);
angular.module(MODULE_NAME, [])
    .factory(SERVICE_NAME, function($q, CLIENT_SETTINGS, $http, userService) {
      console.log("Instantiating service", SERVICE_NAME);

      return {
        getMyFeed: function() {
          console.log("Fetching my feed");
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/feed';
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getMyRoutes: function() {
          console.log("Fetching my routes");
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/routes';
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getPopularRoutes: function() {
          console.log("Fetching popular routes");
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/routes/popular';
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getPledges: function(routeIds) {
          console.log("Fetching pledges for route_ids", routeIds);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/pledges';
          $http.post(url, JSON.stringify({route_ids: routeIds})).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        makePledge: function(route, amount) {
          console.log("Pledging", amount, " to route ", route.route_id);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/pledges/'+route.route_id.toString();
          $http.put(url, JSON.stringify({amount: amount})).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getPledge: function(route) {
          console.log("Fetching pledge for route ", route.route_id);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/pledges/'+route.route_id.toString();
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },


        getTrip: function(tripId) {
          console.log("Fetching trip", tripId);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/trips/' + tripId.toString();
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getRouteTrips: function(route) {
          console.log("Fetching trips for route", route.route_id);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/trips_for_route/'+route.route_id.toString();
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getRouteTripCounts: function() {
          console.log("Fetching route trip counts");
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().userId + '/route_trip_counts';
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },

        getRoute: function(routeId) {
          console.log("Fetching route", routeId);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/routes/all/' + routeId.toString();
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          return deferred.promise;
        },


      };

    });


})();
