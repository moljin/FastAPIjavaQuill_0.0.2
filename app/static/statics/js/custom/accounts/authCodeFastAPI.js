import fastapiClient, {extractErrorMessage, getTagById, loginAndRedirect, getParam} from '../../fastapiClient.js';

// 값이 undefined/null/'' 인 키 제거
const compact = (obj) =>
    Object.fromEntries(
        Object.entries(obj).filter(([, v]) => v !== undefined && v !== null && v !== "")
    );

const errorTag = getTagById("errorTag");
const userIDTag = getTagById("userID");

if (userIDTag) {console.log("userIDTag.value: ", userIDTag.value)} else console.log("userIDTag", userIDTag);

export const authCodeRequest = async (event, {params, setError}) => {
    event.preventDefault();
    const requestFormElement = document.getElementById("authRequestForm");
    const verifyFormElement = document.getElementById("authVerifyForm");
    const oldEmailInput = document.getElementById("old-email");

    const url = '/apis/accounts/authcode/request';
    const requestEmailInput = document.getElementById("request-email");

    try {
        const data = await fastapiClient('post', url, params);
        alert(data.message);
        if (!oldEmailInput) {
            requestFormElement.style.display = "none";
            verifyFormElement.style.display = "block";
        } else {
            if (requestEmailInput) {
                requestEmailInput.readOnly = true;
                Object.assign(requestEmailInput.style, {
                    backgroundColor: "#f8f8f8",
                    color: "#999",
                    borderColor: "#e5e5e5",
                });
            }
        }
    } catch (err) {
        console.log("실패", err);
        if (setError) {
            const msg = extractErrorMessage(err);
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch auth request error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
        // **에러를 다시 던지더라도, 그 전에 에 원하는 내용을 넣어 두면
        // 화면에는 그대로 노출`errorTag.innerText`**됩니다.
    }
};

export const authCodeVerify = async (event, {params, setError, setToken}) => {
    event.preventDefault();

    const verifyFormElement = document.getElementById("authVerifyForm");
    const accountFormElement = document.getElementById("accountForm");

    const requestEmailInput = document.getElementById("request-email");
    const verifiedTokenInput = document.getElementById('verified-token');

    const url = '/apis/accounts/authcode/verify';
    // 선택 파라미터는 compact로 제거
    // const params = compact({email, authcode, type, old_email, password});

    try {
        const data = await fastapiClient('post', url, params);
        alert(data.message);
        if (typeof setToken === "function" && data && data.verified_token) {
            setToken(data["verified_token"]); // setToken(data.verified_token); 같은 의미
        }
        if (requestEmailInput) {
            requestEmailInput.readOnly = true;
            Object.assign(requestEmailInput.style, {
                backgroundColor: "#f8f8f8",
                color: "#999",
                borderColor: "#e5e5e5",
            });
        }

        if (["register", "lost"].includes(params?.type)) {
            if (verifiedTokenInput) verifiedTokenInput.value = data["verified_token"];
            if (verifyFormElement) verifyFormElement.style.display = "none";
            if (accountFormElement) accountFormElement.style.display = "block";
        } else {
            const loginParams = {email: params.email, password: params.password};
            await loginAndRedirect(loginParams, {
                userIdValue: userIDTag.value,
                errorTag, // 에러 메시지를 표시할 엘리먼트
                // redirectTo: '/원하면/완전한/경로',  // 필요 시 전체 경로 직접 지정
                // redirectBase: '/views/accounts/account/', // 기본값 유지 시 생략
                // onError: (msg, err) => { /* 필요 시 추가 로깅/처리 */ },
            });

            // try {
            //     const res = await fastapiClient('post', '/apis/accounts/login', loginParams);
            //     if (res && res.access_token) {
            //         window.location.href = '/views/accounts/account/' + userIDTag.value;
            //     } else {
            //         errorTag.style.display = 'block';
            //         errorTag.innerText = extractErrorMessage(res) || "로그인에 실패했습니다.";
            //     }
            // } catch (e) {
            //     const msg = extractErrorMessage(e) || "로그인에 실패했습니다.";
            //     errorTag.style.display = 'block';
            //     errorTag.innerText = msg;
            //     console.error("catch login error", e);
            // }
        }


    } catch (err) {
        console.log("실패", err);
        if (setError) {
            const msg = extractErrorMessage(err);
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch auth verify error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }

};

export const accountRegister = async (event, {params, setError}) => {
    event.preventDefault();
    const url = '/apis/accounts/register';

    try {
        const data = await fastapiClient('post', url, params);
        alert("회원가입 완료: 이메일과 비밀번호로 로그인됩니다.");
        const email = getParam(params, 'email');
        const password = getParam(params, 'password');

        const loginParams = {email: email, password: password};
        await loginAndRedirect(loginParams, {
            userIdValue: null, // 홈으로 ...
            // userIdValue: data.id, // 회원 상세페이지로 ...
            errorTag, // 에러 메시지를 표시할 엘리먼트
            // redirectTo: '/원하면/완전한/경로',  // 필요 시 전체 경로 직접 지정
            // redirectBase: '/views/accounts/account/', // 기본값 유지 시 생략
            // onError: (msg, err) => { /* 필요 시 추가 로깅/처리 */ },
        });
    } catch (err) {
        console.log("register 실패", err);           // 실패 시 error/response 로그
        if (setError) {
            const msg = extractErrorMessage(err) || '회원 등록에 실패했습니다.';
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch register error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }
};

export const lostPasswordReset = async (event, {params, setError}) => {
    event.preventDefault();
    const url = '/apis/accounts/lost/password/resetting';

    try {
        const data = await fastapiClient('patch', url, params);
        console.log("lost password reset 성공", data);          // 성공 시 response data 로그
        console.log("params: ", params)
        alert("비밀번호 설정 성공: 재설정된 비밀번호로 로그인됩니다.");

        const loginParams = {email: params.email, password: params.newpassword};
        await loginAndRedirect(loginParams, {
            // userIdValue: null, // 홈으로 ...
            userIdValue: data.id, // 회원 상세페이지로...
            errorTag, // 에러 메시지를 표시할 엘리먼트
            // redirectTo: '/원하면/완전한/경로',  // 필요 시 전체 경로 직접 지정
            // redirectBase: '/views/accounts/account/', // 기본값 유지 시 생략
            // onError: (msg, err) => { /* 필요 시 추가 로깅/처리 */ },
        });
    } catch (err) {
        console.log("lost password reset 실패", err);           // 실패 시 error/response 로그
        if (setError) {
            const msg = extractErrorMessage(err);
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch lost password reset error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }
};