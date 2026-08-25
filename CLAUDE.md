# PulseRoute (repo) — Yönlendirme

Bu dosya yalnız yönlendirme içindir, hafıza/dokümantasyon DEĞİL. Ayrıntılı mimari, API haritası, webhook/QR sistemi, dashboard tasarım dili ve bilinen gotcha'lar için canonical doküman: **`/root/mikoshi-vds-docs/projects/pulseroute.md`**.

Bu dosya `CLAUDE.md`/`AGENTS.md`/`GEMINI.md` üçlüsünün bir parçasıdır (bkz. `/root/.claude/CLAUDE.md`), üçü birebir aynı tutulur.

## Hızlı Hatırlatıcılar (canonical dokümanın özeti değil, yalnız en kritik kurallar)

- Bu dizin **repo**'dur (public, MIT, [dixtuel/pulseroute](https://github.com/dixtuel/pulseroute)). Kavanoz/Dilek Ağacı/Downloader'ın aksine burada ayrı bir "prod kopyası" **yok** — proje kişisel kimlik bağlama verisi (gerçek e-posta, JSON-LD `@id`/`sameAs`) hiç taşımıyor, `OPERATOR_CONTACT_EMAIL` ve `SECRET_KEY` gibi gerçek değerler yalnızca dağıtımı kim yapıyorsa onun kendi `.env`'inde durur (`.gitignore`'da, hiçbir zaman commit edilmez).
- **2026-08-24 itibarıyla Render dağıtımı kaldırıldı** — README/kod/`render.yaml`'daki tüm Render referansları temizlendi, VDS'teki `pulseroute-ping.sh` keep-alive script'inden de çıkarıldı.
- **2026-08-25: Bu VDS'e entegrasyon başladı (henüz canlı değil)** — `sely.tr` domaininin (link kısaltma servisi) paylaşımlı instance'ı olarak planlandı. `/srv/mikoshi-vds/containers/docker-compose.yml`'e `pulseroute-postgres`/`pulseroute-redis`/`pulseroute-app` servisleri eklendi (kendi bundled Caddy'si KULLANILMADI — ana `Caddyfile`'daki `on_demand_tls`/`ask` bloğuna entegre edildi), gerçek secrets `/srv/mikoshi-vds/containers/pulseroute.env`'de (repoya asla karışmaz). Cloudflare DNS/Tunnel ingress (`sely.tr` kök → `127.0.0.1:8010`) hazır. **Container'lar henüz `docker compose up` ile başlatılmadı** (VDS bellek durumu nedeniyle onay bekleniyor) — durumu `docker ps --filter name=pulseroute` ile doğrula, varsayımla "canlı" deme.
- Kod değişikliği yaptığında (`src/pulseroute/`, `tests/`, `README.md`) doğrudan bu dizinde çalış — ayrı bir prod kopyasına senkron gerekmiyor, çünkü henüz yok.

Herhangi bir değişiklik yapmadan önce `pulseroute.md`'yi oku; güncel değilse orayı güncelle — buraya değil.

## Obsidian MCP

`mikoshi-vds-docs` bir Obsidian vault'udur ve kalıcı çalışan bir Obsidian servisi (MCP/Local REST API) var. O depoda dosya taşıma/yeniden adlandırma gibi link-kıran işlemler için mevcutsa Obsidian MCP tercih edilir, basit metin düzenlemesi için düz dosya erişimi yeterlidir. Ayrıntı: `mikoshi-vds-docs/operations/obsidian.md`.
