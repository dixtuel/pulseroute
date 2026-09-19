(function () {
  var KEY = "pulseroute-cookie-consent";
  var COOKIE_NAME = "pr_pref";

  function getPerf() {
    return typeof window !== "undefined" ? window.ClientPerf : null;
  }

  function getProfile() {
    var perf = getPerf();
    return perf ? perf.ClientProfiler.profile() : { tier: "high" };
  }

  function getSavedData() {
    var perf = getPerf();
    if (perf) {
      var decrypted = perf.ClientPref.load(COOKIE_NAME);
      if (decrypted) return decrypted;
    }
    try {
      var ls = localStorage.getItem(KEY);
      if (ls) return { c: ls === "accepted" ? 1 : 0 };
    } catch (e) {}
    return null;
  }

  function getStatus() {
    var data = getSavedData();
    if (!data) return null;
    return data.c === 1 ? "accepted" : "rejected";
  }

  function isLowMode() {
    var perf = getPerf();
    return perf ? perf.getState().isLowMode : false;
  }

  function saveConsent(status) {
    var perf = getPerf();
    var consentVal = status === "accepted" ? 1 : 0;

    // Cookie ONLY stores persistent site consent & timestamp, NEVER transient battery/network states!
    var payload = {
      c: consentVal,
      t: Math.floor(Date.now() / 1000)
    };

    if (perf) {
      perf.ClientPref.save(COOKIE_NAME, payload);
    }
    try {
      localStorage.setItem(KEY, status);
    } catch (e) {}
  }

  window.PulseRouteConsent = {
    getStatus: getStatus,
    isAccepted: function () {
      return getStatus() === "accepted";
    },
    isLowMode: isLowMode,
    toggleLowMode: function () {
      var perf = getPerf();
      if (perf) {
        var cur = perf.getState().isLowMode;
        perf.setOverride(cur ? "force_high" : "force_low");
        return !cur;
      }
      return false;
    },
    getProfile: function () {
      var perf = getPerf();
      return perf ? perf.getState() : {};
    }
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
    saveConsent("accepted");
    hideBanner();
    pushPendingAds();
  }

  function reject() {
    saveConsent("rejected");
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
