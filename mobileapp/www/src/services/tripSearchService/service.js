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
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/my-routes';
          /*
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          */
          deferred.resolve([ 
            { routeId: 200 },
            { routeId: 201 },
            ])
          return deferred.promise;
        },

        getAllRoutes: function() {
          console.log("Fetching all routes");
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/all-routes';
          /*
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          */
          deferred.resolve([ 
            { routeId: 300 },
            { routeId: 301 },
            ])
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

        getRoute: function(routeId) {
          console.log("Fetching route", routeId);
          var deferred = $q.defer();
          var url = CLIENT_SETTINGS.SERVER_URL + '/api/routes/' + routeId.toString();
          /*
          $http.get(url).then(function(resp) {
            deferred.resolve(resp.data);
          });
          */
          deferred.resolve(
            { routeId: routeId }
          );
          return deferred.promise;
        },

      };

    });
  
  
})();
