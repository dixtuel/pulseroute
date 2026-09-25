(() => {
    const pairs = [
        ['PulseRoute — URL Shortener', 'PulseRoute — Bağlantı Kısaltıcı'],
        ['Self-hosted, open-source URL shortener with custom domains, click analytics, QR codes and webhooks.', 'Özel alan adları, tıklama analitiği, QR kodları ve webhook destekli açık kaynak bağlantı kısaltıcı.'],
        ['Links', 'Bağlantılar'], ['Board', 'Analiz'], ['Routes', 'Alan adları'], ['Settings', 'Ayarlar'],
        ['Log in', 'Giriş yap'], ['Sign up', 'Kayıt ol'], ['Switch workspace', 'Çalışma alanını değiştir'],
        ['Workspace', 'Çalışma alanı'], ['New workspace', 'Yeni çalışma alanı'], ['Sign out', 'Çıkış yap'],
        ['Links made without an account disappear after 24 hours.', 'Hesap açmadan oluşturulan bağlantılar 24 saat sonra silinir.'],
        ['Create a free account to keep them.', 'Bağlantılarınızı saklamak için ücretsiz hesap oluşturun.'], ['Create account', 'Hesap oluştur'],
        ['This server only accepts links on your own verified domain.', 'Bu sunucu yalnızca doğrulanmış kendi alan adınızda bağlantı oluşturmanıza izin verir.'],
        ['Sign in and add a domain to continue.', 'Devam etmek için giriş yapıp bir alan adı ekleyin.'],
        ['Where should this link go?', 'Bu bağlantı nereye yönlensin?'], ['Destination URL', 'Hedef URL'],
        ['Custom slug', 'Özel kısa kod'], ['(optional)', '(isteğe bağlı)'], ['Domain', 'Alan adı'],
        ["This server's domain", 'Bu sunucunun alan adı'], ['More options', 'Diğer seçenekler'],
        ['Send iPhone visitors to', 'iPhone ziyaretçilerini şuraya yönlendir'], ['Send Android visitors to', 'Android ziyaretçilerini şuraya yönlendir'],
        ['Tags', 'Etiketler'], ['Send visitors here once this link expires', 'Bağlantı süresi dolunca ziyaretçileri buraya yönlendir'],
        ['Visitors wait at least 5 seconds while the link is verified.', 'Bağlantı doğrulanırken ziyaretçiler en az 5 saniye bekler.'],
        ['Visitor IPs are anonymized (KVKK/GDPR)', 'Ziyaretçi IP adresleri anonimleştirilir (KVKK/GDPR)'],
        ['Shorten link', 'Bağlantıyı kısalt'], ['Your link is ready', 'Bağlantınız hazır'], ['destination', 'hedef'], ['short link', 'kısa bağlantı'],
        ['QR code', 'QR kodu'], ['Copy', 'Kopyala'], ['Anonymous links created in the last 24h', 'Son 24 saatte oluşturulan anonim bağlantılar'],
        ["Individual anonymous links aren't listed here, for privacy.", 'Gizlilik için anonim bağlantılar tek tek burada listelenmez.'],
        ['Your links', 'Bağlantılarınız'], ['Refresh', 'Yenile'], ['Loading…', 'Yükleniyor…'],
        ['See how your links are doing', 'Bağlantılarınızın performansını görün'], ['Sign in to see click activity for your links.', 'Bağlantılarınızın tıklama etkinliğini görmek için giriş yapın.'],
        ['Click activity across every link in this workspace.', 'Bu çalışma alanındaki tüm bağlantıların tıklama etkinliği.'],
        ['Total clicks', 'Toplam tıklama'], ['Unique visitors', 'Tekil ziyaretçi'], ['Filtered as bots', 'Bot olarak filtrelenenler'],
        ['By device', 'Cihaza göre'], ['By country', 'Ülkeye göre'], ['No location data yet.', 'Henüz konum verisi yok.'],
        ['Use your own domain', 'Kendi alan adınızı kullanın'],
        ['Sign in to connect a domain — links will read as yours, with automatic HTTPS.', 'Alan adı bağlamak için giriş yapın; bağlantılarınız size ait görünür ve HTTPS otomatik etkinleşir.'],
        ['Connect a domain you own so links read as yours. HTTPS is set up automatically.', 'Bağlantılarınızın size ait görünmesi için kendi alan adınızı bağlayın. HTTPS otomatik kurulur.'],
        ['Connect a domain', 'Alan adı bağla'], ['Point your DNS here to finish', 'Tamamlamak için DNS kayıtlarınızı buraya yönlendirin'],
        ['Sign in to manage your workspace.', 'Çalışma alanınızı yönetmek için giriş yapın.'],
        ["Your workspace's identity. More preferences are on the way.", 'Çalışma alanınızın kimliği. Yeni tercihler yakında eklenecek.'],
        ['Workspace name', 'Çalışma alanı adı'], ['Workspace slug', 'Çalışma alanı kısa kodu'],
        ['Sponsorlu Alan', 'Sponsored space'], ['REKLAM', 'AD'],
        ['PulseRoute Yüksek Hızlı Link Platformu', 'PulseRoute High-Speed Link Platform'],
        ['Özel alan adları, anlık tıklama grafikleri ve güvenli yönlendirme.', 'Custom domains, live click analytics, and secure redirects.'],
        ['Email', 'E-posta'], ['Password', 'Parola'], ['No account yet?', 'Henüz hesabınız yok mu?'], ['Create your account', 'Hesabınızı oluşturun'],
        ['Name', 'Ad'], ['(min. 8 characters)', '(en az 8 karakter)'], ['Slug', 'Kısa kod'], ['Create workspace', 'Çalışma alanı oluştur'],
        ['PulseRoute • Open-source URL shortener', 'PulseRoute • Açık kaynak bağlantı kısaltıcı'], ['Privacy', 'Gizlilik'], ['Terms', 'Kullanım şartları'],
        ['Accessibility', 'Erişilebilirlik'], ['Status', 'Durum'], ['Search…', 'Ara…'], ['View public stats', 'Herkese açık istatistikleri görüntüle'],
        ['Delete link', 'Bağlantıyı sil'], ['Expires', 'Süre doluyor'], ['Permanent', 'Kalıcı'], ['No links yet. Paste a URL above to create your first one.', 'Henüz bağlantı yok. İlk bağlantınızı oluşturmak için yukarıya bir URL yapıştırın.'],
        ["No temporary links yet — create one above. It'll last 24 hours.", 'Henüz geçici bağlantı yok. Yukarıdan bir tane oluşturun; 24 saat geçerli olur.'],
        ['Desktop', 'Masaüstü'], ['Mobile', 'Mobil'], ['Tablet', 'Tablet'], ['No verified domain yet — add one in Routes', 'Henüz doğrulanmış alan adı yok; Alan adları sekmesinden ekleyin'],
        ["This server's own domain", 'Bu sunucunun alan adı'], ['Always on', 'Her zaman açık'], ['Built in', 'Yerleşik'], ['Verified', 'Doğrulandı'], ['Awaiting DNS', 'DNS doğrulaması bekleniyor'],
        ['Re-check DNS', 'DNS kaydını yeniden kontrol et'], ['Check again', 'Yeniden kontrol et'], ['Remove domain', 'Alan adını kaldır'],
        ['Delete this link?', 'Bu bağlantı silinsin mi?'], ['Remove this domain?', 'Bu alan adı kaldırılsın mı?'],
        ["Couldn't create that account.", 'Hesap oluşturulamadı.'], ["That email and password don't match.", 'E-posta adresi veya parola hatalı.'],
        ["Couldn't create that workspace.", 'Çalışma alanı oluşturulamadı.'], ["Couldn't add that domain.", 'Alan adı eklenemedi.'],
        ["Couldn't create that link.", 'Bağlantı oluşturulamadı.'], ['Could not reach the server. Try again.', 'Sunucuya ulaşılamadı. Yeniden deneyin.'],
        ['Skip to terms', 'Şartlara geç'], ['Skip to content', 'İçeriğe geç'], ['PulseRoute home', 'PulseRoute ana sayfa'],
        ['Legal pages', 'Hukuki metinler'], ['Terms sections', 'Kullanım şartları bölümleri'], ['On this page', 'Bu sayfada'],
        ['The platform', 'Platform'], ['Acceptable use', 'Kabul edilebilir kullanım'], ['Accounts', 'Hesaplar'], ['Rate limits', 'İstek sınırları'],
        ['Warranty', 'Garanti'], ['Report abuse', 'Kötüye kullanım bildirimi'], ['Service terms · MIT open source', 'Hizmet şartları · MIT açık kaynak lisansı'],
        ['Terms of service', 'Hizmet şartları'], ['Clear standards for creating short links, protecting workspaces, and reporting harmful destinations.', 'Kısa bağlantı oluşturma, çalışma alanlarını koruma ve zararlı hedefleri bildirme kuralları.'],
        ['ACCEPTABLE USE', 'KABUL EDİLEBİLİR KULLANIM'], ['Nature of the platform', 'Platformun niteliği'],
        ['PulseRoute is an open-source link-shortening and redirection platform distributed under the MIT License. These terms govern your interaction with this specific running instance. If you self-host PulseRoute, you are the independent operator of your instance and set its policies.', 'PulseRoute, MIT Lisansı ile sunulan açık kaynaklı bir bağlantı kısaltma ve yönlendirme platformudur. Bu şartlar, bu hizmet örneğini kullanımınızı düzenler. PulseRoute’u kendi sunucunuzda barındırıyorsanız örneğinizin bağımsız işletmecisi sizsiniz ve politikalarını siz belirlersiniz.'],
        ['Do not use this service to shorten or distribute:', 'Bu hizmeti aşağıdakileri kısaltmak veya dağıtmak için kullanmayın:'],
        ['Phishing sites, credential harvesters, fake banking portals, or deceptive sign-in pages.', 'Oltalama siteleri, kimlik bilgisi toplayıcıları, sahte bankacılık portalları veya aldatıcı giriş sayfaları.'],
        ['Malware, spyware, ransomware, trojans, or hazardous executable files such as', 'Zararlı yazılım, casus yazılım, fidye yazılımı, Truva atı veya aşağıdaki gibi tehlikeli çalıştırılabilir dosyalar:'],
        ['Internal network probes, loopback destinations, or cloud metadata services (SSRF).', 'Dahili ağ taramaları, yerel döngü hedefleri veya bulut metadata servisleri (SSRF).'],
        ['Recursive redirect chains or attempts to mask the shortener domain to evade threat detection.', 'Tehdit tespitini atlatmak için iç içe yönlendirme zincirleri veya kısaltıcı alan adını gizleme girişimleri.'],
        ['Scams, fraudulent crypto schemes, unlawful counterfeit material, spam campaigns, botnets, or mass unsolicited messages.', 'Dolandırıcılık, sahte kripto şemaları, hukuka aykırı taklit ürünler, spam kampanyaları, botnetler veya toplu istenmeyen iletiler.'],
        ['Destination URLs for desktop, iOS, Android, regional routing, and expiry fallbacks are screened when links are created or updated. Known malicious destinations, restricted file formats, and internal IP ranges are blocked.', 'Masaüstü, iOS, Android, bölgesel yönlendirme ve süre sonu hedef URL’leri bağlantı oluşturulurken veya güncellenirken denetlenir. Bilinen zararlı hedefler, kısıtlı dosya biçimleri ve dahili IP aralıkları engellenir.'],
        ['Accounts and workspaces', 'Hesaplar ve çalışma alanları'],
        ['Each registered user receives an isolated workspace. Links, custom domains, tags, and click analytics are available only to members of that workspace.', 'Her kayıtlı kullanıcıya ayrı bir çalışma alanı verilir. Bağlantılar, özel alan adları, etiketler ve tıklama analitiği yalnızca o çalışma alanının üyelerine açıktır.'],
        ['You are responsible for the destinations and content linked through your workspace.', 'Çalışma alanınız üzerinden bağlanan hedeflerden ve içeriklerden siz sorumlusunuz.'],
        ['Anonymous links expire automatically after 24 hours. After expiry, they are removed and cannot be claimed, edited, or recovered.', 'Anonim bağlantıların süresi 24 saat sonra otomatik dolar. Süre dolunca silinir; sahiplenilemez, düzenlenemez veya kurtarılamaz.'],
        ['Rate limits and abuse response', 'İstek sınırları ve kötüye kullanım bildirimi'],
        ['Sliding-window rate limits protect the service from automated abuse. Repeated failed sign-ins trigger a 10-minute IP lockout. Abuse reports about phishing or malware can quarantine a link immediately. Other report types are counted once per reporter signal during the deduplication window; {{ abuse_quarantine_threshold }} distinct reports quarantine a link, and {{ abuse_delete_threshold }} can result in permanent deletion.', 'Kayan pencere hız sınırları hizmeti otomatik kötüye kullanıma karşı korur. Tekrarlanan başarısız giriş denemeleri IP adresini 10 dakika engeller. Oltalama veya zararlı yazılım bildirimleri bağlantıyı hemen karantinaya alabilir. Diğer bildirim türleri, tekilleştirme süresince bildirim sinyali başına bir kez sayılır; {{ abuse_quarantine_threshold }} farklı bildirim bağlantıyı karantinaya alabilir, {{ abuse_delete_threshold }} bildirim ise kalıcı silinmeye yol açabilir.'],
        ['Automated actions may be taken before a human review. Reports are reviewed as operational capacity allows, and immediate review is not guaranteed. Accounts and workspaces found to repeatedly violate these terms may be closed.', 'Otomatik işlemler insan incelemesinden önce uygulanabilir. Bildirimler operasyonel kapasite ölçüsünde incelenir; anında inceleme garantisi verilmez. Şartları tekrarlı biçimde ihlal ettiği belirlenen hesaplar ve çalışma alanları kapatılabilir.'],
        ['Warranty and limitation of liability', 'Garanti ve sorumluluğun sınırlandırılması'],
        ['This software is provided on an “AS IS” basis, without warranty of any kind, express or implied. The instance operator is not liable for user-provided destination content, temporary network interruptions, or third-party outages. See the', 'Bu yazılım açık veya zımni hiçbir garanti verilmeksizin “OLDUĞU GİBİ” sunulur. Hizmet işletmecisi, kullanıcıların belirlediği hedef içeriklerden, geçici ağ kesintilerinden veya üçüncü taraf hizmet kesintilerinden sorumlu değildir. Veri işleme hakkında bilgi için'],
        ['Privacy Notice', 'Gizlilik bildirimine'], ['for information about data handling.', 'bakın.'],
        ['Yer sağlayıcı bildirimi:', 'Hosting provider notice:'],
        ['Bu platform, 5651 sayılı İnternet Ortamında Yapılan Yayınların Düzenlenmesi ve Bu Yayınlar Yoluyla İşlenen Suçlarla Mücadele Edilmesi Hakkında Kanun kapsamında yer sağlayıcı statüsündedir. Yer sağlayıcı, yönlendirilen üçüncü taraf sitelerin içeriğini önceden denetlemekle yükümlü değildir; hukuka aykırı içerikten haberdar edildiğinde gerekli işlemleri ivedilikle yapar.', 'This service is treated as a hosting provider under Turkish Law No. 5651 on the Regulation of Publications on the Internet and the Fight Against Crimes Committed Through Such Publications. A hosting provider is not required to monitor hosted content or investigate whether an unlawful activity is taking place. Applicable duties to act on legally qualifying notices or orders remain in force.'],
        ['Phishing, malware, copyright, or unlawful-content notices can be sent through the online form or directly to the data controller:', 'Oltalama, zararlı yazılım, telif hakkı veya hukuka aykırı içerik bildirimleri çevrimiçi formdan ya da doğrudan veri sorumlusuna iletilebilir:'],
        ['Open the abuse report form', 'Kötüye kullanım bildirim formunu aç'], ['Direct contact · select to copy or open your mail app', 'Doğrudan iletişim · kopyalamak veya e-posta uygulamanızı açmak için seçin'],
        ['Copy the address or open your mail app', 'Adresi kopyalayın veya e-posta uygulamanızı açın'],
        ['Repeat-infringer policy:', 'Tekrarlayan ihlaller:'], ['Accounts and workspaces found to repeatedly violate these rules may be permanently closed and related network addresses may be blocked.', 'Bu kuralları tekrarlı biçimde ihlal ettiği belirlenen hesaplar ve çalışma alanları kalıcı olarak kapatılabilir; ilişkili ağ adresleri engellenebilir.'],
        ['More information', 'Daha fazla bilgi'], ['Privacy notice', 'Gizlilik bildirimi'], ['Back to PulseRoute', 'PulseRoute’a dön'],
        ['Privacy Policy & Data Notice | PulseRoute', 'Gizlilik Politikası ve Veri Bildirimi | PulseRoute'],
        ['How this PulseRoute instance handles account, click analytics, advertising, and abuse report data.', 'Bu PulseRoute hizmet örneğinin hesap, tıklama analitiği, reklam ve kötüye kullanım bildirim verilerini nasıl işlediği.'],
        ['Legal pages', 'Hukuki metinler'], ['IN THIS NOTICE', 'BU BİLDİRİMDE'], ['Controller', 'Veri sorumlusu'], ['Link visitors', 'Bağlantı ziyaretçileri'],
        ['Advertising', 'Reklamlar'], ['Security', 'Güvenlik'], ['Your rights', 'Haklarınız'], ['Abuse reports', 'Kötüye kullanım bildirimleri'],
        ['PRIVACY · KVKK · GDPR', 'GİZLİLİK · KVKK · GDPR'], ['Privacy Policy & Data Notice', 'Gizlilik Politikası ve Veri Bildirimi'],
        ['What this PulseRoute instance processes, why it does so, and how long it keeps the information.', 'Bu PulseRoute hizmet örneğinin hangi bilgileri, neden ve ne kadar süreyle işlediği.'],
        ['LAST REVIEWED · 25 SEP 2026', 'SON GÜNCELLEME · 25 EYLÜL 2026'], ['Scope and data controller', 'Kapsam ve veri sorumlusu'],
        ['PulseRoute is open-source link-shortening software. This notice covers this hosted instance and its application and infrastructure processing. The instance operator is the data controller under Turkish Personal Data Protection Law No. 6698 (KVKK) and, where applicable, the GDPR.', 'PulseRoute açık kaynaklı bağlantı kısaltma yazılımıdır. Bu bildirim, barındırılan bu hizmet örneğini ve uygulama ile altyapı kapsamındaki veri işlemeyi açıklar. Hizmet işletmecisi, 6698 sayılı Kişisel Verilerin Korunması Kanunu (KVKK) ve uygulanabildiği ölçüde GDPR kapsamında veri sorumlusudur.'],
        ['Data controller contact', 'Veri sorumlusu iletişim bilgisi'], ['Click to email or copy the address', 'E-posta göndermek veya adresi kopyalamak için tıklayın'],
        ['Short link visitors', 'Kısa bağlantı ziyaretçileri'], ['Redirects:', 'Yönlendirmeler:'], ['the redirect flow does not set tracking cookies or behavioral beacons.', 'yönlendirme akışı izleme çerezi veya davranış işaretçisi kullanmaz.'],
        ['Click analytics:', 'Tıklama analitiği:'], ['when analytics are enabled, the service records link and time, approximate location derived from a masked IP, and device, browser, operating system, and referrer information. Raw click IP addresses are not stored in click records. IPv4 addresses are masked to', 'analitik etkin olduğunda hizmet; bağlantı ve zaman bilgisini, maskelenmiş IP’den türetilen yaklaşık konumu, cihaz, tarayıcı, işletim sistemi ve yönlendiren sayfa bilgilerini kaydeder. Ham tıklama IP adresleri tıklama kayıtlarında saklanmaz. IPv4 adresleri'],
        ['and IPv6 to', 've IPv6 adresleri'], ['before location processing.', 'konum işlenmeden önce maskelenir.'], ['Retention:', 'Saklama süresi:'],
        ['detailed click events are retained for up to {{ analytics_retention_days or 90 }} days and then purged; aggregate click counts may remain with the link.', 'ayrıntılı tıklama olayları en fazla {{ analytics_retention_days or 90 }} gün saklanır ve ardından silinir; toplam tıklama sayıları bağlantıyla birlikte tutulabilir.'],
        ['Accounts and workspaces', 'Hesaplar ve çalışma alanları'], ['Registered account data includes email address, optional display name, password hash, workspace membership, links, custom domain records, and related analytics.', 'Kayıtlı hesap verileri e-posta adresini, isteğe bağlı görünen adı, parola özetini, çalışma alanı üyeliğini, bağlantıları, özel alan adı kayıtlarını ve ilişkili analitiği içerir.'],
        ['Passwords are hashed with bcrypt. Workspace authorization restricts access to its members and permitted roles.', 'Parolalar bcrypt ile özetlenir. Çalışma alanı erişimi üyeler ve yetkili rollerle sınırlandırılır.'],
        ['Anonymous links expire after 24 hours. Account holders can request deletion using account settings or the authenticated', 'Anonim bağlantıların süresi 24 saat sonra dolar. Hesap sahipleri, hesap ayarlarından veya kimlik doğrulaması gerektiren'],
        ['endpoint. Provider backups and legally required records may persist for their applicable retention period.', 'uç noktasından silme talep edebilir. Sağlayıcı yedekleri ve kanunen saklanması gereken kayıtlar, geçerli saklama süreleri boyunca tutulabilir.'],
        ['Advertising and cookies', 'Reklamlar ve çerezler'],
        ['This instance may display Google AdSense ads on the management console or optional countdown pages. Advertising scripts and personalized advertising cookies are loaded only after consent where consent is required. If consent is declined or absent, personalized advertising is not enabled; availability of non-personalized ads depends on provider behavior.', 'Bu hizmet örneği yönetim panelinde veya isteğe bağlı geri sayım sayfalarında Google AdSense reklamları gösterebilir. Rıza gereken durumlarda reklam betikleri ve kişiselleştirilmiş reklam çerezleri yalnızca rıza verildikten sonra yüklenir. Rıza verilmez veya reddedilirse kişiselleştirilmiş reklam etkinleştirilmez; kişiselleştirilmemiş reklamların sunulması sağlayıcının davranışına bağlıdır.'],
        ['cookie stores the advertising choice for up to 180 days. It contains the preference, not account credentials. Browser storage and essential session behavior may also be used where needed for the service.', 'çerezi reklam tercihini en fazla 180 gün saklar. Hesap bilgilerini değil, tercihi içerir. Hizmet için gerektiğinde tarayıcı depolaması ve zorunlu oturum işlevleri de kullanılabilir.'],
        ['Security and service providers', 'Güvenlik ve hizmet sağlayıcıları'],
        ['Controls include parameterized database queries, rate limits, access controls, and authenticated encryption for supported integration secrets. No online service can guarantee absolute security.', 'Güvenlik önlemleri parametreli veritabanı sorgularını, istek sınırlarını, erişim kontrollerini ve desteklenen entegrasyon sırları için doğrulamalı şifrelemeyi içerir. Hiçbir çevrimiçi hizmet mutlak güvenlik garantisi veremez.'],
        ['Cloudflare, Render, Neon Postgres, and Upstash Redis may process request or service data to provide DNS, hosting, database, and cache/queue infrastructure. Their processing is governed by their own terms and applicable data processing terms.', 'Cloudflare, Render, Neon Postgres ve Upstash Redis; DNS, barındırma, veritabanı ve önbellek/kuyruk altyapısı sağlamak için istek veya hizmet verilerini işleyebilir. Veri işleme faaliyetleri kendi şartlarına ve geçerli veri işleme hükümlerine tabidir.'],
        ['Subject to applicable law, you may request access, correction, deletion, restriction, or an explanation of processing, and may lodge a complaint with the competent authority. Contact the controller above. Requests may require identity verification and may be limited by legal retention duties.', 'Geçerli mevzuat çerçevesinde verilerinize erişim, düzeltme, silme veya işlemenin kısıtlanmasını ya da işleme hakkında açıklama talep edebilir; yetkili makama şikâyette bulunabilirsiniz. Yukarıdaki veri sorumlusu ile iletişime geçin. Kimlik doğrulaması gerekebilir ve talepler kanuni saklama yükümlülükleriyle sınırlanabilir.'],
        ['Abuse reports and deduplication', 'Kötüye kullanım bildirimleri ve tekilleştirme'],
        ['When you submit a report through the', 'Şu kanal üzerinden bildirim gönderdiğinizde:'], ['or API, the service processes the submitted link, reason, details, reporter email, and a masked IP to review the notice and prevent misuse of the reporting channel. Reports may be retained as required to investigate incidents and meet legal obligations under Law No. 5651 and applicable data protection law.', 'veya API aracılığıyla, hizmet bildirimi incelemek ve bildirim kanalının kötüye kullanımını önlemek için gönderilen bağlantıyı, nedeni, açıklamayı, bildirim sahibinin e-posta adresini ve maskelenmiş IP adresini işler. Bildirimler, olayları araştırmak ve 5651 sayılı Kanun ile geçerli veri koruma mevzuatından doğan yükümlülükleri karşılamak için gerektiği süre boyunca saklanabilir.'],
        ['abuse portal', 'kötüye kullanım portalı'], ['To prevent repeated submissions from automatically affecting a link, the service derives a keyed HMAC-SHA-256 digest from the request IP, user-agent, and language headers. The raw values used for this matching digest are not stored by this feature. The digest is pseudonymous personal data, not anonymous data: it is used for matching during the configured window (default 24 hours), then cleared on the next retention pass, which runs every 15 minutes. The digest is not used for advertising or cross-site tracking.', 'Tekrarlanan bildirimlerin bir bağlantıyı otomatik olarak etkilemesini önlemek için hizmet, isteğin IP adresi, user-agent ve dil başlıklarından anahtarlı HMAC-SHA-256 özeti üretir. Bu eşleştirme özelliği ham değerleri saklamaz. Özet anonim değil, takma adlı kişisel veridir: yapılandırılan süre boyunca (varsayılan 24 saat) eşleştirme için kullanılır ve her 15 dakikada çalışan bir sonraki saklama temizliğinde kaldırılır. Özet reklam veya siteler arası izleme için kullanılmaz.'],
        ['Distinct reports can cause a link to be quarantined at the configured threshold; phishing or malware reports may quarantine immediately. Permanent deletion follows the higher configured threshold. See', 'Farklı bildirimler, yapılandırılmış eşiğe ulaşıldığında bağlantıyı karantinaya alabilir; oltalama veya zararlı yazılım bildirimleri anında karantinaya yol açabilir. Daha yüksek eşikte kalıcı silme uygulanabilir. Ayrıntılar için'],
        ['Terms and Acceptable Use', 'Kullanım Şartları ve Kabul Edilebilir Kullanım'], ['Terms of Service', 'Hizmet Şartları'], ['Return to PulseRoute', 'PulseRoute’a dön'],
        ['Skip to terms', 'Şartlara geç'], ['PulseRoute home', 'PulseRoute ana sayfa'], ['Accessibility Statement | PulseRoute', 'Erişilebilirlik Bildirimi | PulseRoute'],
        ['Digital accessibility statement, WCAG 2.1 compliance, and keyboard navigation support for PulseRoute.', 'PulseRoute için dijital erişilebilirlik bildirimi, WCAG 2.1 rehberliği ve klavye gezinme desteği.'],
        ['Accessibility Statement', 'Erişilebilirlik Bildirimi'], ['LAST REVIEWED • AUGUST 2026', 'SON GÜNCELLEME • AĞUSTOS 2026'],
        ['1. Commitment to Accessibility', '1. Erişilebilirlik taahhüdü'],
        ['PulseRoute is committed to ensuring digital accessibility for individuals with disabilities. We continually refine our user interface to ensure that our link management, analytics boards, and redirection flows are accessible, intuitive, and efficient for everyone.', 'PulseRoute, engelli bireyler için dijital erişilebilirliği iyileştirmeyi amaçlar. Bağlantı yönetimi, analitik ekranları ve yönlendirme akışlarının erişilebilir ve anlaşılır olması için arayüzü geliştirmeye devam ediyoruz.'],
        ['2. Conformance Standards', '2. Rehberler'], ['Our platform is built and maintained to conform with the Web Content Accessibility Guidelines (', 'Platform, Web İçeriği Erişilebilirlik Kılavuzları ('], [') standards.', ') doğrultusunda geliştirilip sürdürülür.'],
        ['3. Key Accessibility Features', '3. Erişilebilirlik özellikleri'], ['Semantic HTML5:', 'Anlamsal HTML5:'], ['Structured with native landmarks (', 'Yerel sayfa bölgeleriyle yapılandırılmıştır ('], ['<header>', '<header>'], ['<main>', '<main>'], ['<footer>', '<footer>'], ['<nav>', '<nav>'], [') and hierarchical headings for screen reader efficiency.', ') ekran okuyucular için başlık sıralaması sağlar.'],
        ['Keyboard Navigation:', 'Klavye ile gezinme:'], ['Full keyboard operation for URL shortening forms, domain management, modal dialogs, and analytics views (Tab, Shift+Tab, Enter, Space, Escape).', 'URL kısaltma formları, alan adı yönetimi, iletişim pencereleri ve analitik ekranları Tab, Shift+Tab, Enter, Space ve Escape tuşlarıyla kullanılabilir.'],
        ['High Contrast & Typography:', 'Yüksek karşıtlık ve tipografi:'], ['High-contrast color palette paired with clear font families (Space Grotesk, Inter, JetBrains Mono) ensuring readability across displays.', 'Ekranlarda okunabilirliği desteklemek için belirgin renk karşıtlığı ve okunaklı yazı tipleri kullanılır.'],
        ['Screen Reader & ARIA Support:', 'Ekran okuyucu ve ARIA desteği:'], ['Explicit labels for interactive controls, action buttons (Copy link, Generate QR), and live status messages.', 'Etkileşimli kontroller, işlem düğmeleri ve canlı durum mesajları açık etiketlere sahiptir.'],
        ['Reduced Motion Support:', 'Azaltılmış hareket desteği:'], ["Respects the operating system’s", 'İşletim sisteminin'], ['setting by disabling animated pulse indicators and non-essential transitions.', 'ayarına saygı göstererek hareketli göstergeleri ve gerekli olmayan geçişleri kapatır.'],
        ['Responsive & Zoom Resilient:', 'Duyarlı tasarım ve yakınlaştırma:'], ['Seamlessly adapts to desktop, tablet, and mobile screens, supporting up to 200% text zoom without breaking navigation or layout.', 'Masaüstü, tablet ve mobil ekranlara uyum sağlar; gezinme ve düzen bozulmadan %200 metin yakınlaştırmasını destekler.'],
        ['4. Feedback & Contact', '4. Geri bildirim ve iletişim'], ['If you experience any accessibility barriers while using PulseRoute or have suggestions for improvement, please contact the instance administrator.', 'PulseRoute’u kullanırken erişilebilirlik engeliyle karşılaşırsanız veya iyileştirme öneriniz varsa hizmet yöneticisiyle iletişime geçin.'], ['Contact:', 'İletişim:'],
        ['Terms', 'Kullanım şartları'], ['Privacy', 'Gizlilik'], ['Return to Console', 'Panele dön'],
        ['Kötüye kullanım bildirimi | PulseRoute', 'Abuse report | PulseRoute'], ['PulseRoute kısa bağlantıları için oltalama, zararlı yazılım ve diğer güvenlik ihlallerini bildirin.', 'Report phishing, malware, and other security issues involving PulseRoute short links.'],
        ['Ana içeriğe geç', 'Skip to main content'], ['PulseRoute ana sayfa', 'PulseRoute home'], ['Ana gezinme', 'Main navigation'], ['Kullanım şartları', 'Terms'], ['Gizlilik', 'Privacy'],
        ['Bildirim bilgisi', 'Report information'], ['GÜVENLİK · BİLDİRİM', 'SECURITY · REPORT'], ['Şüpheli bağlantıyı bize iletin.', 'Report a suspicious link.'],
        ['PulseRoute kısa bağlantısıyla yönlendirilen bir hedefte oltalama, zararlı yazılım, telif ihlali veya başka bir güvenlik sorunu gördüyseniz formu doldurun.', 'Use this form to report phishing, malware, copyright infringement, or another security issue at a destination reached through a PulseRoute short link.'],
        ['Oltalama ve zararlı yazılım', 'Phishing and malware'], ['bildirimleri bağlantıyı hemen karantinaya alabilir. Diğer bildirimler inceleme kuyruğuna alınır; {{ abuse_quarantine_threshold }} farklı bildirim sinyalinde karantina, {{ abuse_delete_threshold }} sinyalde kalıcı silme uygulanabilir.', 'reports may quarantine a link immediately. Other reports enter the review queue; {{ abuse_quarantine_threshold }} distinct report signals may quarantine a link, and {{ abuse_delete_threshold }} may cause permanent deletion.'],
        ['Bildiriminiz değerlendirilirken verdiğiniz e-posta adresi gerekirse sizinle iletişim kurmak için kullanılır.', 'We may use your email address to contact you while assessing your report.'],
        ['5651 · UYAR-KALDIR', 'LAW NO. 5651 · NOTICE AND TAKEDOWN'], ['Kötüye kullanım bildirimi', 'Abuse report'], ['İncelemeye başlayabilmemiz için kısa bağlantıyı ve ihlal türünü belirtin.', 'Provide the short link and type of issue so we can assess the report.'], ['GÜVENLİK BİLDİRİMİ', 'SECURITY REPORT'],
        ['Kısa bağlantı veya kod', 'Short link or code'], ['ps.sely.tr/ornek-kod veya ornek-kod', 'ps.sely.tr/example-code or example-code'], ['Bildirilecek PulseRoute bağlantısını yapıştırın.', 'Paste the PulseRoute link you are reporting.'],
        ['İhlal türü', 'Issue type'], ['Bir kategori seçin', 'Select a category'], ['Oltalama veya sahte giriş sayfası', 'Phishing or fake sign-in page'], ['Zararlı yazılım veya tehlikeli dosya', 'Malware or dangerous file'], ['Yasa dışı içerik', 'Unlawful content'], ['Telif hakkı veya marka ihlali', 'Copyright or trademark infringement'], ['İstenmeyen toplu ileti / spam', 'Unsolicited bulk messages / spam'], ['Diğer güvenlik ihlali', 'Other security issue'],
        ['Oltalama ve zararlı yazılım bildirimleri anında karantinaya alınır.', 'Phishing and malware reports can trigger immediate quarantine.'], ['İletişim e-posta adresiniz', 'Your contact email'], ['guvenlik@kurumunuz.com', 'security@your-organization.com'], ['Ek bilgi veya inceleme sonucu için sizinle iletişim kurabiliriz.', 'We may contact you for more information or to share the review outcome.'],
        ['Açıklama veya delil', 'Details or evidence'], ['İsteğe bağlı', 'Optional'], ['Gördüğünüz sorunu ve varsa ilgili ayrıntıları açıklayın.', 'Describe the issue you observed and include relevant details.'], ['Parola, ödeme bilgisi veya başka hassas kişisel veri eklemeyin.', 'Do not include passwords, payment details, or other sensitive personal data.'],
        ['Güvenlik bildirimini gönder', 'Submit security report'], ['Yer sağlayıcı bildirimi', 'Hosting provider notice'], ['· Hukuka aykırı içerik bildirimleri 5651 sayılı Kanun ve geçerli yükümlülükler kapsamında değerlendirilir. Otomatik eşikler kişi doğrulaması değildir; bir bağlantının karantinaya alınması veya silinmesi için tek başına kesin hukuki karar sayılmaz.', '· Notices about unlawful content are assessed under Law No. 5651 and applicable duties. Automated thresholds do not verify a person and are not, by themselves, a final legal determination that a link is unlawful.'],
        ['Yetkili iletişim', 'Operator contact'], ['E-posta göndermek veya adresi kopyalamak için seçin', 'Select to email or copy the address'], ['← Kullanım şartları', '← Terms'], ['Gizlilik bildirimi', 'Privacy notice'], ['PulseRoute’a dön', 'Back to PulseRoute'],
        ['Bu bildirim daha önce alınmış', 'This report was already received'], ['Bildiriminiz kaydedildi', 'Your report has been recorded'], ['Bildirim gönderilemedi', 'Could not submit report'], ['Sunucuya ulaşılamadı', 'Could not reach the server'], ['Gönderiliyor…', 'Submitting…'],
        ['Bağlantıyı ve girdiğiniz bilgileri kontrol edip tekrar deneyin.', 'Check the link and details, then try again.'], ['Lütfen bağlantınızı kontrol edip daha sonra tekrar deneyin.', 'Check your connection and try again later.'],
        ['Bu bağlantı için aynı sinyalden yakın zamanda bildirim alındı.', 'A report with the same signal for this link was recently received.'], ['Güvenlik bildiriminiz inceleme için alındı.', 'Your security report has been queued for review.'],
        ['Bağlantı kontrol ediliyor — PulseRoute', 'Checking link — PulseRoute'], ['Transit Gate', 'Link checkpoint'], ['Aktarım İstasyonu', 'Link checkpoint'], ['Bağlantıyı doğrulamak için JavaScript etkin olmalı.', 'JavaScript must be enabled to verify this link.'], ['KONTROL', 'CHECKING'], ['Hedef Sayfa Hazırlanıyor...', 'Preparing destination…'], ['Güvenli bağlantı kontrol ediliyor, lütfen birkaç saniye bekleyin.', 'Checking the link for safety. Please wait a few seconds.'], ['HEDEF:', 'DESTINATION:'], ['Bağlantı kontrol ediliyor', 'Checking link'], ['Bekleniyor', 'Please wait'], ['PulseRoute Yüksek Hızlı Yönlendirme', 'PulseRoute High-Speed Redirects'], ['Özel alan adları, gerçek zamanlı tıklama analitiği ve gizlilik odaklı bağlantı altyapısı.', 'Custom domains, real-time click analytics, and privacy-focused link infrastructure.'], ['Güvenli İletim', 'Secure redirect'], ['Şüpheli Bağlantı Bildir', 'Report a suspicious link'], ['Kullanım Şartları', 'Terms of service'],
        ['Güvenlik Uyarısı — Bağlantı Askıya Alındı | PulseRoute', 'Security notice — Link suspended | PulseRoute'], ['HTTP 451 • ERİŞİM ENGELLENDİ', 'HTTP 451 • ACCESS BLOCKED'], ['Güvenlik Uyarısı: Bağlantı Karantinaya Alındı', 'Security notice: Link quarantined'], ['Ulaşmaya çalıştığınız kısa bağlantı;', 'The short link you tried to open was suspended because of a suspected violation involving'], ['5651 Sayılı Kanun', 'Turkish Law No. 5651'], ['Oltalama (Phishing)', 'Phishing'], ['Zararlı Yazılım (Malware)', 'Malware'], ['veya', 'or'], ['Kötüye Kullanım İlkelerimizin', 'our acceptable-use policy'], ['ihlali şüphesiyle sistemimiz tarafından derhal askıya alınmış ve hedef sayfaya yönlendirme durdurulmuştur.', 'and redirects to its destination have been stopped.'], ['Erişim Durumu:', 'Access status:'], ['Askıya Alındı (Quarantined)', 'Suspended (quarantined)'], ['Yasal / Güvenlik Dayanağı:', 'Legal / security basis:'], ['5651 Sayılı Kanun & Safe Harbor Uyar-Kaldır', 'Law No. 5651 and applicable notice-and-takedown rules'], ['Güvenlik Notu:', 'Security note:'], ['Güvenliğiniz için bu bağlantının yönlendirmeye çalıştığı orijinal adresi ziyaret etmeyiniz ve kişisel veya finansal bilgilerinizi kesinlikle paylaşmayınız.', 'For your safety, do not visit the original address or share personal or financial information there.'], ['Kötüye Kullanım Bildir', 'Report abuse'], ['Hizmet Şartları & Güvenlik Politikası →', 'Terms of service & security policy →'], ['PulseRoute Edge Security • 5651 Sayılı Kanun Uyarınca Yer Sağlayıcı Güvenlik Mekanizması', 'PulseRoute edge security • hosting provider safety mechanism under Law No. 5651'],
        ['404 — Link Not Found | PulseRoute', '404 — Bağlantı bulunamadı | PulseRoute'], ['Short Link Not Found', 'Kısa bağlantı bulunamadı'], ['The requested routing slug does not exist in this workspace or has expired.', 'İstenen kısa kod bu çalışma alanında bulunamadı veya süresi doldu.'], ['Return to Routing Console', 'Yönlendirme paneline dön'], ['PulseRoute Deterministic Edge Engine', 'PulseRoute yönlendirme sistemi'],
        ['410 — Link Expired | PulseRoute', '410 — Bağlantının süresi doldu | PulseRoute'], ['Campaign / Link Expired', 'Kampanya / bağlantı süresi doldu'], ['The expiration threshold for this short URL has been reached.', 'Bu kısa bağlantının geçerlilik süresi sona erdi.'], ['PulseRoute Retention Policy Engine', 'PulseRoute saklama politikası sistemi'],
        ['Main navigation', 'Ana gezinme'], ['Home', 'Ana sayfa'], ['SYSTEM CHECK', 'SİSTEM KONTROLÜ'], ['Database', 'Veritabanı'], ['Redis', 'Redis'], ['Probe time', 'Kontrol süresi'], ['Version', 'Sürüm'], ['This endpoint does not expose credentials or connection details.', 'Bu uç nokta kimlik bilgilerini veya bağlantı ayrıntılarını göstermez.'],
        ['Under Article 5 of Turkish Law No. 5651, a hosting provider is not required to monitor hosted content or investigate whether an unlawful activity is taking place. Duties to act on notices or orders that legally require action remain in force.', '5651 sayılı Kanun’un 5. maddesine göre yer sağlayıcı, barındırdığı içeriği izlemek veya hukuka aykırı bir faaliyetin olup olmadığını araştırmakla yükümlü değildir. Hukuken işlem gerektiren bildirim veya kararlar üzerine doğan yükümlülükler devam eder.'],
        ['This service is not staffed around the clock for manual review. We cannot promise an immediate human response or a particular outcome for every report. Automated risk signals may block or quarantine a link without prior human review; they can miss harmful material or flag a link incorrectly. This does not limit any action required by applicable law.', 'Bu hizmette 7/24 manuel inceleme yapılmaz. Her bildirim için anında insan yanıtı veya belirli bir sonuç vaat edemeyiz. Otomatik risk sinyalleri önceden insan incelemesi olmadan bağlantıyı engelleyebilir veya karantinaya alabilir; zararlı içeriği gözden kaçırabilir ya da bağlantıyı yanlış işaretleyebilir. Bu durum, geçerli mevzuatın gerektirdiği işlemleri sınırlamaz.'],
        ['The service does not continuously monitor every third-party destination, and no human operator is continuously available for immediate review. Reports are reviewed as operational capacity allows; a submission does not guarantee an immediate response or a particular decision. Applicable legal duties and valid notices or orders continue to apply. Automated controls may quarantine a link without prior human review.', 'Hizmet, üçüncü taraf hedeflerin tamamını sürekli izlemez ve anında inceleme için sürekli hazır bulunan bir insan işletmeci yoktur. Bildirimler operasyonel kapasite ölçüsünde değerlendirilir; bildirim göndermek anında yanıt veya belirli bir karar garantisi vermez. Geçerli yasal yükümlülükler ile usulüne uygun bildirim ve kararlar geçerliliğini korur. Otomatik kontroller, önceden insan incelemesi olmadan bir bağlantıyı karantinaya alabilir.'],
        ['Automated safety controls may quarantine a link without prior human review; they may miss harmful content or flag a link incorrectly. A report does not guarantee an immediate response or a particular outcome.', 'Otomatik güvenlik kontrolleri, önceden insan incelemesi olmadan bir bağlantıyı karantinaya alabilir; zararlı içeriği gözden kaçırabilir ya da bağlantıyı yanlış işaretleyebilir. Bildirim, anında yanıt veya belirli bir sonuç garantisi vermez.'],
        ['A recent report from this browser and network was already recorded.', 'Bu tarayıcı ve ağdan yakın zamanda bir bildirim zaten kaydedildi.'],
        ['Bağlantı çok sayıda şikayet alması nedeniyle sistemden kalıcı olarak silinmiştir.', 'The link was permanently deleted after receiving multiple reports.'],
        ['Bağlantı, yapılandırılmış kötüye kullanım bildirim eşiğine ulaşıldığı için kalıcı olarak silinmiştir.', 'The link was permanently deleted after reaching the configured abuse report threshold.'],
        ['Bağlantı 5651 Sayılı Kanun ve Güvenlik İlkelerimiz kapsamında derhal karantinaya alınmış ve erişimi durdurulmuştur.', 'The link was quarantined immediately under Law No. 5651 and our safety rules; access has been stopped.'],
        ['Bildiriminiz alınmıştır. İnceleme en geç 24 saat içinde tamamlanacaktır.', 'Your report was received. Review will be completed within 24 hours.'],
        ['Bildiriminiz alındı. İnceleme süresi operasyonel kapasiteye göre değişebilir; anında yanıt garanti edilmez.', 'Your report was received. Review timing may vary with operational capacity; an immediate response is not guaranteed.'],
        ['Bu bağlantı için yakın zamanda aynı cihaz ve ağdan bildirim alındı.', 'A recent report from the same device and network for this link was already received.'],
        ['Too many abuse reports submitted from this IP. Please try again later.', 'Bu IP adresinden çok fazla kötüye kullanım bildirimi gönderildi. Daha sonra tekrar deneyin.'],
        ['Could not extract a valid short link identifier or slug from the input.', 'Girilen metinden geçerli bir kısa bağlantı veya kısa kod alınamadı.'],
        ["Email already registered.", 'Bu e-posta adresi zaten kayıtlı.'],
        ["This email's domain does not appear to accept mail. Please use a real email address.", 'Bu e-posta alan adı e-posta kabul etmiyor gibi görünüyor. Geçerli bir e-posta adresi kullanın.'],
        ['Too many failed login attempts. IP address temporarily blocked for 10 minutes.', 'Çok fazla başarısız giriş denemesi yapıldı. IP adresi 10 dakika geçici olarak engellendi.'],
        ['Invalid email or password.', 'E-posta adresi veya parola hatalı.'], ["Invalid or expired token", 'Oturum anahtarı geçersiz veya süresi dolmuş.'],
        ['User not found or inactive', 'Kullanıcı bulunamadı veya etkin değil.'], ['Domain not found', 'Alan adı bulunamadı'], ['Link not found', 'Bağlantı bulunamadı'],
        ['Custom domains are disabled on this server by the administrator.', 'Yönetici bu sunucuda özel alan adlarını devre dışı bıraktı.'],
        ['Invalid or unverified custom domain for this workspace.', 'Bu çalışma alanı için alan adı geçersiz veya doğrulanmamış.'],
        ['Rate limit exceeded. Please wait before creating more links.', 'İstek sınırı aşıldı. Yeni bağlantı oluşturmadan önce lütfen bekleyin.'],
        ['Workspace slug already taken.', 'Bu çalışma alanı kısa kodu zaten kullanılıyor.'], ['Unsupported format', 'Desteklenmeyen biçim'],
        ['Invalid redirect ticket', 'Yönlendirme bileti geçersiz'], ['Please wait before continuing', 'Devam etmeden önce lütfen bekleyin'],
        ['Link verification is temporarily unavailable', 'Bağlantı doğrulaması geçici olarak kullanılamıyor'],
        ['Public stats are disabled for this link', 'Bu bağlantı için herkese açık istatistikler kapalı'],
        ['Link has been permanently removed due to exceeding the maximum abuse report threshold.', 'Bağlantı, kötüye kullanım bildirim eşiğini aştığı için kalıcı olarak silindi.'],
        ['Link has been quarantined immediately and redirection halted pending formal review.', 'Bağlantı derhal karantinaya alındı ve resmî inceleme beklenirken yönlendirme durduruldu.'],
        ['Report has been safely recorded for review; review timing may vary with operational capacity.', 'Bildiriminiz inceleme için kaydedildi; inceleme süresi operasyonel kapasiteye göre değişebilir.'],
        ['· 5651 sayılı Kanun’un 5. maddesi yer sağlayıcı için içerikleri sürekli izleme veya hukuka aykırılığı araştırma yükümlülüğü öngörmez. Kanundaki geçerli bildirim ve kararlar üzerine doğan yükümlülükler saklıdır.', '· Article 5 of Turkish Law No. 5651 does not require a hosting provider to continuously monitor content or investigate whether it is unlawful. Duties arising from applicable notices and orders remain in force.'],
        ['Bu hizmette 7/24 insan incelemesi yoktur; anında yanıt veya belirli bir sonuç garanti edilemez. Otomatik güvenlik sinyalleri insan incelemesinden önce karantina uygulayabilir; zararlı içerik gözden kaçabilir veya bağlantı yanlış işaretlenebilir. Bildirim, zorunlu hukuki süreçlerin yerine geçmez.', 'This service has no 24/7 human review; an immediate response or a particular outcome cannot be guaranteed. Automated safety signals may quarantine a link before human review; harmful content may be missed or a link may be flagged incorrectly. Reports do not replace legally required procedures.'],
        ['Otomatik eşikler kişi doğrulaması değildir; tek başına kesin hukuki karar sayılmaz.', 'Automated thresholds do not verify a person and are not, by themselves, a final legal determination.'],
        [' for the report handling rules.', ' bildirim süreci hakkında ayrıntı verir.'],
        ['Reklam ve sitenin düzgün çalışması için çerez kullanıyoruz. Zorunlu olmayan çerezleri kabul edebilir ya da reddedebilirsiniz.', 'We use cookies for advertising and to keep the site working properly. You can accept or reject non-essential cookies.'],
        ['Gizlilik Politikası', 'Privacy Policy'], ['Reddet', 'Reject'], ['Kabul Et', 'Accept'],
        ['Çalışma alanını sil', 'Delete workspace'], ['Hesabımı sil', 'Delete my account'], ['Silmek istediğinizden emin misiniz?', 'Are you sure you want to delete this?'],
        ['This service has no 24/7 human review; an immediate response or a particular outcome cannot be guaranteed. Automated safety signals may quarantine a link before human review; harmful content may be missed or a link may be flagged incorrectly. Reports do not replace legally required procedures.', 'Bu hizmette 7/24 insan incelemesi yoktur; anında yanıt veya belirli bir sonuç garanti edilemez. Otomatik güvenlik sinyalleri insan incelemesinden önce karantina uygulayabilir; zararlı içerik gözden kaçabilir veya bağlantı yanlış işaretlenebilir. Bildirim, zorunlu hukuki süreçlerin yerine geçmez.'],
        ['This service has no 24/7 human review; an immediate response or a particular outcome cannot be guaranteed. Automated safety signals may quarantine a link before human review; harmful content may be missed or a link may be flagged incorrectly. Reports do not replace legally required procedures.', 'Bu hizmette 7/24 insan incelemesi yoktur; anında yanıt veya belirli bir sonuç garanti edilemez. Otomatik güvenlik sinyalleri insan incelemesinden önce karantina uygulayabilir; zararlı içerik gözden kaçabilir veya bağlantı yanlış işaretlenebilir. Bildirim, zorunlu hukuki süreçlerin yerine geçmez.'],
        ['Reklam ve sitenin düzgün çalışması için çerez kullanıyoruz. Zorunlu olmayan çerezleri kabul edebilir ya da reddedebilirsiniz.', 'We use cookies for advertising and to keep the site working properly. You can accept or reject non-essential cookies.'],
        ['Gizlilik Politikası', 'Privacy Policy'], ['Reddet', 'Reject'], ['Kabul Et', 'Accept'],
        ['Otomatik eşikler kişi doğrulaması değildir; bir bağlantının karantinaya alınması veya silinmesi için tek başına kesin hukuki karar sayılmaz.', 'Automated thresholds do not verify a person and are not, by themselves, a final legal determination that a link should be quarantined or deleted.'],
        ['5651 notice and takedown', '5651 sayılı Kanun uyarınca bildirim ve içerik kaldırma'],
        ['Connect', 'Bağla'], ['links.mybrand.com', 'links.mybrand.com'], ['my-link', 'ornek-kisa-kod'], ['campaign, social', 'kampanya, sosyal'], ['Growth Team', 'Büyüme Ekibi'], ['growth-team', 'buyume-ekibi'], ['Search…', 'Ara…'],
        ['Click to email or copy the address', 'E-posta göndermek veya adresi kopyalamak için tıklayın'], ['E-posta göndermek ve adresi kopyalamak için tıklayın', 'Click to email or copy the address'], ['E-posta göndermek veya adresi kopyalamak için seçin', 'Select to email or copy the address'],
        ['Güvenlik Uyarısı: Bağlantı Askıya Alındı', 'Security notice: Link suspended'], ['Bu bağlantı oltalama (phishing) veya zararlı yazılım şüphesiyle 5651 Sayılı Kanun kapsamında karantinaya alınmıştır.', 'This link was quarantined under Law No. 5651 because of suspected phishing or malware.'],
        ['GÜVENLİK', 'SECURITY'], ['Erişim durduruldu (Karantina)', 'Access stopped (quarantined)'], ['Engellendi', 'Blocked'], ['Kötüye Kullanım / İhlal Bildir', 'Report abuse / violation'],
        ['Bu bağlantı kayıtlı değil', 'This link is not registered'], ['Bu bağlantı artık kullanılamıyor', 'This link is no longer available'], ['Bu bağlantı şifre gerektiriyor', 'This link requires a password'], ['Bağlantı şu anda doğrulanamıyor', 'This link cannot be verified right now'],
        ['Adresi kontrol edip yeniden deneyin.', 'Check the address and try again.'], ['Daha sonra tekrar deneyebilirsiniz.', 'You can try again later.'], ['DURUM', 'STATUS'], ['Bağlantı bulunamadı', 'Link not found'], ['Yönlendirme yapılamadı', 'Redirect could not be completed'], ['Doğrulanamadı', 'Not verified'],
        ['Ana sayfaya dön', 'Return to home'], ['Yeniden dene', 'Try again'], ['Bağlantı doğrulandı', 'Link verified'], ['Kısa bir beklemeden sonra ilerleyebilirsiniz.', 'You can continue after a short wait.'], ['Hedef hazırlanıyor', 'Preparing destination'], ['Doğrulandı', 'Verified'], ['SANİYE', 'SECONDS'], ['Tıkla ve İlerle', 'Continue'], ['Bağlantınız hazır', 'Your link is ready'], ['Hedef sayfaya geçmek için butona tıklayın.', 'Select the button to continue to the destination.'], ['HAZIR', 'READY'], ['Hedef sayfa', 'Destination page'], ['Bağlantı hazırlanıyor', 'Preparing link'], ['Please wait ({{seconds}}s)', 'Lütfen bekleyin ({{seconds}}s)'],
        ['1. Add a', '1. Bir'], ['record', 'kaydı'], ['named', 'adlı'], ['pointing to', 'şuraya yönlendiren'], ['2. Add a', '2. Bir'], ['at', 'adresinde'], ['with the value:', 'değerini girin:'],
        ['Distinct reports can cause a link to be quarantined at the configured threshold; phishing or malware reports may quarantine immediately. Permanent deletion follows the higher configured threshold. Automated signals can miss harmful material or flag a link incorrectly. See', 'Farklı bildirimler yapılandırılmış eşikte bağlantıyı karantinaya alabilir; oltalama veya zararlı yazılım bildirimleri anında karantinaya yol açabilir. Daha yüksek eşikte kalıcı silme uygulanır. Otomatik sinyaller zararlı içeriği gözden kaçırabilir veya bir bağlantıyı yanlış işaretleyebilir. Ayrıntılar için'],
        ['[data-controller]', '[data-controller]'],
        ['This software is provided without any guarantee that a human operator is continuously available to review reports or respond immediately. Reports are reviewed as operational capacity allows; urgent or legally binding notices are handled as required by applicable law.', 'Bu yazılım, raporları incelemek veya hemen yanıt vermek üzere bir insan işletmecinin sürekli hazır bulunacağı garantisini vermez. Bildirimler operasyonel kapasite ölçüsünde incelenir; acil veya hukuken bağlayıcı bildirimler geçerli mevzuatın gerektirdiği şekilde ele alınır.'],
        ['The service does not continuously monitor every third-party destination. Automated safety signals may block or quarantine a link without prior human review; these systems may miss harmful content or flag a link incorrectly. A report does not guarantee an immediate response or a particular outcome.', 'Hizmet, üçüncü taraf hedeflerin tamamını kesintisiz izlemez. Otomatik güvenlik sinyalleri, önceden insan incelemesi olmadan bir bağlantıyı engelleyebilir veya karantinaya alabilir; bu sistemler zararlı içeriği gözden kaçırabilir ya da bir bağlantıyı yanlış işaretleyebilir. Bildirim, anında yanıt veya belirli bir sonuç garantisi vermez.'],
    ];

    const enToTr = new Map();
    const trToEn = new Map();
    for (const [en, tr] of pairs) {
        enToTr.set(en, tr);
        trToEn.set(tr, en);
    }

    function placeholderRegex(value) {
        const marker = '__PULSEROUTE_NUMBER__';
        const source = value.replace(/\{\{[^}]+\}\}/g, marker).replace(/[.*+?^${}()|[\]\\]/g, '\\$&').replaceAll(marker, '([0-9]+)');
        return new RegExp(`^${source}$`);
    }

    const supplementalPairs = [
        ['Other', 'Diğer'], ['Process liveness', 'İşlem canlılık kontrolü'], ['Process liveness | PulseRoute', 'İşlem canlılık kontrolü | PulseRoute'], ['Dependency health', 'Bağımlılık durumu'], ['Dependency health | PulseRoute', 'Bağımlılık durumu | PulseRoute'],
        ['The web process is responding. Dependencies are not queried by this check.', 'Web süreci yanıt veriyor. Bu kontrolde bağımlılıklar sorgulanmaz.'],
        ['Dependency checks are briefly cached per process to reduce database and Redis load.', 'Veritabanı ve Redis yükünü azaltmak için bağımlılık kontrolleri süreç başına kısa süre önbelleğe alınır.'],
        ['HEALTHY', 'SAĞLIKLI'], ['ALIVE', 'ÇALIŞIYOR'], ['DEGRADED', 'KISITLI'], ['connected', 'bağlı'], ['disconnected', 'bağlı değil'], ['disabled or unavailable', 'devre dışı veya kullanılamıyor'],
        ['We aim to follow the Web Content Accessibility Guidelines (', 'Platformu geliştirirken Web İçeriği Erişilebilirlik Kılavuzları ('],
        [') as we improve the platform. This is an ongoing effort, not a third-party certification.', ') doğrultusunda ilerlemeyi hedefliyoruz. Bu devam eden bir çalışmadır; üçüncü taraf sertifikası değildir.'],
        ['The preference cookie', 'Tercih çerezi'],
        [' stores the language you selected in this browser and is not sent to the service.', ' seçtiğiniz dili bu tarayıcıda saklar ve hizmete gönderilmez.'],
        ['The request failed. Check the details and try again.', 'İstek tamamlanamadı. Bilgileri kontrol edip tekrar deneyin.'],
        ['The account could not be created.', 'Hesap oluşturulamadı.'], ['The workspace could not be created.', 'Çalışma alanı oluşturulamadı.'], ['The domain could not be added.', 'Alan adı eklenemedi.'], ['The link could not be created.', 'Bağlantı oluşturulamadı.'],
        ['The report could not be processed. Check the link and try again.', 'Bildirim işlenemedi. Bağlantıyı kontrol edip tekrar deneyin.'],
    ];
    for (const [en, tr] of supplementalPairs) { enToTr.set(en, tr); trToEn.set(tr, en); }

    const dynamicPairs = [...pairs, ...supplementalPairs].filter(([en, tr]) => en.includes('{{') || tr.includes('{{')).map(([en, tr]) => ({
        en,
        tr,
        enRegex: placeholderRegex(en),
        trRegex: placeholderRegex(tr),
    }));
    const originalText = new WeakMap();
    const originalAttributes = new WeakMap();
    const attrNames = ['title', 'placeholder', 'aria-label', 'alt', 'content'];
    let observer;
    let locale = document.documentElement.dataset.locale || 'en';

    function normalize(value) {
        return value.replace(/\s+/g, ' ').trim();
    }

    function translate(value, target = locale) {
        const source = normalize(value);
        const map = target === 'tr' ? enToTr : trToEn;
        let translated = map.get(source);
        if (translated === undefined) {
            for (const entry of dynamicPairs) {
                const sourceRegex = target === 'tr' ? entry.enRegex : entry.trRegex;
                const match = sourceRegex.exec(source);
                if (!match) continue;
                const values = match.slice(1);
                let index = 0;
                translated = (target === 'tr' ? entry.tr : entry.en).replace(/\{\{[^}]+\}\}/g, () => values[index++]);
                break;
            }
        }
        if (translated === undefined) return value;
        const start = value.match(/^\s*/)?.[0] || '';
        const end = value.match(/\s*$/)?.[0] || '';
        return `${start}${translated}${end}`;
    }

    function translateOr(value, fallback, target = locale) {
        const source = normalize(String(value ?? ''));
        const direct = target === 'tr' ? enToTr : trToEn;
        const alreadyLocalized = target === 'tr' ? trToEn : enToTr;
        if (direct.has(source)) return translate(String(value), target);
        if (alreadyLocalized.has(source)) return String(value);
        for (const entry of dynamicPairs) {
            const targetRegex = target === 'tr' ? entry.enRegex : entry.trRegex;
            const currentRegex = target === 'tr' ? entry.trRegex : entry.enRegex;
            if (targetRegex.test(source)) return translate(String(value), target);
            if (currentRegex.test(source)) return String(value);
        }
        return translate(fallback, target);
    }

    function translateNode(node, target) {
        if (node.nodeType === Node.TEXT_NODE) {
            const parent = node.parentElement;
            if (!parent || parent.closest('script,style,noscript,code,pre,[data-no-i18n]')) return;
            if (!originalText.has(node)) originalText.set(node, node.nodeValue);
            const source = originalText.get(node);
            node.nodeValue = translate(source, target);
            return;
        }
        if (node.nodeType !== Node.ELEMENT_NODE) return;
        if (node.matches('script,style,noscript,svg,[data-no-i18n]')) return;
        let originals = originalAttributes.get(node);
        if (!originals) {
            originals = new Map();
            for (const name of attrNames) {
                if (node.hasAttribute(name)) originals.set(name, node.getAttribute(name));
            }
            originalAttributes.set(node, originals);
        }
        for (const [name, source] of originals) node.setAttribute(name, translate(source, target));
        for (const child of node.childNodes) translateNode(child, target);
    }

    function updateButtons(target) {
        document.querySelectorAll('[data-language-switch]').forEach((button) => {
            button.setAttribute('aria-label', target === 'tr' ? 'Dili değiştir; English seç' : 'Change language; select Türkçe');
            button.querySelectorAll('[data-locale-option]').forEach((option) => {
                option.classList.toggle('is-current', option.dataset.localeOption === target);
                option.setAttribute('aria-current', option.dataset.localeOption === target ? 'true' : 'false');
            });
        });
    }

    function setLanguage(target, persist = true) {
        locale = target === 'tr' ? 'tr' : 'en';
        document.documentElement.lang = locale;
        document.documentElement.dataset.locale = locale;
        if (persist) {
            try { localStorage.setItem('pulseroute_locale', locale); } catch (_) {}
        }
        if (observer) observer.disconnect();
        if (document.body) translateNode(document.body, locale);
        for (const meta of document.querySelectorAll('meta[name="description"]')) translateNode(meta, locale);
        document.title = translate(document.title, locale);
        updateButtons(locale);
        window.dispatchEvent(new CustomEvent('pulseroute:localechange', { detail: { locale } }));
        document.documentElement.classList.remove('i18n-pending');
        observe();
    }

    function observe() {
        if (!document.body) return;
        if (!observer) {
            observer = new MutationObserver((records) => {
                observer.disconnect();
                for (const record of records) {
                    if (record.type === 'characterData') translateNode(record.target, locale);
                    for (const node of record.addedNodes || []) translateNode(node, locale);
                }
                observer.observe(document.body, { childList: true, subtree: true, characterData: true });
            });
        }
        observer.observe(document.body, { childList: true, subtree: true, characterData: true });
    }

    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-language-switch]');
        if (button) setLanguage(locale === 'tr' ? 'en' : 'tr');
    });

    window.PulseRouteI18n = { setLanguage, translate, translateOr, get locale() { return locale; } };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', () => setLanguage(locale, false), { once: true });
    } else {
        setLanguage(locale, false);
    }
})();
