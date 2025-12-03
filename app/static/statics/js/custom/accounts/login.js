import fastapiClient, {getTagById, extractErrorMessage} from '../../fastapiClient.js';

document.addEventListener('DOMContentLoaded', () => {
  const form = document.getElementById('accountForm');
  if (!form) return;
  form.addEventListener('submit', async (ev) => {
    ev.preventDefault();
    const params = {
      email: form.elements['email'].value,
      password: form.elements['password'].value
    };
    const errorTag = getTagById("errorTag");
    try {
      const res = await fastapiClient('post', '/apis/accounts/login', params);
      console.log(res);
      if (res && res.access_token) {
        window.location.href = '/';
      } else {
          errorTag.style.display = 'block';
          errorTag.innerText = extractErrorMessage(res) || "로그인에 실패했습니다.";
      }
    } catch (e) {
        const msg =extractErrorMessage(e);
        errorTag.style.display = 'block';
        errorTag.innerText = msg;
      console.error("catch login error", e);
    }
  });
});
