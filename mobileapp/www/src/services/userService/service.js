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
    .factory(SERVICE_NAME, function($q, CLIENT_SETTINGS, $http, $rootScope) {
      console.log("Instantiating service", SERVICE_NAME);

      function rand4() {
        return Math.floor((1 + Math.random()) * 0x10000)
          .toString(16)
          .substring(1);
      }

      $rootScope.currentUser = JSON.parse(localStorage.getItem('currentUser') || JSON.stringify({
        'username': undefined,
        'name': '',
        'profilePic': '',
        'isFacebookEnabled': false,
        'isTwitterEnabled': false,
        'isInstagramEnabled': false,
      }));
      if(!$rootScope.currentUser.userId) {
        $rootScope.currentUser.userId = rand4()+rand4()+rand4()+rand4();
      }

      $rootScope.$watch('currentUser', _.debounce(function() {
        console.log('currentUser changed to', $rootScope.currentUser);
        localStorage.setItem('currentUser', JSON.stringify($rootScope.currentUser));
      }, 1000), true);

      return {
        getCurrentUser: function() {
          return $rootScope.currentUser;
        },
      };

    });
  
  
})();