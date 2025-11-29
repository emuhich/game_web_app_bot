function getTelegramUser() {
  try { return Telegram.WebApp.initDataUnsafe.user; } catch { return null; }
}
function getTelegramUserId() {
  try { return Telegram?.WebApp?.initDataUnsafe?.user?.id || null; } catch { return null; }
}
function getQueryUserId(){
  const p = new URLSearchParams(window.location.search);
  const v = p.get('user_id');
  return v ? parseInt(v) : null;
}
function showLoading(flag){
  const l = document.getElementById('loading');
  if(!l) return;
  l.style.display = flag ? 'block' : 'none';
}
function todayISO(){
  const d = new Date();
  return d.toISOString().slice(0,10); // YYYY-MM-DD
}
async function loadApplications(userId) {
  const container = document.getElementById('apps');
  const empty = document.getElementById('empty');
  const status = document.getElementById('status');
  container.innerHTML='';
  if(!userId){ empty.style.display='block'; status.textContent='Не найден user_id'; status.className='status-banner err'; return; }
  status.textContent=''; showLoading(true);
  let res;
  try { res = await fetch(`/api/applications/${userId}`); } catch(e){ status.textContent='Ошибка сети'; status.className='status-banner err'; showLoading(false); return; }
  showLoading(false);
  if(!res.ok){ empty.style.display='block'; status.textContent='Ошибка загрузки'; status.className='status-banner err'; return; }
  const data = await res.json();
  if(!data.length){ empty.style.display='block'; status.textContent='Записей нет'; status.className='status-banner'; return; }
  empty.style.display='none'; status.textContent='';
  data.forEach(app => {
    const card = document.createElement('div');
    card.className='app-card';
    card.innerHTML = `\n      <h3>Запись #${app.application_id}</h3>\n      <div class="app-meta">\n        <span>Услуга: ${app.service_name}</span>\n        <span>Мастер: ${app.master_name}</span>\n        <span>Дата: ${app.appointment_date}</span>\n        <span>Время: ${app.appointment_time}</span>\n        <span>Пол: ${app.gender}</span>\n      </div>\n      <div class="app-actions">\n        <button class="small cancel" data-id="${app.application_id}">Отменить</button>\n        <button class="small reschedule" data-id="${app.application_id}">Перенести</button>\n      </div>\n    `;
    container.appendChild(card);
  });
}
async function cancelApplication(id){
  const status = document.getElementById('status');
  showLoading(true);
  let res; try { res = await fetch(`/api/applications/${id}`, { method:'DELETE' }); } catch(e){ status.textContent='Ошибка сети'; status.className='status-banner err'; showLoading(false); return; }
  showLoading(false);
  if(res.status===204){
    status.textContent = `Заявка #${id} отменена`; status.className='status-banner ok';
    const uid = getTelegramUserId() || getQueryUserId(); if(uid) loadApplications(uid);
  } else {
    status.textContent = `Не удалось отменить заявку #${id}`; status.className='status-banner err';
  }
}
async function rescheduleApplication(id, newDate, newTime){
  const status = document.getElementById('status');
  // Валидация даты > сегодня
  const today = todayISO();
  if(newDate <= today){
    status.textContent = 'Дата должна быть позже сегодняшней';
    status.className='status-banner err';
    return;
  }
  showLoading(true);
  let res; try { res = await fetch(`/api/applications/${id}/reschedule`, {
    method:'PATCH', headers:{'Content-Type':'application/json'}, body:JSON.stringify({appointment_date:newDate, appointment_time:newTime})
  }); } catch(e){ status.textContent='Ошибка сети'; status.className='status-banner err'; showLoading(false); return; }
  showLoading(false);
  if(res.ok){
    status.textContent = `Заявка #${id} перенесена`; status.className='status-banner ok';
    const uid = getTelegramUserId() || getQueryUserId(); if(uid) loadApplications(uid);
  } else {
    const data = await res.json().catch(()=>({detail:'Ошибка'}));
    status.textContent = `Ошибка переноса: ${data.detail}`; status.className='status-banner err';
  }
}
function attachActions(){
  document.getElementById('apps').addEventListener('click', (e)=>{
    const cancelBtn = e.target.closest('button.cancel');
    const reschedBtn = e.target.closest('button.reschedule');
    if(cancelBtn){ cancelApplication(cancelBtn.dataset.id); }
    if(reschedBtn){
      const id = reschedBtn.dataset.id;
      const card = reschedBtn.closest('.app-card');
      if(card.querySelector('.reschedule-form')) return;
      const form = document.createElement('div');
      form.className='reschedule-form';
      form.innerHTML = `\n        <input type="date" class="new-date" required min="${todayISO()}">\n        <input type="time" class="new-time" required>\n        <button type="button" class="do-reschedule">OK</button>\n      `;
      card.appendChild(form);
      form.querySelector('.do-reschedule').addEventListener('click', ()=>{
        const d = form.querySelector('.new-date').value;
        const t = form.querySelector('.new-time').value;
        if(!d || !t){ return; }
        rescheduleApplication(id, d, t);
      });
    }
  });
  const refreshBtn = document.getElementById('refresh-apps');
  if(refreshBtn){
    refreshBtn.addEventListener('click', ()=>{
      const uid = getTelegramUserId() || getQueryUserId();
      if(uid) loadApplications(uid);
    });
  }
}

document.addEventListener('DOMContentLoaded', ()=>{
  const uid = getTelegramUserId() || getQueryUserId();
  if(uid){ loadApplications(uid); } else { document.getElementById('empty').style.display='block'; }
  attachActions();
});
