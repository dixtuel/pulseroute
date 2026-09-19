/**
 * client-perf.js — Real-Time Adaptive Performance, Hardware Profiler & Compact Cookie Engine
 *
 * Architecture:
 * 1. CompactCookie: Compact authenticated symmetric stream cipher for session/consent cookies.
 *    (Cookies do NOT store transient hardware/battery states. Cookies are strictly for site/user preferences).
 * 2. DynamicPerfMonitor: Truly reactive real-time monitor for hardware, battery saver, Save-Data,
 *    network changes, old WebView engines and runtime frame drops. Dispatches dynamic events when
 *    device conditions change (e.g. charging plugged in/unplugged, battery drops, user toggles Data Saver).
 */
(function (global) {
  "use strict";

  // =========================================================================
  // 1. PURE JS SHA-256 & HMAC-SHA256 (Zero-dep, Works across ancient WebViews)
  // =========================================================================
  var K = [
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5,
    0xd807aa98, 0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174,
    0xe49b69c1, 0xefbe4786, 0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da,
    0x983e5152, 0xa831c66d, 0xb00327c8, 0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967,
    0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13, 0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85,
    0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819, 0xd6990624, 0xf40e3585, 0x106aa070,
    0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a, 0x5b9cca4f, 0x682e6ff3,
    0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7, 0xc67178f2
  ];

  function sha256Words(words, len) {
    var H = [0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19];
    var W = new Array(64);
    words[len >> 2] |= 0x80 << (24 - (len % 4) * 8);
    words[(((len + 8) >> 6) << 4) + 15] = len * 8;

    for (var i = 0; i < words.length; i += 16) {
      var a = H[0], b = H[1], c = H[2], d = H[3], e = H[4], f = H[5], g = H[6], h = H[7];
      for (var j = 0; j < 64; j++) {
        if (j < 16) {
          W[j] = words[i + j] | 0;
        } else {
          var gamma0 = ((W[j - 15] >>> 7) | (W[j - 15] << 25)) ^ ((W[j - 15] >>> 18) | (W[j - 15] << 14)) ^ (W[j - 15] >>> 3);
          var gamma1 = ((W[j - 2] >>> 17) | (W[j - 2] << 15)) ^ ((W[j - 2] >>> 19) | (W[j - 2] << 13)) ^ (W[j - 2] >>> 10);
          W[j] = (gamma1 + W[j - 7] + gamma0 + W[j - 16]) | 0;
        }
        var ch = (e & f) ^ (~e & g);
        var maj = (a & b) ^ (a & c) ^ (b & c);
        var sigma0 = ((a >>> 2) | (a << 30)) ^ ((a >>> 13) | (a << 19)) ^ ((a >>> 22) | (a << 10));
        var sigma1 = ((e >>> 6) | (e << 26)) ^ ((e >>> 11) | (e << 21)) ^ ((e >>> 25) | (e << 7));
        var t1 = (h + sigma1 + ch + K[j] + W[j]) | 0;
        var t2 = (sigma0 + maj) | 0;
        h = g; g = f; f = e; e = (d + t1) | 0;
        d = c; c = b; b = a; a = (t1 + t2) | 0;
      }
      H[0] = (H[0] + a) | 0; H[1] = (H[1] + b) | 0; H[2] = (H[2] + c) | 0; H[3] = (H[3] + d) | 0;
      H[4] = (H[4] + e) | 0; H[5] = (H[5] + f) | 0; H[6] = (H[6] + g) | 0; H[7] = (H[7] + h) | 0;
    }
    var res = [];
    for (var k = 0; k < 8; k++) {
      res.push((H[k] >>> 24) & 0xff, (H[k] >>> 16) & 0xff, (H[k] >>> 8) & 0xff, H[k] & 0xff);
    }
    return res;
  }

  function bytesToWords(bytes) {
    var words = [];
    for (var i = 0; i < bytes.length; i++) {
      words[i >> 2] |= bytes[i] << (24 - (i % 4) * 8);
    }
    return words;
  }

  function hmacSha256(keyBytes, msgBytes) {
    var blockSize = 64;
    if (keyBytes.length > blockSize) {
      keyBytes = sha256Words(bytesToWords(keyBytes), keyBytes.length);
    }
    var oKeyPad = new Array(blockSize);
    var iKeyPad = new Array(blockSize);
    for (var i = 0; i < blockSize; i++) {
      var k = i < keyBytes.length ? keyBytes[i] : 0;
      oKeyPad[i] = k ^ 0x5c;
      iKeyPad[i] = k ^ 0x36;
    }
    var innerMsg = iKeyPad.concat(msgBytes);
    var innerHash = sha256Words(bytesToWords(innerMsg), innerMsg.length);
    var outerMsg = oKeyPad.concat(innerHash);
    return sha256Words(bytesToWords(outerMsg), outerMsg.length);
  }

  function strToUtf8(str) {
    var utf8 = unescape(encodeURIComponent(str));
    var arr = [];
    for (var i = 0; i < utf8.length; i++) arr.push(utf8.charCodeAt(i));
    return arr;
  }

  function utf8ToStr(arr) {
    var str = '';
    for (var i = 0; i < arr.length; i++) str += String.fromCharCode(arr[i]);
    return decodeURIComponent(escape(str));
  }

  function bytesToHex(arr) {
    var hex = '';
    for (var i = 0; i < arr.length; i++) {
      var b = arr[i].toString(16);
      if (b.length === 1) b = '0' + b;
      hex += b;
    }
    return hex;
  }

  function hexToBytes(hex) {
    var arr = [];
    for (var i = 0; i < hex.length; i += 2) {
      arr.push(parseInt(hex.substr(i, 2), 16));
    }
    return arr;
  }

  var DEFAULT_SECRET = "mikoshi-vds-shared-cookie-secret-key-2026";

  var CompactCookie = {
    encrypt: function (data, secret) {
      var key = strToUtf8(secret || DEFAULT_SECRET);
      var plaintext = strToUtf8(JSON.stringify(data));
      var iv = [];
      for (var i = 0; i < 4; i++) {
        iv.push(Math.floor(Math.random() * 256));
      }
      var keystream = [];
      var blockNum = 0;
      while (keystream.length < plaintext.length) {
        var b1 = (blockNum >> 8) & 0xff;
        var b2 = blockNum & 0xff;
        var blockMsg = iv.concat([b1, b2]);
        var blockHash = hmacSha256(key, blockMsg);
        keystream = keystream.concat(blockHash);
        blockNum++;
      }
      var ciphertext = [];
      for (var j = 0; j < plaintext.length; j++) {
        ciphertext.push(plaintext[j] ^ keystream[j]);
      }
      var tagMsg = iv.concat(ciphertext);
      var tagHash = hmacSha256(key, tagMsg).slice(0, 8);
      return 'v1_' + bytesToHex(iv) + '_' + bytesToHex(ciphertext) + '_' + bytesToHex(tagHash);
    },

    decrypt: function (tokenStr, secret) {
      if (!tokenStr || typeof tokenStr !== 'string') return null;
      var parts = tokenStr.split('_');
      if (parts.length !== 4 || parts[0] !== 'v1') return null;
      var iv = hexToBytes(parts[1]);
      var ciphertext = hexToBytes(parts[2]);
      var tag = hexToBytes(parts[3]);
      if (iv.length !== 4 || tag.length !== 8) return null;

      var key = strToUtf8(secret || DEFAULT_SECRET);
      var tagMsg = iv.concat(ciphertext);
      var expectedTag = hmacSha256(key, tagMsg).slice(0, 8);
      for (var t = 0; t < 8; t++) {
        if (tag[t] !== expectedTag[t]) return null;
      }

      var keystream = [];
      var blockNum = 0;
      while (keystream.length < ciphertext.length) {
        var b1 = (blockNum >> 8) & 0xff;
        var b2 = blockNum & 0xff;
        var blockMsg = iv.concat([b1, b2]);
        var blockHash = hmacSha256(key, blockMsg);
        keystream = keystream.concat(blockHash);
        blockNum++;
      }
      var plaintext = [];
      for (var j = 0; j < ciphertext.length; j++) {
        plaintext.push(ciphertext[j] ^ keystream[j]);
      }
      try {
        return JSON.parse(utf8ToStr(plaintext));
      } catch (e) {
        return null;
      }
    }
  };

  // =========================================================================
  // 2. DYNAMIC REAL-TIME PERFORMANCE & ENVIRONMENT MONITOR
  // =========================================================================
  var nav = typeof navigator !== 'undefined' ? navigator : {};
  var ua = nav.userAgent || '';

  // Static Browser / Engine Analysis (computed once at boot)
  var isAndroidWebView = /Version\/[\d.]+.*Chrome\/[\d.]+/i.test(ua) || /\bwv\b/i.test(ua);
  var isIosWebView = /(iPhone|iPod|iPad).*AppleWebKit(?!.*Safari)/i.test(ua) ||
    /FBAN|FBAV|Instagram|Twitter|Line|Snapchat/i.test(ua);
  var isWebView = isAndroidWebView || isIosWebView;

  var chromeMatch = ua.match(/Chrome\/(\d+)/i);
  var chromeVer = chromeMatch ? parseInt(chromeMatch[1], 10) : null;
  var androidMatch = ua.match(/Android\s+([\d.]+)/i);
  var androidVer = androidMatch ? parseFloat(androidMatch[1]) : null;
  var isOldWebView = (chromeVer !== null && chromeVer < 90) || (androidVer !== null && androidVer <= 8);

  var cores = nav.hardwareConcurrency || 4;
  var mem = nav.deviceMemory || 4;
  var isLowHardware = cores <= 2 || mem <= 2;

  // Dynamic Runtime State (changes dynamically over time without page reload)
  var dynamicState = {
    batteryCharging: true,
    batteryLevel: 1.0,
    isLowBattery: false,
    saveData: false,
    effectiveType: '4g',
    isSlowNet: false,
    reducedMotion: false,
    isStruggling: false, // Frame-drop indicator
    userOverride: null   // 'force_low' | 'force_high' | null
  };

  var listeners = [];

  function getState() {
    var reasons = [];
    if (isWebView) reasons.push('webview');
    if (isOldWebView) reasons.push('old_webview');
    if (isLowHardware) reasons.push('low_hardware');
    if (dynamicState.isLowBattery) reasons.push('low_battery_' + Math.round(dynamicState.batteryLevel * 100) + '%');
    if (dynamicState.saveData) reasons.push('save_data');
    if (dynamicState.isSlowNet) reasons.push('slow_net_' + dynamicState.effectiveType);
    if (dynamicState.reducedMotion) reasons.push('reduced_motion');
    if (dynamicState.isStruggling) reasons.push('frame_drops');

    var autoLow = isOldWebView || isLowHardware || dynamicState.isLowBattery ||
                  dynamicState.saveData || dynamicState.isSlowNet ||
                  dynamicState.reducedMotion || dynamicState.isStruggling;

    var effectiveLow = autoLow;
    if (dynamicState.userOverride === 'force_low') effectiveLow = true;
    if (dynamicState.userOverride === 'force_high') effectiveLow = false;

    return {
      isLowMode: effectiveLow,
      isAutoLow: autoLow,
      userOverride: dynamicState.userOverride,
      isWebView: isWebView,
      isOldWebView: isOldWebView,
      isLowHardware: isLowHardware,
      battery: {
        charging: dynamicState.batteryCharging,
        level: dynamicState.batteryLevel,
        isLow: dynamicState.isLowBattery
      },
      network: {
        saveData: dynamicState.saveData,
        effectiveType: dynamicState.effectiveType,
        isSlow: dynamicState.isSlowNet
      },
      isStruggling: dynamicState.isStruggling,
      dprCap: effectiveLow ? 1 : (typeof window !== 'undefined' ? Math.min(window.devicePixelRatio || 1, 2) : 1),
      fpsTarget: effectiveLow ? 30 : 60,
      reasons: reasons
    };
  }

  function notify() {
    var s = getState();
    if (typeof document !== 'undefined' && document.documentElement) {
      if (s.isLowMode) {
        document.documentElement.classList.add('low-mode');
      } else {
        document.documentElement.classList.remove('low-mode');
      }
    }
    for (var i = 0; i < listeners.length; i++) {
      try {
        listeners[i](s);
      } catch (e) {
        console.error('Perf listener error:', e);
      }
    }
    if (typeof window !== 'undefined' && window.dispatchEvent && typeof CustomEvent !== 'undefined') {
      window.dispatchEvent(new CustomEvent('perfstatechange', { detail: s }));
    }
  }

  // --- Real-Time Battery Monitoring ---
  if (typeof navigator !== 'undefined' && navigator.getBattery) {
    navigator.getBattery().then(function (battery) {
      function updateBattery() {
        dynamicState.batteryCharging = battery.charging;
        dynamicState.batteryLevel = battery.level;
        // Low battery condition: Unplugged AND level <= 20%
        dynamicState.isLowBattery = (!battery.charging && battery.level <= 0.20);
        notify();
      }
      battery.addEventListener('chargingchange', updateBattery);
      battery.addEventListener('levelchange', updateBattery);
      updateBattery();
    }).catch(function () {});
  }

  // --- Real-Time Network / Save-Data Monitoring ---
  var conn = nav.connection || nav.mozConnection || nav.webkitConnection;
  if (conn) {
    function updateConn() {
      dynamicState.saveData = conn.saveData === true;
      dynamicState.effectiveType = conn.effectiveType || '4g';
      dynamicState.isSlowNet = ['slow-2g', '2g', '3g'].indexOf(dynamicState.effectiveType) !== -1;
      notify();
    }
    if (conn.addEventListener) {
      conn.addEventListener('change', updateConn);
    }
    updateConn();
  }

  // --- Real-Time Reduced Motion Monitoring ---
  if (typeof window !== 'undefined' && window.matchMedia) {
    var mql = window.matchMedia('(prefers-reduced-motion: reduce)');
    dynamicState.reducedMotion = mql.matches;
    function updateMotion(e) {
      dynamicState.reducedMotion = e.matches;
      notify();
    }
    if (mql.addEventListener) {
      mql.addEventListener('change', updateMotion);
    } else if (mql.addListener) {
      mql.addListener(updateMotion);
    }
  }

  // --- Frame-Drop Dynamic Watcher ---
  // Call `ClientPerf.recordFrame(deltaMs)` inside requestAnimationFrame
  var slowFrameCounter = 0;
  function recordFrame(deltaMs) {
    if (deltaMs > 45) { // Frame took > 45ms (< 22 FPS)
      slowFrameCounter++;
      if (slowFrameCounter > 25 && !dynamicState.isStruggling) {
        dynamicState.isStruggling = true;
        notify();
      }
    } else {
      if (slowFrameCounter > 0) slowFrameCounter--;
      if (slowFrameCounter === 0 && dynamicState.isStruggling) {
        dynamicState.isStruggling = false;
        notify();
      }
    }
  }

  // Check saved manual override in localStorage (optional client-side only preference)
  if (typeof localStorage !== 'undefined') {
    try {
      var savedOverride = localStorage.getItem('perf_mode_override');
      if (savedOverride === 'force_low' || savedOverride === 'force_high') {
        dynamicState.userOverride = savedOverride;
      }
    } catch (e) {}
  }

  function setOverride(mode) {
    // mode: 'force_low' | 'force_high' | 'auto'
    if (mode === 'force_low' || mode === 'force_high') {
      dynamicState.userOverride = mode;
      if (typeof localStorage !== 'undefined') {
        try { localStorage.setItem('perf_mode_override', mode); } catch (e) {}
      }
    } else {
      dynamicState.userOverride = null;
      if (typeof localStorage !== 'undefined') {
        try { localStorage.removeItem('perf_mode_override'); } catch (e) {}
      }
    }
    notify();
  }

  function subscribe(fn) {
    listeners.push(fn);
    fn(getState());
    return function unsubscribe() {
      var idx = listeners.indexOf(fn);
      if (idx !== -1) listeners.splice(idx, 1);
    };
  }

  // =========================================================================
  // 3. COOKIE & CONSENT MANAGER (Cookie = Permanent User/Session Data Only)
  // =========================================================================
  var ClientPref = {
    getCookie: function (name) {
      if (typeof document === 'undefined') return null;
      var match = document.cookie.match(new RegExp('(?:^|; )' + name.replace(/([.$?*|{}()[\\]\\\/+^])/g, '\\$1') + '=([^;]*)'));
      return match ? decodeURIComponent(match[1]) : null;
    },

    setCookie: function (name, value, days) {
      if (typeof document === 'undefined') return;
      var expires = "";
      if (days) {
        var d = new Date();
        d.setTime(d.getTime() + (days * 24 * 60 * 60 * 1000));
        expires = "; expires=" + d.toUTCString();
      }
      var isSecure = typeof location !== 'undefined' && location.protocol === 'https:';
      document.cookie = name + "=" + encodeURIComponent(value) + expires + "; path=/; SameSite=Lax" + (isSecure ? "; Secure" : "");
    },

    load: function (cookieName, secret) {
      var raw = this.getCookie(cookieName);
      var data = raw ? CompactCookie.decrypt(raw, secret) : null;
      if (!data && typeof localStorage !== 'undefined') {
        try {
          var ls = localStorage.getItem(cookieName);
          if (ls) data = JSON.parse(ls);
        } catch (e) {}
      }
      return data;
    },

    save: function (cookieName, data, secret) {
      data.t = Math.floor(Date.now() / 1000);
      var encrypted = CompactCookie.encrypt(data, secret);
      this.setCookie(cookieName, encrypted, 365);
      if (typeof localStorage !== 'undefined') {
        try {
          localStorage.setItem(cookieName, JSON.stringify(data));
        } catch (e) {}
      }
      return encrypted;
    }
  };

  // Initial class application
  if (typeof document !== 'undefined' && document.documentElement) {
    if (getState().isLowMode) {
      document.documentElement.classList.add('low-mode');
    }
  }

  var ClientPerf = {
    CompactCookie: CompactCookie,
    getState: getState,
    setOverride: setOverride,
    subscribe: subscribe,
    recordFrame: recordFrame,
    ClientPref: ClientPref
  };

  global.ClientPerf = ClientPerf;
  if (typeof module !== 'undefined' && module.exports) {
    module.exports = ClientPerf;
  }
})(typeof window !== 'undefined' ? window : (typeof global !== 'undefined' ? global : this));
