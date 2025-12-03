import fastapiClient, {extractErrorMessage, getTagById, loginAndRedirect} from "../../fastapiClient.js";

const errorTag = getTagById("errorTag");
const userIDTag = getTagById("userID");

export const accountUpdate = async (event, {params, setError}) => {
    event.preventDefault();
    const url = '/apis/accounts/account/update/' + userIDTag.value;

    try {
        const data = await fastapiClient('patch', url, params);
        window.location.href = '/views/accounts/account/' + userIDTag.value;
    } catch (err) {
        if (setError) {
            const msg = extractErrorMessage(err) || '회원 등록에 실패했습니다.';
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch update error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }
};

export const passwordUpdate = async (event, {params, setError}) => {
    event.preventDefault();
    const url = '/apis/accounts/account/password/update/' + userIDTag.value;

    try {
        const data = await fastapiClient('patch', url, params);
        const loginParams = {email: data.email, password: params.newpassword};
        alert("비밀번호 변경 완료: 새로운 비밀번호로 로그인됩니다.");
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
        //          window.location.href = '/views/accounts/account/' + userIDTag.value;
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


    } catch (err) {
        if (setError) {
            const msg = extractErrorMessage(err) || '회원 등록에 실패했습니다.';
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch passwordUpdate error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }
};