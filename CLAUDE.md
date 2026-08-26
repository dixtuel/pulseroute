# PulseRoute (repo) — Yönlendirme

Bu dosya yalnız yönlendirme içindir, hafıza/dokümantasyon DEĞİL. Ayrıntılı mimari, API haritası, webhook/QR sistemi, dashboard tasarım dili, Render/Neon/Upstash dağıtım detayları ve bilinen gotcha'lar için canonical doküman: **`/root/mikoshi-vds-docs/projects/pulseroute.md`**.

Bu dosya `CLAUDE.md`/`AGENTS.md`/`GEMINI.md` üçlüsünün bir parçasıdır (bkz. `/root/.claude/CLAUDE.md`), üçü birebir aynı tutulur.

## Repo vs Production Ayrımı (Kavanoz/Dilek Ağacı'ndan farklı bir model)

- Bu dizin (`/opt/pulseroute`) **public GitHub repo**'dur ([dixtuel/pulseroute](https://github.com/dixtuel/pulseroute), MIT). Kişisel kimlik bağlama verisi (gerçek e-posta, gerçek secret) burada **asla bulunmaz** — `.env` `.gitignore`'da, kod yalnız `pydantic` `Settings` (`src/pulseroute/core/config.py`) üzerinden env okur, hiçbir gerçek değer commit edilmez.
- Kavanoz/Dilek Ağacı'nın aksine burada **ikinci bir dosya sistemi kopyası (ayrı "prod checkout") yok** — production doğrudan bu GitHub reposundan Render'ın build/deploy pipeline'ıyla çalışır (`git push origin main` → Render otomatik yeniden build+deploy alır, `autoDeploy: commit`). Repo/production ayrımı bir dizin ayrımı değil, **secret yönetimi** ayrımıdır: gerçek `SECRET_KEY`/`DATABASE_URL`/`REDIS_URL`/`OPERATOR_CONTACT_EMAIL` değerleri yalnızca Render Dashboard'un Environment sekmesinde (veya `RENDER_API_KEY` ile CLI/API üzerinden) tutulur, repoya hiç dokunmaz.
- **2026-08-26: Render dağıtımı yeniden kuruldu.** (2026-08-24'te bilinçli olarak kaldırılmıştı — dashboard redesign'ı sırasında canlı örnek indirilmişti, teknik bir arıza değildi.) Servis: `pulseroute` (`srv-da7dqvou01pc7393osh0`, Render workspace "Ren Mikoshi", plan `free`, region `oregon`, runtime `python`). Domain: `ps.sely.tr` Cloudflare DNS (proxied CNAME) ile bu servise bağlandı ve doğrulandı; Render'ın kendi `pulseroute.onrender.com` adresi (`renderSubdomainPolicy: disabled`) kapatıldı — servis artık yalnız `ps.sely.tr` üzerinden erişilebilir.
- **DB/Cache henüz Render/VDS'in kendi add-on'ları değil, dış kartsız sağlayıcılara taşınıyor**: Postgres için **Neon** (expire olmuyor), cache için **Upstash** (Redis, expire olmuyor) — ikisi de bu not yazıldığında henüz açılmadı. Açılana kadar `DATABASE_URL` varsayılan SQLite fallback'te, `REDIS_URL` erişilemez durumda çalışıyor (kod bunu zaten sorunsuz `try/except` ile handle ediyor — bkz. `pulseroute.md`). Hesaplar açılınca `DATABASE_URL`/`REDIS_URL` Render env var olarak güncellenecek.
- VDS Docker Compose'daki (`/srv/mikoshi-vds/containers/docker-compose.yml`) `pulseroute-postgres`/`pulseroute-redis`/`pulseroute-app` servisleri artık **kullanılmıyor** (Render'a taşındı) — kaldırılıp kaldırılmayacağı ayrı bir karar, henüz kaldırılmadı, `docker ps -a --filter name=pulseroute` ile durumunu asla varsaymadan doğrula.
- Kod değişikliği yaptığında (`src/pulseroute/`, `tests/`, `README.md`) doğrudan bu dizinde çalış, `git push origin main` yeterli — Render otomatik deploy alır, ayrı bir prod kopyasına senkron gerekmez.

Herhangi bir değişiklik yapmadan önce `pulseroute.md`'yi oku; güncel değilse orayı güncelle — buraya değil.

## Obsidian MCP

`mikoshi-vds-docs` bir Obsidian vault'udur ve kalıcı çalışan bir Obsidian servisi (MCP/Local REST API) var. O depoda dosya taşıma/yeniden adlandırma gibi link-kıran işlemler için mevcutsa Obsidian MCP tercih edilir, basit metin düzenlemesi için düz dosya erişimi yeterlidir. Ayrıntı: `mikoshi-vds-docs/operations/obsidian.md`.
