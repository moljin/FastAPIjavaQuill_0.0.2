import fastapiClient from './fastapiClient.js';

// set server url if template injected window.SERVER_URL else default
if (typeof window !== 'undefined') {
  if (!window.SERVER_URL || window.SERVER_URL === '') {
    // default to origin
    window.SERVER_URL = window.location.origin;
  }
}

(async function mainInit() {
  try {
    startDigitalClock("clock");

    // call the client to make sure CSRF cookie/token exists
    // optional: pre-fetch CSRF token for pages (useful for forms)
    await fastapiClient('get', '/apis/auth/csrf_token', {});
  } catch (e) {
    // ignore
    console.warn('csrf prefetch failed', e);
  }
})();

function startDigitalClock(target) {
  const el = typeof target === 'string' ? document.getElementById(target) : target;
  if (!el) throw new Error('Clock target element not found');

  function render() {
    const now = new Date();
    const year = String(now.getFullYear()).padStart(4, '0');
    const month = String(now.getMonth() + 1).padStart(2, '0'); // 1월=0 → +1
    const date = String(now.getDate()).padStart(2, '0');
    const hours = String(now.getHours()).padStart(2, '0');
    const minutes = String(now.getMinutes()).padStart(2, '0');
    const seconds = String(now.getSeconds()).padStart(2, '0');
    el.textContent = `${year}-${month}-${date} ${hours}:${minutes}:${seconds}`;
  }

  render(); // 즉시 1회 표시
  const timerId = setInterval(render, 1000);

  // 중지 함수 반환
  return function stop() {
    clearInterval(timerId);
  };
}
