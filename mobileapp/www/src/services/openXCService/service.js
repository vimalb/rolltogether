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
        checkForNewTrips: function() {
          console.log("OpenXC checking for new trips");
          var deferred = $q.defer();

          var latest_url =  CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().user_id + '/latest_trip_info';
          $http.get(latest_url).then(function(resp) {
            var latest_time = new Date(resp.data.local_timestamp);
            if((new Date() - latest_time)/(1000*60) > 15) {
              var url = CLIENT_SETTINGS.SERVER_URL + '/api/users/' + userService.getCurrentUser().user_id + '/open_xc';
              $http.get(url).then(function(resp) {
                deferred.resolve(resp.data);
              });
            }
            else {
              deferred.resolve(resp.data);
            }
          });

          return deferred.promise;
        },



      };

    });


})();
