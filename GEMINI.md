# PulseRoute (repo) — Yönlendirme

Bu dosya yalnız yönlendirme içindir, hafıza/dokümantasyon DEĞİL. Ayrıntılı mimari, API haritası, webhook/QR sistemi, dashboard tasarım dili ve bilinen gotcha'lar için canonical doküman: **`/root/mikoshi-vds-docs/projects/pulseroute.md`**.

Bu dosya `CLAUDE.md`/`AGENTS.md`/`GEMINI.md` üçlüsünün bir parçasıdır (bkz. `/root/.claude/CLAUDE.md`), üçü birebir aynı tutulur.

## Hızlı Hatırlatıcılar (canonical dokümanın özeti değil, yalnız en kritik kurallar)

- Bu dizin **repo**'dur (public, MIT, [dixtuel/pulseroute](https://github.com/dixtuel/pulseroute)). Kavanoz/Dilek Ağacı/Downloader'ın aksine burada ayrı bir "prod kopyası" **yok** — proje kişisel kimlik bağlama verisi (gerçek e-posta, JSON-LD `@id`/`sameAs`) hiç taşımıyor, `OPERATOR_CONTACT_EMAIL` ve `SECRET_KEY` gibi gerçek değerler yalnızca dağıtımı kim yapıyorsa onun kendi `.env`'inde durur (`.gitignore`'da, hiçbir zaman commit edilmez).
- **2026-08-24 itibarıyla Render dağıtımı kaldırıldı** — README/kod/`render.yaml`'daki tüm Render referansları temizlendi, VDS'teki `pulseroute-ping.sh` keep-alive script'inden de çıkarıldı. Proje şu an hiçbir yerde canlı değil; kendi sunucunda çalıştırmak isteyen `deploy/docker-compose.yml` + kendi `.env`'ini kullanır (bkz. README "Self-Hosted Deployment"). Bu VDS'te canlıya alınırsa (yeni domain/Cloudflare Tunnel/systemd), o kurulum ayrı bir dizinde tutulmalı ve gerçek `.env`'i asla bu repoya karışmamalı — aynen diğer projelerdeki repo/prod ayrımı gibi.
- Kod değişikliği yaptığında (`src/pulseroute/`, `tests/`, `README.md`) doğrudan bu dizinde çalış — ayrı bir prod kopyasına senkron gerekmiyor, çünkü henüz yok.

Herhangi bir değişiklik yapmadan önce `pulseroute.md`'yi oku; güncel değilse orayı güncelle — buraya değil.
