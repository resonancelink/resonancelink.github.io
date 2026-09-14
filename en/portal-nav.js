(() => {
  const script = document.currentScript;
  const page = script.dataset.page;
  const rooms = [
    ['zukan','Atlas of Consciousness'],['hikiyose','Law of Attraction Lab'],
    ['guidance','Michiyo’s Guidance'],['michiyo_oraclecards','Today’s Card'],
    ['tamashii_shindan','House of the Soul'],['suki_shindan','Discover What You Love']
  ];
  function run() {
    const nav = document.createElement('nav');
    nav.className = 'en-nav'; nav.setAttribute('aria-label','Main navigation');
    const row=document.createElement('div');row.className='en-nav-inner';
    const home=document.createElement('a');home.href='/en/';home.className='en-home';home.textContent='The Institute';row.append(home);
    const details=document.createElement('details');details.className='en-menu';
    const summary=document.createElement('summary');summary.textContent='Explore';details.append(summary);
    const list=document.createElement('ul');
    rooms.forEach(([key,name])=>{const li=document.createElement('li'),a=document.createElement('a');a.href='/en/'+key+'/';a.textContent=name;if(key===page)a.setAttribute('aria-current','page');li.append(a);list.append(li)});
    details.append(list);row.append(details);
    const lang=document.createElement('a');lang.className='en-japanese';lang.lang='ja';lang.hreflang='ja';lang.textContent='日本語';lang.setAttribute('aria-label','View this page in Japanese');
    const syncLanguage=()=>{lang.href='/'+page+'/'+(location.pathname.endsWith('/about.html')?'about.html':'')+location.hash};
    syncLanguage();addEventListener('hashchange',syncLanguage);['click','focus','pointerenter','contextmenu'].forEach(event=>lang.addEventListener(event,syncLanguage));row.append(lang);nav.append(row);
    document.body.prepend(nav);
    document.addEventListener('click',e=>{if(!details.contains(e.target))details.open=false});
    document.addEventListener('keydown',e=>{if(e.key==='Escape'&&details.open){details.open=false;summary.focus()}});
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',run);else run();
})();
