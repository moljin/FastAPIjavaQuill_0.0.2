const STORAGE_KEY = 'access_token';
const ACCESS_TOKEN_COOKIE_NAME = 'access_token';
const ACCESS_TOKEN_EXPIRE = 30; // 백엔드와 맞춤
let SERVER_URL = (typeof window !== 'undefined' && window.SERVER_URL) ? window.SERVER_URL.replace(/\/+$/, '') : '';


export function getTagById(idName) {
    return document.getElementById(idName);
}

export function gerUserEmailTag() {
    return document.getElementById('userEmail');
}

/**
 * FormData 또는 일반 객체에서 키에 대한 값을 안전하게 가져옵니다.
 * - FormData면 .get(key) 결과(첫 번째 값)를 반환
 * - 일반 객체면 obj[key]를 반환
 */
export function getParam(params, key) {
    const isFormData =
        typeof FormData !== 'undefined' && params instanceof FormData;
    return isFormData ? params.get(key) : params?.[key];
}


export function getCookie(name) {
    if (typeof document === 'undefined') return '';
    const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
    return m ? decodeURIComponent(m.pop()) : '';
}

async function ensureCsrfToken() {
    let csrf_token = getCookie('csrf_token') || getCookie('csrftoken') || '';
    if (csrf_token) return csrf_token;
    // fetch server endpoint to ensure cookie and get token in JSON
    try {
        const url = (SERVER_URL || '') + '/apis/auth/csrf_token';
        const res = await fetch(url, {method: 'GET', credentials: 'include'});
        if (!res.ok) return '';
        const j = await res.json();
        csrf_token = j && (j.csrf_token || j.csrf || j.token) || '';
        return csrf_token;
    } catch (e) {
        console.warn('Failed to fetch csrf token', e);
        return '';
    }
}

// 공통 에러 메시지 정규화 헬퍼 (업데이트)
export function extractErrorMessage(err) {
    const toStr = (s) => (s ?? '').toString();
    const strip = (s) => toStr(s).replace(/^Error:\s*/, '');
    const tryParse = (s) => {
        if (typeof s !== 'string') return null;
        const t = s.trim();
        if (!(t.startsWith('{') || t.startsWith('['))) return null;
        try {
            return JSON.parse(t);
        } catch {
            return null;
        }
    };

    // 1) 문자열
    if (typeof err === 'string') {
        const parsed = tryParse(err);
        if (parsed) return extractErrorMessage(parsed);
        return strip(err);
    }

    // 2) Error 인스턴스
    if (err instanceof Error) {
        const msg = strip(err.message);
        const parsed = tryParse(msg);
        if (parsed) return extractErrorMessage(parsed);
        if (msg && msg !== '[object Object]') return msg;

        // Error에 실린 부가 정보 탐색
        if (err.cause) {
            const fromCause = extractErrorMessage(err.cause);
            if (fromCause && fromCause !== '[object Object]') return fromCause;
        }
        if (err.data) {
            const fromData = extractErrorMessage(err.data);
            if (fromData) return fromData;
        }
        if (err.response && err.response.data) {
            const fromResp = extractErrorMessage(err.response.data);
            if (fromResp) return fromResp;
        }
    }

    // 3) 서버 응답으로 추정되는 페이로드 탐색
    const data =
        err?.response?.data ??
        err?.data ??
        err?.body ??
        err?.payload ??
        err?.json ??
        err?.error ??
        err;

    // FastAPI: detail이 문자열
    if (typeof data?.detail === 'string' && data.detail) return data.detail;

    // FastAPI: detail이 배열(검증 오류) → msg 모아 출력
    if (Array.isArray(data?.detail)) {
        const msgs = data.detail
            .map((d) => d?.msg || d?.message || (typeof d === 'string' ? d : ''))
            .filter(Boolean);
        if (msgs.length) return msgs.join('\n');
    }

    // FastAPI: detail이 객체({필드: [메시지, ...]}) → 첫 메시지만 반환
    if (data && data.detail && typeof data.detail === 'object' && !Array.isArray(data.detail)) {
        const values = Object.values(data.detail);
        const firstValue = values.length ? values[0] : undefined;

        // 배열이면 첫 번째 요소, 아니면 값 자체를 메시지로 사용
        const rawMessage = Array.isArray(firstValue) ? firstValue[0] : firstValue;

        // 문자열화했을 때 [object Object]가 아니면 그대로 반환, 아니면 기본 메시지
        const message = toStr(rawMessage);
        return message && message !== '[object Object]'
            ? message
            : '알 수 없는 오류가 발생했습니다.';
    }


    // 일반적인 필드
    if (typeof data?.message === 'string' && data.message) return data.message;
    if (typeof data?.msg === 'string' && data.msg) return data.msg;
    if (typeof data?.error === 'string' && data.error) return data.error;

    // 상태 텍스트 보조
    const statusText = err?.response?.statusText || err?.statusText || err?.status?.text;
    if (typeof statusText === 'string' && statusText) return statusText;

    // 마지막 수단
    if (data && typeof data === 'object') {
        const nested = data?.error || data?.errors;
        if (nested) {
            const nm = extractErrorMessage(nested);
            if (nm) return nm;
        }
        try {
            return JSON.stringify(data);
        } catch {
        }
    }

    return '오류가 발생했습니다.';
}

// 실패 응답을 Error로 만들 때 원본 페이로드를 보존해 주는 유틸 (추가)
async function throwForBadResponse(res) {
    let payload = null;
    try {
        const ct = res.headers.get('content-type') || '';
        if (ct.includes('application/json')) payload = await res.json();
        else payload = await res.text();
    } catch (_) {
        payload = null;
    }

    const message =
        extractErrorMessage(payload) ||
        res.statusText ||
        `HTTP ${res.status}`;

    // cause/data에 원본을 담아두면 상위에서 extractErrorMessage가 복원 가능
    const error = new Error(message, {cause: payload ?? undefined});
    error.status = res.status;
    error.data = payload;
    throw error;
}


/**
 * fastapiClient(operation, url, params, success_callback, failure_callback)
 */
// helper: shallow build query string
function buildQuery(paramsObj = {}) {
    const usp = new URLSearchParams();
    Object.entries(paramsObj || {}).forEach(([k, v]) => {
        if (v === undefined || v === null || v === '') return;
        if (Array.isArray(v)) {
            v.forEach((item) => {
                if (item !== undefined && item !== null && item !== '') usp.append(k, String(item));
            });
        } else {
            usp.append(k, String(v));
        }
    });
    const s = usp.toString();
    return s ? `?${s}` : '';
}

function hasFileValue(obj) {
    if (!obj || typeof obj !== 'object') return false;
    for (const v of Object.values(obj)) {
        if (!v) continue;
        if (typeof File !== 'undefined' && v instanceof File) return true;
        if (typeof Blob !== 'undefined' && v instanceof Blob) return true;
        if (typeof FileList !== 'undefined' && v instanceof FileList && v.length > 0) return true;
        if (typeof v === 'object' && hasFileValue(v)) return true;
    }
    return false;
}

function objectToFormData(obj, form = new FormData(), prefix = '') {
    if (!obj || typeof obj !== 'object') return form;
    for (const [key, value] of Object.entries(obj)) {
        const formKey = prefix ? `${prefix}.${key}` : key;
        if (value === undefined || value === null) continue;

        if (typeof File !== 'undefined' && value instanceof File) {
            form.append(formKey, value);
        } else if (typeof Blob !== 'undefined' && value instanceof Blob) {
            const filename = (value && value.name) || 'blob';
            form.append(formKey, value, filename);
        } else if (typeof FileList !== 'undefined' && value instanceof FileList) {
            Array.from(value).forEach((f) => form.append(formKey, f));
        } else if (Array.isArray(value)) {
            value.forEach((item) => {
                if (item === undefined || item === null) return;
                if (typeof item === 'object' && !(item instanceof Date)) {
                    objectToFormData(item, form, `${formKey}[]`);
                } else {
                    form.append(`${formKey}[]`, String(item));
                }
            });
        } else if (value instanceof Date) {
            form.append(formKey, value.toISOString());
        } else if (typeof value === 'object') {
            objectToFormData(value, form, formKey);
        } else {
            form.append(formKey, String(value));
        }
    }
    return form;
}

export default async function fastapiClient(operation, url, params = {}, success_callback = () => {
}, failure_callback = () => {
}) {
    const method = (operation || 'GET').toUpperCase();
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 20000);
    const errorTag = getTagById("errorTag");

    if (!SERVER_URL) {
        SERVER_URL = (typeof window !== 'undefined' && window.SERVER_URL) ? window.SERVER_URL.replace(/\/+$/, '') : '';
    }

    // Split query/body with backward compatibility:
    // - If params is FormData => body = params
    // - If params has shape { query, body, useFormData } => use that
    // - Else: GET/DELETE -> params as query, others -> params as body
    let queryObj = {};
    let bodyCandidate = null;
    let forceForm = false;

    if (typeof FormData !== 'undefined' && params instanceof FormData) {
        bodyCandidate = params;
    } else if (params && (Object.prototype.hasOwnProperty.call(params, 'body') || Object.prototype.hasOwnProperty.call(params, 'query'))) {
        queryObj = params.query || {};
        bodyCandidate = Object.prototype.hasOwnProperty.call(params, 'body') ? params.body : null;
        forceForm = !!params.useFormData;
    } else {
        if (method === 'GET' || method === 'DELETE') {
            queryObj = params || {};
        } else {
            bodyCandidate = params || {};
        }
    }

    // Build URL with query
    const base = (SERVER_URL || '') + url.replace(/\/+$/, '');
    const qs = buildQuery(queryObj);
    const fullUrl = base + qs;

    // Decide body + headers for JSON vs FormData
    let body = null;
    let isForm = false;

    if (bodyCandidate != null && method !== 'GET' && method !== 'DELETE') {
        if (typeof FormData !== 'undefined' && bodyCandidate instanceof FormData) {
            body = bodyCandidate;
            isForm = true;
        } else if (forceForm || hasFileValue(bodyCandidate)) {
            body = objectToFormData(bodyCandidate);
            isForm = true;
        } else {
            body = JSON.stringify(bodyCandidate);
            isForm = false;
        }
    }

    const headers = {};

    // Only set Content-Type for JSON; for FormData let browser set multipart boundary
    if (!isForm) {
        headers['Content-Type'] = 'application/json';
    }

    // Attach tokens if available
    // const accessToken = getAccessToken();
    // if (accessToken) {
    //   headers['Authorization'] = `Bearer ${accessToken}`;
    // }
    try {
        const csrf_token = await ensureCsrfToken();
        if (csrf_token) {
            headers['X-CSRF-Token'] = csrf_token;
        }
    } catch (e) {
        // non-fatal
    }

    const fetchOptions = {
        method,
        headers,
        credentials: 'include',
        signal: controller.signal,
    };

    if (body != null) {
        fetchOptions.body = body;
    }

    try {
        const res = await fetch(fullUrl, fetchOptions);
        if (!res.ok) await throwForBadResponse(res);

        const contentType = res.headers.get('content-type') || '';
        let payload = null;
        if (contentType.includes('application/json')) {
            payload = await res.json();
        } else {
            const text = await res.text();
            try {
                payload = JSON.parse(text);
            } catch {
                payload = {detail: text};
            }
        }

        if (res.ok) {
            success_callback(payload, res);
            return payload;
        }

        if (errorTag) {
            errorTag.innerText = (payload && (payload.detail || payload.message)) || `Error ${res.status}: ${res.statusText}`;
        }
        failure_callback(payload, res);
        return Promise.reject(payload);
    } catch (err) {
        if (errorTag) {
            if (err.name === "AbortError") {
                errorTag.innerText = "요청이 시간 초과되었습니다. 네트워크 상태를 확인한 뒤 다시 시도해 주세요.";
            } else {
                console.error("Delete error", err);
                errorTag.innerText = err && err.message ? err.message : 'Network error 혹은 삭제 처리 중 오류가 발생했습니다.';
            }
        }
        failure_callback(err);
        throw err;
    }
    finally {
        clearTimeout(timeoutId);
    }
}

// 공통 로그인 처리 함수
export async function loginAndRedirect(loginParams, {
    userIdValue,
    // redirectTo가 있으면 그대로 사용, 없으면 redirectBase + userIdValue
    redirectTo,
    redirectBase = '/views/accounts/account/',
    errorTag,
    fallbackMessage = '로그인에 실패했습니다.',
    onError, // 필요 시 커스텀 에러 핸들러 (msg, err) => void
} = {}) {
    // 내부 헬퍼: 에러 메시지 표시
    const showError = (msg, err) => {
        if (errorTag) {
            errorTag.style.display = 'block';
            errorTag.innerText = msg;
        }
        if (typeof onError === 'function') {
            try {
                onError(msg, err);
            } catch (_) {
            }
        }
    };

    try {
        const res = await fastapiClient('post', '/apis/accounts/login', loginParams);

        if (res && res.access_token) {
            const hasUserId =
                userIdValue !== undefined &&
                userIdValue !== null &&
                String(userIdValue).trim() !== '';

            window.location.href = redirectTo ?? (hasUserId ? (redirectBase + userIdValue) : '/');
            /* - redirectTo가 설정되어 있으면 그 값으로 이동합니다.
               - redirectTo가 없고 userIdValue가 비어 있으면 '/'로 이동합니다.
               - redirectTo가 없고 userIdValue가 값이 있으면 redirectBase + userIdValue로 이동합니다.
               */
            return {ok: true, data: res};
        }

        const msg = extractErrorMessage(res) || fallbackMessage;
        showError(msg, res);
        return {ok: false, error: res, message: msg};
    } catch (e) {
        const msg = extractErrorMessage(e) || fallbackMessage;
        showError(msg, e);
        return {ok: false, error: e, message: msg};
    }
}
