async function fetchOptions() {
  try {
    const [servicesRes, mastersRes] = await Promise.all([
      fetch('/api/services'),
      fetch('/api/masters')
    ]);
    if (!servicesRes.ok || !mastersRes.ok) throw new Error('Не удалось загрузить справочники');
    const services = await servicesRes.json();
    const masters = await mastersRes.json();
    const serviceSelect = document.getElementById('service_id');
    const masterSelect = document.getElementById('master_id');
    services.forEach(s => {
      const opt = document.createElement('option');
      opt.value = s.service_id; opt.textContent = s.service_name; serviceSelect.appendChild(opt);
    });
    masters.forEach(m => {
      const opt = document.createElement('option');
      opt.value = m.master_id; opt.textContent = m.master_name; masterSelect.appendChild(opt);
    });
  } catch (e) {
    const statusEl = document.getElementById('status');
    statusEl.textContent = 'Ошибка загрузки данных: ' + e.message;
    statusEl.className = 'status-message error';
  }
}

function prefillFromQuery() {
  const params = new URLSearchParams(window.location.search);
  const userId = params.get('user_id');
  const firstName = params.get('first_name');
  if (userId) {
    document.getElementById('user_id').value = userId;
  }
  if (firstName) {
    document.getElementById('client_name').value = firstName;
  }
}

document.addEventListener('DOMContentLoaded', () => {
  prefillFromQuery();
  fetchOptions();
  const form = document.getElementById('application-form');
  const statusEl = document.getElementById('status');
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    statusEl.textContent = '';
    const formData = new FormData(form);
    const payload = Object.fromEntries(formData.entries());
    if (!payload.gender) { statusEl.textContent = 'Выберите пол'; statusEl.className='status-message error'; return; }
    try {
      const res = await fetch('/api/applications', {
        method:'POST',
        headers:{'Content-Type':'application/json'},
        body: JSON.stringify({
          user_id: parseInt(payload.user_id || '0'),
          master_id: parseInt(payload.master_id),
          service_id: parseInt(payload.service_id),
          appointment_date: payload.appointment_date,
          appointment_time: payload.appointment_time,
          gender: payload.gender,
          client_name: payload.client_name
        })
      });
      if (!res.ok) throw new Error('Ошибка запроса');
      const data = await res.json();
      statusEl.textContent = 'Запись создана! ID: ' + data.id;
      statusEl.className='status-message success';
      form.reset();
    } catch (err) {
      statusEl.textContent = 'Ошибка: ' + err.message;
      statusEl.className='status-message error';
    }
  });
});
