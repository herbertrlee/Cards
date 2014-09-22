/**
 * @fileoverview
 * Provides methods for the Hello Endpoints sample UI and interaction with the
 * cah API.
 */

/** google global namespace for Google projects. */
var google = google || {};

/** appengine namespace for Google Developer Relations projects. */
google.appengine = google.appengine || {};

/** cah namespace*/
google.appengine.cah = google.appengine.cah || {};

/**
 * Initializes the application.
 * @param {string} apiRoot Root of the API's path.
 */
google.appengine.cah.init = function(apiRoot) {
  // Loads the OAuth and helloworld APIs asynchronously, and triggers login
  // when they have completed.
  var apisToLoad;
  var callback = function() {
    if (--apisToLoad == 0) {
      google.appengine.cah.enableButtons();
    }
  }

  apisToLoad = 1; // must match number of calls to gapi.client.load()
  gapi.client.load('cah', 'v1', callback, apiRoot);
};

/**
 * Enables the button callbacks in the UI.
 */
google.appengine.cah.enableButtons = function() {
  var getUserInfo = document.querySelector('#getUserInfo');
  getUserInfo.addEventListener('click', function(e) {
    google.appengine.cah.getUserInfo(
        document.querySelector('#id').value);
  });
};

/**
 * Prints a greeting to the greeting log.
 * param {Object} greeting Greeting to print.
 */
google.appengine.cah.print = function(string) {
  var element = document.createElement('div');
  element.classList.add('row');
  element.innerHTML = string;
  document.querySelector('#outputLog').appendChild(element);
};

/**
 * Gets a numbered greeting via the API.
 * @param {string} id ID of the greeting.
 */
google.appengine.cah.getUserInfo = function(id) {
  gapi.client.cah.userInfo.get({'id': id}).execute(
      function(resp) {
        if (!resp.code) {
          google.appengine.cah.print(resp.alias);
        }
      });
};