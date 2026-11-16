"use strict";

// Attach the paired-device bearer token to same-origin API requests.
// The token is created by /static/connect.html and remains in this browser's
// local storage for this PC origin only.
(() => {
  const originalFetch = window.fetch.bind(window);
  window.fetch = (input, init = {}) => {
    let url;
    try {
      url = new URL(typeof input === "string" ? input : input.url, window.location.href);
    } catch (_) {
      return originalFetch(input, init);
    }
    if (url.origin === window.location.origin && url.pathname.startsWith("/api/")) {
      const token = window.localStorage.getItem("pc_controller_token");
      if (token) {
        const headers = new Headers(init.headers || (input instanceof Request ? input.headers : undefined));
        headers.set("Authorization", "Bearer " + token);
        init = { ...init, headers };
      }
    }
    return originalFetch(input, init);
  };
})();
