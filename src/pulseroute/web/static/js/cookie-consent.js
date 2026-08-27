(function () {
  var KEY = "pulseroute-cookie-consent";

  function getStatus() {
    try {
      return localStorage.getItem(KEY);
    } catch (e) {
      return null;
    }
  }

  function setStatus(value) {
    try {
      localStorage.setItem(KEY, value);
    } catch (e) {
      /* private mode / storage disabled — banner just won't persist */
    }
  }

  window.PulseRouteConsent = {
    getStatus: getStatus,
    isAccepted: function () {
      return getStatus() === "accepted";
    },
  };

  function pushPendingAds() {
    document.querySelectorAll('ins.adsbygoogle[data-consent-pending="true"]').forEach(function (ins) {
      ins.removeAttribute("data-consent-pending");
      (window.adsbygoogle = window.adsbygoogle || []).push({});
    });
  }

  function hideBanner() {
    var el = document.getElementById("cookie-consent-banner");
    if (el) el.remove();
  }

  function accept() {
    setStatus("accepted");
    hideBanner();
    pushPendingAds();
  }

  function reject() {
    setStatus("rejected");
    hideBanner();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var status = getStatus();
    if (status === "accepted") {
      pushPendingAds();
    }

    var banner = document.getElementById("cookie-consent-banner");
    if (!banner) return;

    if (status !== null) {
      banner.remove();
      return;
    }

    banner.classList.remove("hidden");
    var acceptBtn = document.getElementById("cookie-consent-accept");
    var rejectBtn = document.getElementById("cookie-consent-reject");
    if (acceptBtn) acceptBtn.addEventListener("click", accept);
    if (rejectBtn) rejectBtn.addEventListener("click", reject);
  });
})();
