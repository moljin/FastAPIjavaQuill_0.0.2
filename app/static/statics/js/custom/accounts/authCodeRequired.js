import {getTagById, extractErrorMessage} from '../../fastapiClient.js';
import {authCodeRequest, authCodeVerify, accountRegister, lostPasswordReset} from './authCodeFastAPI.js';

document.addEventListener('DOMContentLoaded', () => {
    const authRequestForm = document.getElementById('authRequestForm');
    if (!authRequestForm) return;
    const authVerifyForm = document.getElementById('authVerifyForm');
    if (!authVerifyForm) return;

    const requestEmailInput = document.getElementById('request-email');
    const verifyEmailInput = document.getElementById('verify-email');
    const registerEmailInput = document.getElementById('register-email');
    const errorTag = getTagById("errorTag");
    let error = null;

    requestEmailInput.addEventListener('input', function () {
        // 한 문자씩 타이핑 할 때마다 hidden input 태그에 복사
        verifyEmailInput.value = this.value;
        if (registerEmailInput) registerEmailInput.value = this.value;
    });

    authRequestForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const params = {
            email: authRequestForm.elements['email'].value,
            type: authRequestForm.elements['type'].value
        };
        try {
            await authCodeRequest(ev, {
                params, setError: (v) => (error = v)
            });
        } catch (e) {
            const msg = extractErrorMessage(e) || '인증코드 요청 중 오류가 발생했습니다.';

            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
            }
            console.error("2. catch authcode request error", e);
        }
    });

    authVerifyForm.addEventListener('submit', async (ev) => {
        ev.preventDefault();
        const params = { // 단순 인증하기와 인증과 동시에 이메일 변경
            authcode: authVerifyForm.elements['authcode'].value,
            email: authVerifyForm.elements['email'].value,
            type: authVerifyForm.elements['type'].value,
            old_email: authVerifyForm.elements['old_email'].value,
            password: authVerifyForm.elements['password'].value
        };
        let token = null;
        try {
            await authCodeVerify(ev, {
                params, setError: (v) => (error = v),
                setToken: (v) => (token = v)
            });
        } catch (e) {
            const msg = extractErrorMessage(e) || '인증코드 검증 중에 오류가 발생했습니다.';
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
            }
            console.error("catch authcode verify error", e);
        }
    });

    const accountForm = document.getElementById('accountForm');
    // if (!accountForm) return; 이메일 변경 html에는 이 accountForm이 없어 조기 종료되는 것을 막을 수 있다.
    if (accountForm) {
        accountForm.addEventListener('submit', async (ev) => {
            ev.preventDefault();
            const type = accountForm.elements['type'].value;
            try {
                if (type === "register") {
                    try {
                        // 파일 업로드 여부에 따라 FormData/JSON 분기
                        const fileInput = accountForm.elements['imagefile'];
                        const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
                        const fd = new FormData();
                        fd.append('username', accountForm.elements['username']?.value || '');
                        fd.append('email', accountForm.elements['email']?.value || '');
                        fd.append('token', accountForm.elements['token']?.value || '');
                        fd.append('password', accountForm.elements['password']?.value || '');
                        fd.append('password2', accountForm.elements['password2']?.value || '');
                        if (hasFile && fileInput.files[0] && fileInput.files[0].name) {
                            fd.append('imagefile', fileInput.files[0]);
                        }
                        let params = fd; // fastapiClient가 FormData면 body로 전송


                        await accountRegister(ev, {
                            params, setError: (v) => (error = v)
                        });

                    } catch (e) {
                        const msg = extractErrorMessage(e) || '인증코드 검증 중에 오류가 발생했습니다.';

                        if (errorTag) {
                            errorTag.style.display = 'block';
                            errorTag.innerText = msg;
                        }
                    }

                } else { // 비번 분실
                    try {
                        const params = {
                            email: accountForm.elements['email'].value,
                            token: accountForm.elements['token'].value,
                            newpassword: accountForm.elements['newpassword'].value,
                            confirmPassword: accountForm.elements['confirmPassword'].value
                        };
                        await lostPasswordReset(ev, {
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
    }

});
