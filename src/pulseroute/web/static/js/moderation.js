(() => {
  const api = '/api/v1/moderation';
  const $ = (s) => document.querySelector(s);
  const labels = {
    tr: {history:'Karar geçmişi', masked:'Maskelenmiş IP', reports:'Bildirimler', restricted:'Kısıtlananlar', appeals:'İtirazlar', loading:'Yükleniyor…', empty:'Bu kuyrukta kayıt yok.', failed:'İstek tamamlanamadı. Yeniden deneyin.', report:'GÜVENLİK BİLDİRİMİ', appeal:'KALDIRMA İTİRAZI', link:'BAĞLANTI DURUMU', id:'Kayıt', email:'Bildiren', reason:'Kategori', submitted:'Gönderilme', details:'Açıklama', target:'Hedef', state:'Durum', approve:'Onayla ve kaldır', reject:'Reddet', quarantine:'Karantinaya al', release:'Karantinadan çıkar', ban:'Yasakla', unban:'Yasağı kaldır', note:'İç not (isteğe bağlı)', reportDesc:'Bildirimi onaylamak kısa bağlantıyı kaldırır.', appealDesc:'İtirazı onaylamak bağlantıdaki kısıtlamayı kaldırır.', saved:'Karar kaydedildi.', signed:'Oturum açıldı.', removed:'Kaldırıldı', banned:'Yasaklı', quarantined:'Karantinada', active:'Etkin', new:'Yeni', pending:'Bekliyor', approved:'Onaylandı', rejected:'Reddedildi', signout:'Oturum kapatılamadı.'},
    en: {history:'Decision history', masked:'Masked IP', reports:'Reports', restricted:'Restricted', appeals:'Appeals', loading:'Loading…', empty:'Nothing in this queue.', failed:'Request failed. Please try again.', report:'SAFETY REPORT', appeal:'REMOVAL APPEAL', link:'LINK STATUS', id:'Record', email:'Reporter', reason:'Category', submitted:'Submitted', details:'Details', target:'Destination', state:'Status', approve:'Approve & remove', reject:'Reject', quarantine:'Quarantine', release:'Release quarantine', ban:'Ban', unban:'Remove ban', note:'Internal note (optional)', reportDesc:'Approving a report removes the short link.', appealDesc:'Approving an appeal removes the link restriction.', saved:'Decision saved.', signed:'Signed in.', removed:'Removed', banned:'Banned', quarantined:'Quarantined', active:'Active', new:'New', pending:'Pending', approved:'Approved', rejected:'Rejected', signout:'Could not sign out.'}
  };
  let locale = document.documentElement.lang === 'tr' ? 'tr' : 'en';
  let queue = 'reports', cursor = null, selected = null, cacheItems = [];
  const tr = (s) => labels[locale][s] || s;
  const safe = (v) => v == null || v === '' ? '—' : String(v);
  const request = async (url, options = {}) => {
    const res = await fetch(url, {credentials:'same-origin', ...options, headers:{'Content-Type':'application/json', ...(options.headers || {})}});
    if (!res.ok) { if (res.status === 401) showLogin(); throw new Error(res.status === 404 ? 'not-found' : 'request'); }
    return res.status === 204 ? null : res.json();
  };
  function showLogin() { $('#login-view').hidden = false; $('#desk-view').hidden = true; $('#logout').hidden = true; }
  function showDesk() { $('#login-view').hidden = true; $('#desk-view').hidden = false; $('#logout').hidden = false; loadQueue(true); }
  async function checkSession() { try { await request(`${api}/session`); showDesk(); } catch (_) { showLogin(); } }
  function drawQueue() {
    const host = $('#queue-list'); host.replaceChildren();
    if (!cacheItems.length) { const p = document.createElement('p'); p.className='queue-empty'; p.textContent=tr('empty'); host.append(p); return; }
    for (const item of cacheItems) {
      const button = document.createElement('button'); button.className=`queue-item${selected?.id === item.id ? ' selected' : ''}`; button.type='button';
      const title = document.createElement('span'); title.className='queue-item-title'; title.textContent=item.slug || `#${item.id}`;
      const meta = document.createElement('span'); meta.className='queue-item-meta'; meta.textContent=`#${item.id} · ${new Date(item.created_at || item.moderation_updated_at || Date.now()).toLocaleDateString(locale === 'tr' ? 'tr-TR' : 'en-US')}`;
      const status = document.createElement('span'); status.className='queue-item-status'; status.textContent=tr(item.review_status || item.status || item.moderation_status || 'new');
      button.append(title, status, meta); button.addEventListener('click', () => openItem(item)); host.append(button);
    }
  }
  async function loadQueue(reset=false) {
    if (reset) { cursor=null; cacheItems=[]; $('#queue-list').innerHTML=`<p class="queue-empty">${tr('loading')}</p>`; }
    let url = queue === 'reports' ? `${api}/reports?status=new` : queue === 'appeals' ? `${api}/appeals?status=pending` : `${api}/restricted`;
    if (cursor) url += `&before=${encodeURIComponent(cursor)}`;
    try { const data=await request(url); cacheItems=reset?data.items:cacheItems.concat(data.items); cursor=data.next; $('#load-more').hidden=!cursor; drawQueue(); }
    catch (_) { $('#queue-list').textContent=tr('failed'); }
  }
  function field(dl, key, value, url=false) { const dt=document.createElement('dt'); dt.textContent=tr(key); const dd=document.createElement('dd'); if(url && value){const a=document.createElement('a');a.href=value;a.target='_blank';a.rel='noopener noreferrer';a.className='detail-url';a.textContent=value;dd.append(a)}else dd.textContent=safe(value);dl.append(dt,dd); }
  async function openItem(item) {
    selected=item; drawQueue(); const article=$('#detail-card'); article.hidden=false; article.replaceChildren(); $('#empty-detail').hidden=true;
    const endpoint=queue==='reports'?`${api}/reports/${item.id}`:queue==='appeals'?`${api}/appeals/${item.id}`:`${api}/links/${item.id}`;
    let data=item;
    if(endpoint){try{data=await request(endpoint)}catch(_){article.textContent=tr('failed');return}}
    const heading=document.createElement('p');heading.className='detail-kicker';heading.textContent=queue==='reports'?tr('report'):queue==='appeals'?tr('appeal'):tr('link');
    const title=document.createElement('h2');title.className='detail-title';title.textContent=data.slug || '—';
    const meta=document.createElement('p');meta.className='detail-meta';meta.textContent=`#${data.id} · ${new Date(data.created_at || Date.now()).toLocaleString(locale==='tr'?'tr-TR':'en-US')}`;
    const rule=document.createElement('hr');rule.className='detail-rule';const dl=document.createElement('dl');dl.className='detail-grid';
    if(queue==='reports'){field(dl,'email',data.reporter_email);field(dl,'masked',data.masked_ip);field(dl,'reason',data.reason);field(dl,'state',data.review_status);field(dl,'target',data.destination_url,true);field(dl,'details',data.details)}
    else if(queue==='appeals'){field(dl,'email',data.requester_email);field(dl,'state',data.link_status);field(dl,'target',data.destination_url,true);field(dl,'details',data.details)}
    else {field(dl,'state',data.moderation_status);field(dl,'reason',data.quarantine_reason);}
    const actions=document.createElement('div');actions.className='detail-actions';
    const note=document.createElement('textarea');note.className='detail-note';note.placeholder=tr('note');note.setAttribute('aria-label',tr('note'));
    const description=document.createElement('small');description.className='detail-meta';description.textContent=queue==='reports'?tr('reportDesc'):queue==='appeals'?tr('appealDesc'):'';
    const buttons=queue==='reports'?[['approve','danger'],['reject',''],['quarantine','']]:queue==='appeals'?[['approve',''],['reject','danger']]:data.moderation_status==='banned'?[['unban',''],['ban','danger']]:data.moderation_status==='quarantined'?[['release',''],['ban','danger']]:[['release',''],['ban','danger']];
    for(const [decision,style] of buttons){const b=document.createElement('button');b.type='button';b.className=`action-button ${style}`;b.textContent=tr(decision);b.addEventListener('click',()=>decide(item,decision,note.value));actions.append(b)}
    article.append(heading,title,meta,rule,dl,description,note,actions);
    if(data.history?.length){const historyTitle=document.createElement('h3');historyTitle.className='detail-kicker';historyTitle.textContent=tr('history');const historyList=document.createElement('ol');historyList.className='decision-history';for(const entry of data.history){const row=document.createElement('li');row.textContent=`${entry.action} · ${entry.actor} · ${new Date(entry.created_at).toLocaleString(locale==='tr'?'tr-TR':'en-US')}${entry.note?` — ${entry.note}`:''}`;historyList.append(row)}article.append(historyTitle,historyList)}
  }
  async function decide(item, decision, note) {
    const path=queue==='reports'?`${api}/reports/${item.id}/decision`:queue==='appeals'?`${api}/appeals/${item.id}/decision`:`${api}/links/${item.id}/decision`;
    try { await request(path,{method:'POST',body:JSON.stringify({decision,note})}); selected=null; $('#detail-card').hidden=true;$('#empty-detail').hidden=false;await loadQueue(true); }
    catch(_){window.alert(tr('failed'))}
  }
  $('#login-form').addEventListener('submit',async(event)=>{event.preventDefault();const form=new FormData(event.currentTarget);$('#login-error').textContent='';try{await request(`${api}/session`,{method:'POST',body:JSON.stringify({email:form.get('email'),password:form.get('password')})});event.currentTarget.reset();showDesk()}catch(_){$('#login-error').textContent=tr('failed')}});
  $('#logout').addEventListener('click',async()=>{try{await request(`${api}/session`,{method:'DELETE'});showLogin()}catch(_){window.alert(tr('signout'))}});
  document.querySelectorAll('.queue-tab').forEach((button)=>button.addEventListener('click',()=>{queue=button.dataset.queue;selected=null;document.querySelectorAll('.queue-tab').forEach(x=>x.classList.toggle('active',x===button));$('#detail-card').hidden=true;$('#empty-detail').hidden=false;loadQueue(true)}));
  $('#load-more').addEventListener('click',()=>loadQueue(false));
  window.addEventListener('pulseroute:localechange',(event)=>{locale=event.detail.locale; if(!$('#desk-view').hidden)loadQueue(true)});
  checkSession();
})();
