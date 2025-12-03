import fastapiClient, {getTagById} from '../../fastapiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  const logoutBtn = document.getElementById('logoutBtn');
  if (!logoutBtn) return;

  logoutBtn.addEventListener('click', async (ev) => {
    ev.preventDefault();
    const ok = confirm('정말 로그아웃 하시겠습니까?');
    if (!ok) return;

    try {
      await fastapiClient('post', '/apis/accounts/logout', {});
      window.location.href = '/';
    } catch (err) {
      console.error('logout failed', err);
      const errorTag = getTagById("errorTag");
      errorTag.style.display = 'block';
      errorTag.innerText = '로그아웃 중 오류가 발생했습니다.';
    }
  });
});
