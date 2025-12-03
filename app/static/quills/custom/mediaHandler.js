//////////// 안전한 ImageResize 등록: 모듈화 전작업 /////////////////////////////////////////////////////////////////////////
import {extractErrorMessage, getTagById, getCookie} from "../../statics/js/fastapiClient.js";
const errorTag = getTagById('errorTag');

// ... 최상단 혹은 관련 코드 위쪽에 추가하세요.
let __mediaHandlerInstance = null;

/**
 * Quill 툴바 핸들러(image/video)가 사용할 공용 핸들러 인스턴스를 설정합니다.
 * 호출 시점: Quill 생성 직후, 업로드 URL을 포함한 QuillImageVideoHandler를 만들고 여기로 전달
 */
export function setMediaHandlerInstance(instance) {
    __mediaHandlerInstance = instance;
}

/**
 * 내부에서 사용할 getter
 * imageInsertByToolbarButton / videoInsertByToolbarButton 내에서 이 함수를 사용해 인스턴스를 참조하도록 하세요.
 */
export function getMediaHandlerInstance() {
    if (!__mediaHandlerInstance) {
        throw new Error('Media handler is not initialized. Call setMediaHandlerInstance(...) after creating Quill.');
    }
    return __mediaHandlerInstance;
}


class ImageResizeModule {
    constructor(quill, options) {
        this.quill = quill;
        this.options = options;
        //this.registerImageResize();
    }

    resolveImageResize() {
        if (typeof window.ImageResize === 'function') return window.ImageResize;
        if (window.ImageResize && typeof window.ImageResize.default === 'function') return window.ImageResize.default;
        if (window.ImageResize && typeof window.ImageResize.ImageResize === 'function') return window.ImageResize.ImageResize;
        return null;
    }
}

const imageResizeModule = new ImageResizeModule();
export const ImageResize = imageResizeModule.resolveImageResize();

//////////// 클릭/ 빈 단락 삽입 모듈화 //////////////////////////////////////////////////////////////////////////////////////
class MediaGapHandler {
    constructor(quill, options = {}) {
        this.quill = quill;
        this.options = Object.assign({gapThreshold: 25}, options); //gapThreshold: 25, // 여백 감지 px 값
        this.container = quill.root;

        this.initEvents();
        this.observeMutations();
    }

    // 이벤트 초기화
    initEvents() {
        this.container.addEventListener("click", (e) => {
            const target = e.target;

            // 1. 미디어 직접 클릭 시 → 단락 생성하지 않음
            if (target.tagName === "IMG" || target.tagName === "IFRAME" || target.tagName === "VIDEO") {
                return;
            }

            const rect = this.container.getBoundingClientRect();
            const clickY = e.clientY - rect.top + this.container.scrollTop;
            const children = [...this.container.children];

            for (let i = 0; i < children.length; i++) {
                const node = children[i];
                const media = this.getMedia(node);

                if (media) {
                    const mediaRect = media.getBoundingClientRect();
                    const mediaTop = mediaRect.top - rect.top + this.container.scrollTop;
                    const mediaBottom = mediaRect.bottom - rect.top + this.container.scrollTop;

                    // ▷ 미디어 위쪽 여백
                    if (
                        clickY >= mediaTop - this.options.gapThreshold &&
                        clickY <= mediaTop
                    ) {
                        e.preventDefault();
                        e.stopPropagation();
                        this.insertParagraph(node, "before");
                        return;
                    }

                    // ▷ 미디어 사이 여백
                    const nextNode = children[i + 1];
                    const nextMedia = nextNode ? this.getMedia(nextNode) : null;
                    if (nextMedia) {

                        const nextRect = nextMedia.getBoundingClientRect();
                        const nextTop = nextRect.top - rect.top + this.container.scrollTop;

                        if (clickY > mediaBottom && clickY < nextTop) {
                            e.preventDefault();
                            e.stopPropagation();

                            // 중간에 빈 단락이 없는 경우에만 생성
                            if (
                                !node.nextElementSibling ||
                                node.nextElementSibling === nextNode
                            ) {
                                this.insertParagraph(node, "after");
                            }
                            return;
                        }
                    }
                }
            }
        });
    }

    // 미디어 요소(img, iframe, video) 탐색
    getMedia(node) {
        if (!node || node.nodeType !== 1) return null; // 요소 노드만
        if (node.matches("img, iframe, video")) return node; // node 자체가 미디어면 그대로 반환
        return node.querySelector("img, iframe, video"); // 아니면 자손에서 탐색
    }

    // MutationObserver: 미디어 삽입 감지
    observeMutations() {
        const observer = new MutationObserver((mutations) => {
            for (const mutation of mutations) {
                for (const node of mutation.addedNodes) {
                    if ((node.tagName === "P" && this.getMedia(node)) ||
                        (node.classList && node.classList.contains("ql-video"))
                    ) {// 미디어 삽입 시 → 아래에 빈 단락 추가
                        if (!node.nextElementSibling) {
                            const newPara = document.createElement("p");
                            newPara.innerHTML = "<br>";
                            node.parentNode.appendChild(newPara);
                            this.scrollToElement(newPara);
                        }
                    }
                }
            }
        });

        observer.observe(this.container, {childList: true});
    }

    // 단락 삽입 함수
    insertParagraph(refNode, position) {
        let newPara;

        if (position === "before") {
            if (
                !refNode.previousElementSibling ||
                refNode.previousElementSibling.innerText.trim() !== ""
            ) {
                newPara = document.createElement("p");
                newPara.innerHTML = "<br>";
                refNode.parentNode.insertBefore(newPara, refNode);
            }
        } else if (position === "after") {
            if (
                !refNode.nextElementSibling ||
                refNode.nextElementSibling.innerText.trim() === ""
            ) {
                newPara = document.createElement("p");
                newPara.innerHTML = "<br>";
                refNode.parentNode.insertBefore(newPara, refNode.nextSibling);
            }
        }

        if (newPara) {
            this.placeCursor(newPara);
        }
    }

    // 커서 위치 지정
    placeCursor(paragraph) {
        const range = document.createRange();
        const sel = window.getSelection();
        range.setStart(paragraph, 0);
        range.collapse(true);
        sel.removeAllRanges();
        sel.addRange(range);

        this.scrollToElement(paragraph);
    }

    // 커서가 보이도록 스크롤 이동
    scrollToElement(el) {
        setTimeout(() => {
            el.scrollIntoView({behavior: "smooth", block: "center"});
        }, 30);
    }
} ///클릭/ 빈 단락 삽입 모듈화 end //////////////////////////////////////////////////////////////////////////////////////////

////// 이미지 삽입 관련 시작 ////////////////////////////////////////////////////////////////////////////////////////////////
const headers = {};
const csrfToken = getCookie('csrf_token');
if (csrfToken) headers['X-CSRF-Token'] = csrfToken;
const EDITOR_IMAGE_UPLOAD_URL = '/apis/wysiwyg/article/image/upload';
const EDITOR_VIDEO_UPLOAD_URL = '/apis/wysiwyg/article/video/upload';

// javascript
export class QuillImageVideoHandler {
    /**
     * @param {Quill} quill
     * @param {{
     *   imageUploadUrl: string,
     *   videoUploadUrl: string,
     *   headers?: Record<string, string>,
     *   imageFieldName?: string,
     *   videoFieldName?: string,
     *   timeoutMs?: number
     * }} options
     */
    constructor(quill, options = {}) {
        this.quill = quill;
        this.mediaGapHandler = new MediaGapHandler(quill);

        this.config = {
            imageUploadUrl: options.imageUploadUrl,
            videoUploadUrl: options.videoUploadUrl,
            headers: options.headers, // 필요 없으면 undefined 그대로 두면 됩니다
            imageFieldName: options.imageFieldName || 'imagefile',
            videoFieldName: options.videoFieldName || 'videofile',
            timeoutMs: typeof options.timeoutMs === 'number' ? options.timeoutMs : 20000,
        };

        if (!this.config.imageUploadUrl || !this.config.videoUploadUrl) {
            throw new Error('QuillImageVideoHandler: imageUploadUrl과 videoUploadUrl은 필수입니다.');
        }
    }

    // 서버에 이미지 파일을 업로드하는 비동기 메서드
    async imageUploadToServer(file) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs);

        const formData = new FormData();
        formData.append(this.config.imageFieldName, file);

        const response = await fetch(this.config.imageUploadUrl, {
            method: 'POST',
            body: formData,
            headers: this.config.headers,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error('Upload failed: ' + response.status);
        }
        return response.json();
    }

    // 서버에 동영상 파일을 업로드하는 비동기 메서드
    async videoUploadToServer(file) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.config.timeoutMs);

        const formData = new FormData();
        formData.append(this.config.videoFieldName, file);

        const response = await fetch(this.config.videoUploadUrl, {
            method: 'POST',
            body: formData,
            headers: this.config.headers,
            signal: controller.signal,
        });

        clearTimeout(timeoutId);

        if (!response.ok) {
            throw new Error('Upload failed: ' + response.status);
        }
        return response.json();
    }

    // 이미지/비디오 업로드 후 에디터에 삽입
    async imageVideoInsertHandler(file, type) {
        if (file && typeof file.type === 'string' && file.type.startsWith('image/')) {
            try {
                const response = await this.imageUploadToServer(file);
                if (response && response.url) {
                    const range = this.quill.getSelection(true);
                    const insertIndex = (range && typeof range.index === 'number')
                        ? range.index
                        : this.quill.getLength();

                    this.quill.insertEmbed(insertIndex, type, response.url, 'user');

                    // 이미지 뒤에 빈 줄 추가 후 커서 이동
                    this.quill.insertText(insertIndex + 1, "\n", 'user');
                    const newCursorIndex = insertIndex + 2;
                    this.quill.setSelection(newCursorIndex, 0);

                    const [line] = this.quill.getLine(newCursorIndex);
                    const pTag = line && line.domNode && line.domNode.tagName
                        ? (line.domNode.tagName.toLowerCase() === 'p' ? line.domNode : null)
                        : null;

                    this.mediaGapHandler.placeCursor(pTag);
                } else {
                    alert('이미지 업로드 실패');
                }
            } catch (e) {
                alert(`이미지 업로드 오류: ${e.message || e}`);
            }
        } else {
            try {
                const response = await this.videoUploadToServer(file);
                if (response && response.url) {
                    const range = this.quill.getSelection(true) || { index: this.quill.getLength(), length: 0 };
                    const insertIndex = (range && typeof range.index === 'number')
                        ? range.index
                        : this.quill.getLength();

                    this.quill.insertEmbed(insertIndex, type, response.url, 'user');

                    // 동영상 뒤에 빈 줄 추가 후 커서 이동
                    this.quill.insertText(insertIndex + 1, "\n", 'user');
                    const newCursorIndex = insertIndex + 2;
                    this.quill.setSelection(newCursorIndex, 0, 'user');

                    const [line] = this.quill.getLine(newCursorIndex);
                    const pTag = line && line.domNode && line.domNode.tagName
                        ? (line.domNode.tagName.toLowerCase() === 'p' ? line.domNode : null)
                        : null;

                    this.mediaGapHandler.placeCursor(pTag);
                } else {
                    alert('동영상 업로드 실패');
                }
            } catch (e) {
                alert(`동영상 업로드 오류: ${e.message || e}`);
            }
        }
    }
}


//////////////////////* 툴바를 통해 이미지 삽입과 저장 후 src 받아오기 *//////////////////////////////////////////////////////////
// 이미지 삽입 로직을 처리하는 메인 로직
export function imageInsertByToolbarButton() {
    // 동기 컨텍스트에서 실행되어야 함 (async 금지)
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'image/*';
    input.style.display = 'none';

    const cleanup = () => {
        input.value = '';
        input.remove();
    };

    input.addEventListener('change', async () => {
        try {
            const file = input.files && input.files[0];
            if (!file) return;
            // 비동기 처리는 여기에서
            const handler = getMediaHandlerInstance();
            await handler.imageVideoInsertHandler(file, 'image');
        } finally {
            cleanup();
        }
    }, { once: true });

    // 일부 브라우저(iOS Safari 등) 호환을 위해 DOM에 붙인 뒤 클릭
    document.body.appendChild(input);
    input.click();

}

// 동영상 삽입 로직을 처리하는 메인 로직
export function videoInsertByToolbarButton() {
    // 동기 컨텍스트에서 실행되어야 함 (async 금지)
    const input = document.createElement('input');
    input.type = 'file';
    input.accept = 'video/*';
    input.style.display = 'none';

    const cleanup = () => {
        input.value = '';
        input.remove();
    };

    input.addEventListener('change', async () => {
        try {
            const file = input.files && input.files[0];
            if (!file) return;
            const handler = getMediaHandlerInstance();
            await handler.imageVideoInsertHandler(file, 'video');
        } finally {
            cleanup();
        }
    }, { once: true });

    document.body.appendChild(input);
    input.click();

}


/////////////// 캡쳐 붙여넣기, 드래그 드랍 삽입과 저장 후 src 받아오기 //////////////////////////////////////////////////////////////
//// 붙여넣기 (capture 단계에서 가로채기) — 화면 캡쳐 중복 삽입 방지 ////////////////////////////////////////////////////////////////
/**
 * Quill 붙여넣기 공통 처리기 등록
 *
 * - 텍스트: 평문으로 삽입
 * - 이미지: 클립보드의 image/* 파일을 콜백을 통해 비동기 삽입
 *
 * @param {object} quill                Quill 인스턴스
 * @param {object} options
 * @param {boolean} [options.pasteAsPlainText=true]  텍스트를 평문으로만 삽입
 * @param {(file: File, kind: 'image') => Promise<void>|void} options.insertImage
 *        이미지 파일을 실제로 에디터에 삽입하는 사용자 정의 콜백
 * @param {boolean} [options.capture=true]           캡처 단계에서 이벤트 가로채기
 * @returns {() => void}                             등록 해제 함수(remove listener)
 */
export async function registerQuillPasteHandler(
  quill,
  {
    pasteAsPlainText = true,
    insertImage,
    capture = true,
  } = {}
) {
  if (!quill || !quill.root) {
    throw new Error('에디터 생성이 필요합니다.');
  }

  const onPaste = (e) => {
    const clipboard = e.clipboardData || window.clipboardData;

    // 1) 클립보드 텍스트 평문 삽입
    if (pasteAsPlainText && clipboard && typeof clipboard.getData === 'function') {
      const text = clipboard.getData('text/plain') || '';
      if (text) {
        e.preventDefault();
        const range = quill.getSelection(true);
        const index = range ? range.index : quill.getLength();
        quill.insertText(index, text, 'user');
        quill.setSelection(index + text.length, 0, 'user');
      }
    }

    // 2) 클립보드 이미지 삽입
    const items = (clipboard && clipboard.items) || [];
    const imageFiles = [];
    for (let i = 0; i < items.length; i++) {
      const it = items[i];
      if (it && it.type && it.type.indexOf('image') === 0) {
        const f = typeof it.getAsFile === 'function' ? it.getAsFile() : null;
        if (f) imageFiles.push(f);
      }
    }

    if (imageFiles.length > 0 && typeof insertImage === 'function') {
      // Quill 기본 paste를 막고, 이미지 삽입만 수행
      e.preventDefault();
      if (typeof e.stopImmediatePropagation === 'function') {
        e.stopImmediatePropagation();
      }

      // 비동기 처리(IIFE)로 이벤트 루프 막지 않기
      (async () => {
        for (const file of imageFiles) {
          try {
            await insertImage(file, 'image');
          } catch (err) {
              // 필요 시 에러 로깅/알림 처리
              const msg = extractErrorMessage(err) || '게시글 저장에 실패했습니다.';
              if (errorTag) {
                  errorTag.style.display = 'block';
                  errorTag.innerText = msg;
                  console.error("1. catch article submit error", err);
              }
            console.error('Failed to insert pasted image:', err);
          }
        }
      })();
    }
  };

  quill.root.addEventListener('paste', onPaste, capture);

  // 등록 해제 함수 반환(중복 등록 방지용)
  return () => quill.root.removeEventListener('paste', onPaste, capture);
}

//// 드래그&드롭 처리 /////////////////////////////////////////////////////////////////////////////////////////////////////////////
// 드래그&드롭 공통 등록 유틸: 이미지 전용
export async function registerImageDrop({ container,
                                            dropArea = null,
                                            onDropFiles,
                                            fileFilter = (f) => f.type && f.type.startsWith('image/') }) {
    if (!container) return () => {};

    const showUI = () => { if (dropArea) dropArea.style.display = 'flex'; };
    const hideUI = () => { if (dropArea) dropArea.style.display = 'none'; };

    // dragenter/dragleave 버블링 보정용 카운터
    let dragCounter = 0;

    const onDragOver = (e) => {
        e.preventDefault();
        showUI();
    };

    const onDragEnter = () => {
        dragCounter += 1;
        showUI();
    };

    const onDragLeave = () => {
        dragCounter = Math.max(0, dragCounter - 1);
        if (dragCounter === 0) hideUI();
    };

    const onDrop = async (e) => {
        e.preventDefault();
        if (typeof e.stopImmediatePropagation === 'function') {
            e.stopImmediatePropagation();
        }
        dragCounter = 0;
        hideUI();

        const dt = e.dataTransfer;
        if (!dt) return;

        const files = Array.from(dt.files || []).filter(fileFilter);
        if (!files.length) return;

        if (typeof onDropFiles === 'function') {
            await onDropFiles(files, e);
        }
    };

    container.addEventListener('dragover', onDragOver);
    container.addEventListener('dragenter', onDragEnter);
    container.addEventListener('dragleave', onDragLeave);
    container.addEventListener('drop', onDrop);

    // 등록 해제 함수 반환
    return () => {
        container.removeEventListener('dragover', onDragOver);
        container.removeEventListener('dragenter', onDragEnter);
        container.removeEventListener('dragleave', onDragLeave);
        container.removeEventListener('drop', onDrop);
        hideUI();
    };
}

//// MutationObserver: 이미지 삭제 후보 추적: Undo ////////////////////////////////////////////////////////////////////////
// 안전 로거: Linter에서 'console is not defined' 경고 회피
const logger = (() => {
  const c =
    (typeof window !== 'undefined' && window.console) ||
    (typeof globalThis !== 'undefined' && globalThis.console) ||
    { log() {}, warn() {}, error() {} };
  return { log: c.log.bind(c), warn: c.warn.bind(c), error: c.error.bind(c) };
})();

function defaultGetCookie(name) {
  if (typeof document === 'undefined') return '';
  const m = document.cookie.match('(^|;)\\s*' + name + '\\s*=\\s*([^;]+)');
  return m ? decodeURIComponent(m.pop()) : '';
}

function collectImgSrcsFromNode(node) {
  const urls = [];
  if (node && node.nodeType === Node.ELEMENT_NODE) {
    const el = node;
    if (el.tagName && el.tagName.toUpperCase() === 'IMG') {
      const src = el.getAttribute('src');
      if (src) urls.push(src);
    }
    const imgs = el.querySelectorAll ? el.querySelectorAll('img') : [];
    for (const img of imgs) {
      const src = img.getAttribute('src');
      if (src) urls.push(src);
    }
  }
  return urls;
}

/**
 * 이미지 삭제 후보 추적용 옵저버 생성
 * options:
 * - onMark(urls: string[]): 직접 처리 콜백(선택)
 * - onUnmark(urls: string[]): 직접 처리 콜백(선택)
 * - markUrl: string (onMark 미사용 시 POST 전송)
 * - unmarkUrl: string (onUnmark 미사용 시 POST 전송)
 * - getCsrfToken: () => string | Promise<string> (선택)
 * - fetchImpl: fetch 대체(선택)
 * - headers: 추가 헤더(선택)
 */
export function createImageUploadObserver(options = {}) {
  const {
    onMark,
    onUnmark,
    markUrl,
    unmarkUrl,
    getCsrfToken = () => defaultGetCookie('csrf_token'),
    fetchImpl = (typeof fetch !== 'undefined' ? fetch.bind(globalThis) : null),
    headers = {}
  } = options;

  const removedImageUrls = new Set();

  const imageUploadObserver = new MutationObserver((mutations) => {
    const toMark = new Set();
    const toUnmark = new Set();

    for (const m of mutations) {
      if (m.type === 'childList') {
        for (const node of m.removedNodes) {
          for (const url of collectImgSrcsFromNode(node)) {
            removedImageUrls.add(url);
            toMark.add(url);
          }
        }
        for (const node of m.addedNodes) {
          for (const url of collectImgSrcsFromNode(node)) {
            if (removedImageUrls.has(url)) {
              removedImageUrls.delete(url);
              toUnmark.add(url);
            }
          }
        }
      } else if (m.type === 'attributes' && m.attributeName === 'src') {
        const el = m.target;
        if (el && el.tagName && el.tagName.toUpperCase() === 'IMG') {
          const oldUrl = m.oldValue || null;
          const newUrl = el.getAttribute('src') || null;
          if (oldUrl && oldUrl !== newUrl) {
            removedImageUrls.add(oldUrl);
            toMark.add(oldUrl);
          }
          if (newUrl && removedImageUrls.has(newUrl)) {
            removedImageUrls.delete(newUrl);
            toUnmark.add(newUrl);
          }
        }
      }
    }

    const marks = Array.from(toMark);
    const unmarks = Array.from(toUnmark);
    if (marks.length === 0 && unmarks.length === 0) return;

    (async () => {
      try {
        if (marks.length > 0) {
          if (typeof onMark === 'function') {
            await onMark(marks);
          } else if (markUrl && fetchImpl) {
            const csrf = await getCsrfToken();
            await fetchImpl(markUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(csrf ? {'X-CSRF-Token': csrf} : {}),
                ...headers
              },
              body: JSON.stringify(marks)
            });
          }
        }

        if (unmarks.length > 0) {
          if (typeof onUnmark === 'function') {
            await onUnmark(unmarks);
          } else if (unmarkUrl && fetchImpl) {
            const csrf = await getCsrfToken();
            await fetchImpl(unmarkUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(csrf ? {'X-CSRF-Token': csrf} : {}),
                ...headers
              },
              body: JSON.stringify(unmarks)
            });
          }
        }
      } catch (err) {
        logger.error('Image mark/unmark failed:', err);
      }
    })();
  });

  return {
    start(editorElement) {
      if (!editorElement) {
        logger.warn('[imageObserver] editorElement not found.');
        return;
      }
      imageUploadObserver.observe(editorElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['src'],
        attributeOldValue: true
      });
    },
    stop() {
      imageUploadObserver.disconnect();
    },
    disconnect() {
      imageUploadObserver.disconnect();
    }
  };
}

// 간편 사용: 즉시 시작하고 핸들 반환
export function startImageUploadObserver(editorElement, options) {
  const inst = createImageUploadObserver(options);
  inst.start(editorElement);
  return inst;
}


//// MutationObserver: 동영상 삭제 후보 추적: Undo ////////////////////////////////////////////////////////////////////////
function collectVideoSrcsFromNode(node) {
  const urls = new Set();
  if (!(node instanceof Element)) return [];

  const push = (u) => {
    if (typeof u === 'string' && u.trim().length > 0) urls.add(u);
  };

  // 전달된 노드가 IFRAME일 수도 있음
  if (node.tagName && node.tagName.toUpperCase() === 'IFRAME') {
    push(node.getAttribute('src'));
    node.querySelectorAll('source[src]').forEach(s => push(s.getAttribute('src')));
  }

  // 하위 VIDEO 및 SOURCE 스캔
  node.querySelectorAll('video[src]').forEach(v => push(v.getAttribute('src')));
  node.querySelectorAll('video source[src]').forEach(s => push(s.getAttribute('src')));
  return Array.from(urls);
}

/**
 * 비디오 삭제 후보 추적용 옵저버 생성
 * options:
 * - onMark(urls: string[]): 직접 처리 콜백(선택)
 * - onUnmark(urls: string[]): 직접 처리 콜백(선택)
 * - markUrl: string (onMark 미사용 시 POST 전송)
 * - unmarkUrl: string (onUnmark 미사용 시 POST 전송)
 * - getCsrfToken: () => string | Promise<string> (선택)
 * - fetchImpl: fetch 대체(선택)
 * - headers: 추가 헤더(선택)
 */
export function createVideoUploadObserver(options = {}) {
  const {
    onMark,
    onUnmark,
    markUrl,
    unmarkUrl,
    getCsrfToken = () => defaultGetCookie('csrf_token'),
    fetchImpl = (typeof fetch !== 'undefined' ? fetch.bind(globalThis) : null),
    headers = {}
  } = options;

  const removedVideoUrls = new Set();

  const videoUploadObserver = new MutationObserver((mutations) => {
    const toMark = new Set();
    const toUnmark = new Set();

    for (const m of mutations) {
      if (m.type === 'childList') {
        for (const node of m.removedNodes) {
          for (const url of collectVideoSrcsFromNode(node)) {
            removedVideoUrls.add(url);
            toMark.add(url);
          }
        }
        for (const node of m.addedNodes) {
          for (const url of collectVideoSrcsFromNode(node)) {
            if (removedVideoUrls.has(url)) {
              removedVideoUrls.delete(url);
              toUnmark.add(url);
            }
          }
        }
      } else if (m.type === 'attributes' && m.attributeName === 'src') {
        const el = m.target;
        const tag = el && el.tagName ? el.tagName.toUpperCase() : '';
        if (tag === 'VIDEO' || tag === 'SOURCE') {
          const oldUrl = m.oldValue || null;
          const newUrl = el.getAttribute('src') || null;
          if (oldUrl && oldUrl !== newUrl) {
            removedVideoUrls.add(oldUrl);
            toMark.add(oldUrl);
          }
          if (newUrl && removedVideoUrls.has(newUrl)) {
            removedVideoUrls.delete(newUrl);
            toUnmark.add(newUrl);
          }
        }
      }
    }

    const marks = Array.from(toMark);
    const unmarks = Array.from(toUnmark);
    if (marks.length === 0 && unmarks.length === 0) return;

    (async () => {
      try {
        if (marks.length > 0) {
          if (typeof onMark === 'function') {
            await onMark(marks);
          } else if (markUrl && fetchImpl) {
            const csrf = await getCsrfToken();
            await fetchImpl(markUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(csrf ? {'X-CSRF-Token': csrf} : {}),
                ...headers
              },
              body: JSON.stringify(marks)
            });
          }
        }

        if (unmarks.length > 0) {
          if (typeof onUnmark === 'function') {
            await onUnmark(unmarks);
          } else if (unmarkUrl && fetchImpl) {
            const csrf = await getCsrfToken();
            await fetchImpl(unmarkUrl, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
                ...(csrf ? {'X-CSRF-Token': csrf} : {}),
                ...headers
              },
              body: JSON.stringify(unmarks)
            });
          }
        }
      } catch (err) {
        logger.error('Video mark/unmark failed:', err);
      }
    })();
  });

  return {
    start(editorElement) {
      if (!editorElement) {
        logger.warn('[videoObserver] editorElement not found.');
        return;
      }
      videoUploadObserver.observe(editorElement, {
        childList: true,
        subtree: true,
        attributes: true,
        attributeFilter: ['src'],
        attributeOldValue: true
      });
    },
    stop() {
      videoUploadObserver.disconnect();
    },
    disconnect() {
      videoUploadObserver.disconnect();
    }
  };
}

// 간편 사용: 즉시 시작하고 핸들 반환
export function startVideoUploadObserver(editorElement, options) {
  const inst = createVideoUploadObserver(options);
  inst.start(editorElement);
  return inst;
}










