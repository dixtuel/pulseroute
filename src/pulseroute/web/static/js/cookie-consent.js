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
    var data = getSavedData();
    if (data && data.l !== undefined) {
      return data.l === 1;
    }
    return getProfile().tier === "low";
  }

  function savePreferences(status, lowMode) {
    var perf = getPerf();
    var profile = getProfile();
    var isLow = lowMode !== undefined ? !!lowMode : isLowMode();
    var consentVal = status === "accepted" ? 1 : 0;

    var payload = {
      c: consentVal,
      l: isLow ? 1 : 0,
      w: profile.isWebView ? 1 : 0,
      t: Math.floor(Date.now() / 1000)
    };

    if (perf) {
      perf.ClientPref.save(COOKIE_NAME, payload);
      perf.ClientPref.applyLowModeClass(isLow);
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
      var next = !isLowMode();
      savePreferences(getStatus() || "accepted", next);
      return next;
    },
    getProfile: getProfile
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
    savePreferences("accepted", isLowMode());
    hideBanner();
    pushPendingAds();
  }

  function reject() {
    savePreferences("rejected", isLowMode());
    hideBanner();
  }

  document.addEventListener("DOMContentLoaded", function () {
    var perf = getPerf();
    var low = isLowMode();
    if (perf) {
      perf.ClientPref.applyLowModeClass(low);
    }

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
