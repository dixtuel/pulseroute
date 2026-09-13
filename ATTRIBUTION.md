# Açık Kaynak Lisans ve Atıf Bildirimleri (Attribution)

Bu belge, **PulseRoute** projesinde doğrudan veya dolaylı olarak kullanılan açık kaynaklı yazılımları, web sunucularını, CLI araçlarını ve kriptografik kütüphaneleri listeler. Tüm bileşenlerin telif hakları ilgili hak sahiplerine aittir.

---

## 1. Web Çerçevesi ve API

### [FastAPI](https://fastapi.tiangolo.com/)
- **Kullanım:** Asenkron HTTP ve REST API yönlendirme katmanı.
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2018 Sebastián Ramírez

### [Starlette](https://www.starlette.io/)
- **Kullanım:** FastAPI'nin altında yatan ASGI araç seti ve middleware mimarisi.
- **Lisans:** BSD-3-Clause Lisansı
- **Telif Hakkı:** Copyright (c) 2018, Encode OSS Ltd.

### [Uvicorn](https://www.uvicorn.org/)
- **Kullanım:** Yıldırım hızında ASGI sunucu uygulaması.
- **Lisans:** BSD-3-Clause Lisansı
- **Telif Hakkı:** Copyright (c) 2017-present, Encode OSS Ltd.

### [Pydantic](https://docs.pydantic.dev/)
- **Kullanım:** Veri doğrulama ve ayarların yönetimi (`pydantic-settings`).
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2017 to present Pydantic Services Inc. and individual contributors.

---

## 2. Veritabanı, Önbellek ve Veri Akışı

### [SQLAlchemy](https://www.sqlalchemy.org/)
- **Kullanım:** Asenkron ORM ve SQL soyutlama katmanı.
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2005-2026 Michael Bayer and contributors.

### [asyncpg](https://magicstack.github.io/asyncpg/)
- **Kullanım:** Yüksek başarımlı PostgreSQL asenkron sürücüsü.
- **Lisans:** Apache License 2.0
- **Telif Hakkı:** Copyright (c) 2016-present MagicStack Inc.

### [redis-py](https://github.com/redis/redis-py)
- **Kullanım:** Redis KV önbellekleme ve Redis Streams analitik veri toplama hattı.
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2019 Redis Ltd.

---

## 3. Komut Satırı Arayüzü (CLI) ve Terminal

### [Typer](https://typer.tiangolo.com/)
- **Kullanım:** Tip ipuçlarına dayalı modern CLI motoru.
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2019 Sebastián Ramírez

### [Rich](https://rich.readthedocs.io/)
- **Kullanım:** Terminalde zengin metin, tablolar ve renkli çıktılar.
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2020 Will McGugan

---

## 4. Güvenlik, Kriptografi ve Yardımcılar

### [cryptography (Fernet)](https://cryptography.io/)
- **Kullanım:** Webhook sırlarının at-rest şifrelenmesi (AES-128-CBC + HMAC-SHA256).
- **Lisans:** Apache License 2.0 / BSD-3-Clause
- **Telif Hakkı:** Copyright (c) Individual contributors.

### [passlib & bcrypt](https://foss.heptapod.net/python-libs/passlib)
- **Kullanım:** Parola özetleme ve güvenli kimlik doğrulama.
- **Lisans:** BSD Lisansı

### [PyJWT](https://pyjwt.readthedocs.io/)
- **Kullanım:** JSON Web Token (JWT) imzalama ve doğrulama.
- **Lisans:** MIT Lisansı
- **Telif Hakkı:** Copyright (c) 2015 José Padilla

### [qrcode](https://github.com/lincolnloop/python-qrcode)
- **Kullanım:** Kısaltılmış linkler için dinamik QR kod üretimi.
- **Lisans:** BSD-3-Clause Lisansı
- **Telif Hakkı:** Copyright (c) 2011, Lincoln Loop

---

## 5. Altyapı ve Test

### [Caddy Web Server](https://caddyserver.com/)
- **Kullanım:** Özel alan adları (Custom Domains) için otomatik On-Demand TLS sertifikalandırma ve ters proxy.
- **Lisans:** Apache License 2.0
- **Telif Hakkı:** Copyright (c) 2015-present The Caddy Authors

### [Pytest & pytest-asyncio & pytest-cov](https://pytest.org/)
- **Kullanım:** Otomatik test yürütme ve kod kapsama raporlaması.
- **Lisans:** MIT Lisansı

### [Ruff](https://astral.sh/ruff)
- **Kullanım:** Hızlı Python linter ve kod formatlayıcı.
- **Lisans:** MIT / Apache-2.0
- **Telif Hakkı:** Copyright (c) 2023 Astral Software Inc.

---

## 6. Lisans Bildirimi

Yukarıda listelenen bileşenlerin kendi lisans koşulları saklı kalmak kaydıyla, PulseRoute kaynak kodunun tamamı **[MIT Lisansı](LICENSE)** ile lisanslanmıştır.
