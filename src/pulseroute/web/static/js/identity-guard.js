/**
 * Identity & Contact Protection Guard
 * Obfuscates contact details against web scrapers and harvesting bots.
 */
(function () {
    'use strict';

    // Character code definitions (never stored as plaintext string)
    var NAME_CODES = [65, 115, 114, 305, 110, 32, 75, 305, 108, 305, 199]; // Asrın Kılıç
    var USER_CODES = [97, 115, 114, 105, 110, 107, 108, 99, 99]; // asrinklcc
    var DOMAIN_DIXTUEL_CODES = [100, 105, 120, 116, 117, 101, 108, 46, 116, 114]; // dixtuel.tr
    var DOMAIN_SELY_CODES = [115, 101, 108, 121, 46, 116, 114]; // sely.tr

    function decodeCodes(codes) {
        return String.fromCharCode.apply(null, codes);
    }

    function getEmail(domainType) {
        var u = decodeCodes(USER_CODES);
        var d = domainType === 'sely' ? decodeCodes(DOMAIN_SELY_CODES) : decodeCodes(DOMAIN_DIXTUEL_CODES);
        return u + '@' + d;
    }

    function initIdentityProtection() {
        // Protect contact email spans
        var contactSpans = document.querySelectorAll('.protected-contact');
        contactSpans.forEach(function (el) {
            var rawCodes = el.getAttribute('data-codes');
            var email;
            if (rawCodes) {
                try {
                    var parsed = JSON.parse(rawCodes);
                    if (Array.isArray(parsed) && parsed.length > 0) {
                        email = decodeCodes(parsed);
                    }
                } catch (e) {}
            }
            if (!email) {
                var domain = el.getAttribute('data-domain') || 'dixtuel';
                email = getEmail(domain);
            }
            
            var isEn = el.getAttribute('data-locale') === 'en';

            var link = document.createElement('a');
            link.href = 'mailto:' + email;
            link.className = 'protected-contact-link';
            link.textContent = email;
            link.title = isEn ? 'Click to send email' : 'E-posta göndermek için tıklayın';

            el.innerHTML = '';
            el.appendChild(link);
        });

        // Protect name spans
        var nameSpans = document.querySelectorAll('.protected-name');
        nameSpans.forEach(function (el) {
            el.textContent = decodeCodes(NAME_CODES);
        });
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initIdentityProtection);
    } else {
        initIdentityProtection();
    }
})();
