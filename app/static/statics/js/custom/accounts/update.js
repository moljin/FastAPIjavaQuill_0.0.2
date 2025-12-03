import {getTagById, extractErrorMessage} from '../../fastapiClient.js';
import {accountUpdate, passwordUpdate} from './updateFastAPI.js';

document.addEventListener('DOMContentLoaded', () => {
    const errorTag = getTagById("errorTag");
    let error = null;

    const accountForm = document.getElementById('accountForm');

    accountForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const type = accountForm.elements['type'].value;
        const fd = new FormData(accountForm);
        try {
            if (type === "user") { //username or profile image
                try {
                    // 파일 업로드 여부에 따라 FormData/JSON 분기
                    const fileInput = accountForm.elements['imagefile'];
                    const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;

                    if (hasFile && fileInput.files[0] && fileInput.files[0].name) {
                        fd.append('imagefile', fileInput.files[0]);
                    }

                    let params = fd; // fastapiClient가 FormData면 body로 전송
                    await accountUpdate(ev, {
                        params, setError: (v) => (error = v)
                    });

                } catch (e) {
                    const msg = extractErrorMessage(e) || '인증코드 검증 중에 오류가 발생했습니다.';

                    if (errorTag) {
                        errorTag.style.display = 'block';
                        errorTag.innerText = msg;
                    }
                }
            } else { // password
                try {
                    const params = {
                        user_id: accountForm.elements['user_id'].value,
                        password: accountForm.elements['password'].value,
                        newpassword: accountForm.elements['newpassword'].value,
                        confirmPassword: accountForm.elements['confirmPassword'].value
                    };
                    await passwordUpdate(ev, {
                        params, setError: (v) => (error = v)
                    });

                } catch (e) {
                    const msg = extractErrorMessage(e) || '인증코드 검증 중에 오류가 발생했습니다.';

                    if (errorTag) {
                        errorTag.style.display = 'block';
                        errorTag.innerText = msg;
                    }
                }
            }

        } catch (e) {
            console.error("catch register error", e);
        }
    });


});
