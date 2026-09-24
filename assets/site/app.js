(() => {
  'use strict';
  const root = document.body.dataset.root || './';
  const get = (key, fallback) => { try { return JSON.parse(localStorage.getItem('sparks-v3-' + key)) ?? fallback; } catch { return fallback; } };
  const set = (key, value) => { try { localStorage.setItem('sparks-v3-' + key, JSON.stringify(value)); } catch {} };
  const legacy = (route) => {
    const aliases = {read:'topics/',topics:'topics/',people:'people/',sources:'sources/',timeline:'timeline/',events:'timeline/',debates:'debates/',practice:'practice/',questions:'questions/',glossary:'glossary/',resources:'resources/',skills:'skills/',saved:'saved/',bookmarks:'saved/',about:'about/',welcome:'',home:'',story:'archive.html#c1',tasks:'practice/',methods:'practice/',quotes:'sources/'};
    if (Object.hasOwn(aliases, route)) return aliases[route];
    if (/^c[1-7]$/.test(route)) return 'archive.html#' + route;
    const parts = route.replace(/^(topic|person|source|event|debate|task|method|question)-/, '$1/').split('/');
    const folders = {topic:'topics',person:'people',source:'sources',event:'events',debate:'debates',task:'tasks',method:'methods',question:'questions'};
    if (folders[parts[0]] && /^[a-z]+\d+$/.test(parts[1] || '')) return folders[parts[0]] + '/' + parts[1] + '/';
    if (/^(route|trail|glossary)\//.test(route)) return 'archive.html#' + encodeURI(route);
    return null;
  };
  if (document.body.hasAttribute('data-legacy-router') && location.hash) {
    let hash; try { hash = decodeURIComponent(location.hash.slice(1)); } catch { hash = ''; }
    const target = legacy(hash.replace(/^\/+|\/+$/g,''));
    if (target !== null && target !== '') location.replace(new URL(root + target, location.href));
  }
  document.querySelector('[data-theme-toggle]')?.addEventListener('click', () => {
    const theme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = theme; set('theme', theme);
  });
  document.querySelectorAll('[data-font]').forEach(button => button.addEventListener('click', () => {
    const current = Number(get('font', 17));
    const value = Math.max(16, Math.min(24, (Number.isFinite(current) ? current : 17) + Number(button.dataset.font)));
    document.documentElement.style.setProperty('--reading-size', value + 'px'); set('font',value);
  }));
  const dialog = document.getElementById('join-dialog');
  document.querySelectorAll('[data-join]').forEach(button => button.addEventListener('click', () => {
    if (dialog?.showModal) dialog.showModal(); else location.href = root + 'join/';
  }));
  dialog?.querySelector('[data-close]')?.addEventListener('click', () => dialog.close());
  dialog?.addEventListener('click', e => {
    if (e.target !== dialog) return;
    const b = dialog.getBoundingClientRect();
    if (e.clientX < b.left || e.clientX > b.right || e.clientY < b.top || e.clientY > b.bottom) dialog.close();
  });
  // A group QR is temporary. Do not keep presenting it as usable after its stated date.
  const shanghaiDay = new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
  const expired = shanghaiDay >= '2026-10-01';
  document.querySelectorAll('[data-qr-expired]').forEach(el => el.hidden = !expired);
  document.querySelectorAll('[data-qr-current]').forEach(el => el.hidden = expired);
  const saveButton = document.querySelector('[data-save]');
  const saved = () => { const v=get('saved',[]); return Array.isArray(v) ? v.filter(x=>x && typeof x.route==='string') : []; };
  const reflect = () => {
    if (!saveButton) return;
    const on = saved().some(s => s.route === saveButton.dataset.save);
    saveButton.textContent = on ? '已收藏' : '收藏这篇'; saveButton.setAttribute('aria-pressed',String(on));
  };
  reflect();
  saveButton?.addEventListener('click', () => {
    let items=saved();const route=saveButton.dataset.save;
    if (items.some(x=>x.route===route)) items=items.filter(x=>x.route!==route);
    else items.push({route,title:document.querySelector('h1').textContent,time:Date.now()});
    set('saved',items);reflect();
  });
  const savedList=document.getElementById('saved-list');
  if (savedList) {
    const items=saved().filter(x=>legacy(x.route)!==null);
    if (!items.length) savedList.textContent='还没有收藏。打开一篇话题，在文末点“收藏这篇”。';
    for (const item of items) {
      const li=document.createElement('li');const a=document.createElement('a');
      a.href=root+legacy(item.route);a.textContent=item.title || item.route;li.append(a);savedList.append(li);
    }
  }
  document.querySelector('[data-copy-link]')?.addEventListener('click',async e=>{
    const button=e.currentTarget;
    try{await navigator.clipboard.writeText(location.href);button.textContent='链接已复制';}catch{button.textContent='请复制浏览器地址';}
  });
  const searchForm=document.getElementById('search-form');
  if(searchForm){
    const input=document.getElementById('search-input'), result=document.getElementById('search-results'), count=document.getElementById('search-count');
    const data=window.GUANLAN_SEARCH || [];
    const run=()=>{
      const q=input.value.trim();result.replaceChildren();
      if(!q){count.textContent='输入你关心的问题、关键词或昵称。';return;}
      const terms=q.toLocaleLowerCase().split(/\s+/); const matched=data.filter(x=>terms.every(t=>(x.title+' '+x.text).toLocaleLowerCase().includes(t)));
      matched.sort((a,b)=>Number(terms.every(t=>b.title.toLocaleLowerCase().includes(t)))-Number(terms.every(t=>a.title.toLocaleLowerCase().includes(t))));
      count.textContent=matched.length ? `找到 ${matched.length} 条相关内容` : '没有找到。可以换一个短一些的词，或按话题分类查找。';
      for(const item of matched){
        const li=document.createElement('li'),kind=document.createElement('span'),h=document.createElement('h2'),a=document.createElement('a'),p=document.createElement('p');
        kind.className='search-result-kind';kind.textContent=item.kind;a.href=root+item.url;a.textContent=item.title;h.append(a);
        let start=Math.max(0,item.text.toLocaleLowerCase().indexOf(terms[0])-35);
        p.textContent=(start?'…':'')+item.text.slice(start,start+150)+(item.text.length>start+150?'…':'');li.append(kind,h,p);result.append(li);
      }
    };
    const params=new URLSearchParams(location.search);input.value=params.get('q') || '';run();
    searchForm.addEventListener('submit',e=>{e.preventDefault();const q=input.value.trim();history.replaceState(null,'',location.pathname+(q?'?q='+encodeURIComponent(q):''));run();});
  }
})();
