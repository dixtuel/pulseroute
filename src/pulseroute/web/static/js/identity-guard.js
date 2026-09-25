/**
 * Identity & Contact Protection Guard
 * Clean, scrape-protected presentation of operator contact and legal identity.
 * Employs DOM decoy traps to foil automated web scrapers while keeping the UI accessible.
 */
(function () {
    'use strict';

    function initIdentityProtection() {
        var contactLinks = document.querySelectorAll('.protected-contact-link, .protected-contact');

        contactLinks.forEach(function (el) {
            // Avoid duplicate listeners
            if (el.getAttribute('data-guard-initialized')) return;
            el.setAttribute('data-guard-initialized', 'true');

            el.addEventListener('click', function (e) {
                e.preventDefault();
                handleContactAction(el);
            });

            el.addEventListener('keydown', function (e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    handleContactAction(el);
                }
            });
        });
    }

    function handleContactAction(el) {
        var email = el.getAttribute('data-email');
        if (!email) {
            var userSpan = el.querySelector('.protected-user');
            var domainSpan = el.querySelector('.protected-domain');
            if (userSpan && domainSpan) {
                email = userSpan.textContent.trim() + '@' + domainSpan.textContent.trim();
            } else {
                return;
            }
        }

        // Copy to clipboard
        if (navigator && navigator.clipboard && navigator.clipboard.writeText) {
            navigator.clipboard.writeText(email).then(function () {
                showCopiedFeedback(el);
            }).catch(function () {});
        }

        // Open mailto client
        window.location.href = 'mailto:' + email;
    }

    function showCopiedFeedback(el) {
        var existingBadge = el.querySelector('.protected-copied-badge');
        if (existingBadge) return;

        var isEn = el.getAttribute('data-locale') === 'en';
        var badge = document.createElement('span');
        badge.className = 'protected-copied-badge ml-1 px-1.5 py-0.5 rounded text-[10px] font-mono bg-emerald-500/20 text-emerald-400 border border-emerald-500/30';
        badge.textContent = isEn ? 'copied' : 'kopyalandı';

        el.appendChild(badge);
        setTimeout(function () {
            if (badge && badge.parentNode) {
                badge.parentNode.removeChild(badge);
            }
        }, 2200);
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initIdentityProtection);
    } else {
        initIdentityProtection();
    }
})();
