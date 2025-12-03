import quillClient from '../quillClient.js';
import {baseToolbar, QuillCustomizer} from '../baseSettings.js';
import {articleSubmit} from "../quillAPI.js";
import {extractErrorMessage, getCookie, getTagById} from "../../../statics/js/fastapiClient.js";
import {
    getMediaHandlerInstance,
    QuillImageVideoHandler,
    registerImageDrop,
    registerQuillPasteHandler,
    setMediaHandlerInstance,
    startImageUploadObserver,
    startVideoUploadObserver
} from "../mediaHandler.js";

document.addEventListener('DOMContentLoaded', async () => {
    const articleEditor = document.getElementById('article-editor');
    const articleIDTag = getTagById("article_id");
    const ARTICLE_CONTENT = (typeof window !== 'undefined' && window.ARTICLE_CONTENT) ? window.ARTICLE_CONTENT : '';

    let articleQuill = null;
    if (articleEditor && !articleIDTag) { // 게시글 쓰기(create)
        articleQuill = quillClient(articleEditor, baseToolbar, QuillCustomizer);
    } else if (articleEditor && articleIDTag) { // 게시글 수정(update)
        articleQuill = quillClient(articleEditor, baseToolbar, QuillCustomizer, articleIDTag.value, ARTICLE_CONTENT);
    }

    const markID = getTagById("markID")?.value;

    const imageObs = startImageUploadObserver(articleEditor, {
        markUrl: `/apis/wysiwyg/mark_delete_images/${markID}`,
        unmarkUrl: `/apis/wysiwyg/unmark_delete_images/${markID}`,
        getCsrfToken: () => getCookie('csrf_token') // 프로젝트 유틸 사용 가능
    });

    const videoObs = startVideoUploadObserver(articleEditor, {
        markUrl: `/apis/wysiwyg/mark_delete_videos/${markID}`,
        unmarkUrl: `/apis/wysiwyg/unmark_delete_videos/${markID}`,
        getCsrfToken: () => getCookie('csrf_token')
    });

    // 필요 시 중단
    // imageObs.stop();
    // videoObs.stop();

    const articleQuillMediaHandler = new QuillImageVideoHandler(articleQuill, {
        imageUploadUrl: '/apis/wysiwyg/article/image/upload',
        videoUploadUrl: '/apis/wysiwyg/article/video/upload',
        headers: {
            // 필요한 경우 예: 인증/보안 헤더
            'X-CSRF-Token': getCookie('csrf_token'),
        },
        // 옵션(기본값: imagefile, videofile)
        imageFieldName: 'imagefile',
        videoFieldName: 'videofile',
        // 옵션(기본값: 20000ms)
        timeoutMs: 20000,
    });
    setMediaHandlerInstance(articleQuillMediaHandler);


    const articleQuillContainer = getTagById('editor-container');
    const articleDropArea = getTagById("drop-area");
    // 켑쳐 and paste
    let articleUnregisterPaste = null;
    if (articleQuillContainer) {
        articleUnregisterPaste = await registerQuillPasteHandler(articleQuill, {
            pasteAsPlainText: true,
            insertImage: async (file) => {
                const handler = getMediaHandlerInstance();
                await handler.imageVideoInsertHandler(file, 'image');
            },
            capture: true, // Quill 기본 paste보다 먼저 가로채기
        });
    }
    // 드래그 & 드랍
    let articleUnregisterImageDnd = null;
    if (articleQuillContainer) {
        articleUnregisterImageDnd = registerImageDrop({
            container: articleQuillContainer,
            articleDropArea,
            onDropFiles: async (files) => {
                for (const file of files) {
                    const handler = getMediaHandlerInstance();
                    await handler.imageVideoInsertHandler(file, 'image');
                }
            },
            // 필요 시 파일 필터를 커스터마이징할 수 있습니다.
            // fileFilter: (f) => f.type === 'image/png' || f.type === 'image/jpeg',
        });
    }

    // 필요 시 페이지 이탈/언마운트 시 해제
    window.addEventListener('beforeunload', () => {
        if (articleUnregisterPaste) articleUnregisterPaste();
        if (articleUnregisterImageDnd) articleUnregisterImageDnd();
    });

    const errorTag = getTagById("errorTag");
    let error = null;

    const articleFormElement = document.getElementById("articleForm");
    if (!articleFormElement) return;
    articleFormElement.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        if (!articleQuill) {
            console.error("에디터가 초기화되지 않았습니다.");
            return;
        }

        if (articleFormElement.dataset.submitting === "1") return;
        articleFormElement.dataset.submitting = "1";
        if (errorTag) errorTag.textContent = "";

        try {
            const hasText = articleQuill.getText().trim().length > 0;
            const hasImage = !!articleQuill.root.querySelector("img");
            if (!hasText && !hasImage) throw new Error("본문을 입력해 주세요.");
            //const hasVideo = !!articleQuill.root.querySelector("video");
            //if (!hasText && !hasImage && !hasVideo) throw new Error("본문을 입력해 주세요.");

            const fileInput = articleFormElement.elements['imagefile'];
            const hasFile = fileInput && fileInput.files && fileInput.files.length > 0;
            const fd = new FormData(articleFormElement);

            fd.append('title', articleFormElement.elements['title']?.value || '');
            if (hasFile && fileInput.files[0] && fileInput.files[0].name) {
                fd.append('imagefile', fileInput.files[0]);
            }
            if (fd.has("content")) fd.delete("content");
            fd.append("content", articleQuill.root.innerHTML.trim());

            let params = fd; // fastapiClient가 FormData면 body로 전송
            await articleSubmit(ev, {
                params, setError: (v) => (error = v)
            });

        } catch (e) {
            const msg = extractErrorMessage(e) || '저장 중에 오류가 발생했습니다.';

            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
            }
        } finally {
            articleFormElement.dataset.submitting = "0";
        }
    });

    const cancelBTN = getTagById("cancelBTN");
    cancelBTN.addEventListener("click", () => {
        const ok = confirm('작성취소하면, 작성중이던 내용이 저장되지 않습니다.');
        if (!ok) return;
        window.location.href = "/views/articles/all";
    });

    // 다른 quill form이 있으면 quill 붙일 div의 id name으로 Quill 생성하여, submit 가능하다.
    // 예를 들어 article에 대한 reply와 그 reply에 대한 답변 등등


});
