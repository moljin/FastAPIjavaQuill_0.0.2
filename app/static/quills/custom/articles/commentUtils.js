import {UTCtoKST} from '../../../statics/js/utils.js';
import quillClient from '../quillClient.js';
import {baseToolbar, QuillCustomizer} from '../baseSettings.js';
import {commentSubmit} from "../quillAPI.js";
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
import {MinimalCustomizer, minimalToolbar} from "../minimalSettings.js";


export function commentCreateFormAttach(commentContainer, commentBTN) {
    const commentCreateFormHTML = `<form id="commentForm" enctype="multipart/form-data">
                                                <div class="uk-margin" id="errorTag"><!--js에서 넘어온 오류 메시지를 넣는다.--></div>
                                                <div id="editor-container">
                                                    <div id="drop-area"></div>
                                                    <div id="comment-editor"></div>                                
                                                </div>
                                                
                                                <div class="cancel-submit">
                                                    <div class="cancel" id="cancelBTN">작성취소</div>
                                                    <button class="submit">글 올리기</button>
                                                </div>
                                            </form>`;
    commentContainer.insertAdjacentHTML('afterbegin', commentCreateFormHTML);
    commentBTN.style.display = "none";
}

export function replyCreateFormAttach(replyContainer, replyBTN) {
    const commentReplyFormHTML = `<form id="replyForm" enctype="multipart/form-data">
                                            <div class="uk-margin" id="errorTag"><!--js에서 넘어온 오류 메시지를 넣는다.--></div>
                                            <div id="editor-container">
                                                <div id="drop-area"></div>
                                                <div id="reply-editor"></div>
                                            </div>
                            
                                            <div class="cancel-submit">
                                                <div class="cancel" id="cancelBTN">작성취소</div>
                                                <button class="submit">글 올리기</button>
                                            </div>
                                        </form>`;
    replyContainer.insertAdjacentHTML('afterbegin', commentReplyFormHTML);
    replyBTN.style.display = "none";
}

export function updateFormAttach(updateContainer, Box, updateBTN) {
    /*comment update와 reply update를 위한 공통 함수 (Box: .comment-box or .reply-box*/
    const updateFormHTML = `<form id="updateForm" enctype="multipart/form-data">
                                        <div class="uk-margin" id="errorTag"><!--js에서 넘어온 오류 메시지를 넣는다.--></div>
                                        <div id="editor-container">
                                            <div id="drop-area"></div>
                                            <div id="update-editor"></div>
                                        </div>
                        
                                        <div class="cancel-submit">
                                            <div class="cancel" id="cancelBTN">작성취소</div>
                                            <button class="submit">글 올리기</button>
                                        </div>
                                    </form>`;
    updateContainer.insertAdjacentHTML('afterbegin', updateFormHTML);
    Box.style.display = "none";
    updateBTN.style.display = "none";
}

export function openedFormRemove() {
    const commentBoxContainerAll = document.querySelectorAll(".comment-box-container");
    const replyBoxContainerAll = document.querySelectorAll(".reply-box-container");
    const hasReplies = replyBoxContainerAll.length > 0;

    commentBoxContainerAll.forEach(commentBoxContainer => {
        const commentBox = commentBoxContainer.querySelector(".comment-box");
        const commentBTN = document.getElementById("commentBTN");
        // 코멘트(댓글)만 있는 경우
        if (commentBox) {
            if (commentBox.style.display === "none") {
                commentBox.style.display = "block";
                commentBox.querySelector(".commentUpdateBTN").style.display = "block";
                commentBox.querySelector(".replyBTN").style.display = "block";
            } else {
                if (commentBox.querySelector(".replyBTN")) {
                    commentBox.querySelector(".replyBTN").style.display = "block";
                }

            }
        }
        if (commentBTN.style.display === "none") commentBTN.style.display = "block";

        const openedCommentForm = document.getElementById("commentForm");
        if (openedCommentForm) openedCommentForm.remove();
        const openedUpdateForm = document.getElementById("updateForm");
        if (openedUpdateForm) openedUpdateForm.remove();
        const openedReplyForm = document.getElementById("replyForm");
        if (openedReplyForm) openedReplyForm.remove();

        if (hasReplies) { //코멘트(댓글)와 그 답글(대댓글)이 있는 경우
            replyBoxContainerAll.forEach(replyBoxContainer => {
                const replyBox = replyBoxContainer.querySelector(".reply-box");
                const replyUpdateContainer = replyBoxContainer.querySelector(".replyUpdateContainer");
                const replyUpdateBTN = replyBoxContainer.querySelector(".replyUpdateBTN");

                if (commentBox.style.display === "none") commentBox.style.display = "block";
                if (replyBox.style.display === "none") replyBox.style.display = "block";
                if (replyUpdateContainer) {
                    if (replyUpdateContainer.style.display === "block") replyUpdateContainer.style.display = "none";
                }

                if (replyUpdateBTN && replyUpdateBTN.style.display === "none") replyUpdateBTN.style.display = "block";

                const openedCommentForm = document.getElementById("commentForm");
                if (openedCommentForm) openedCommentForm.remove();
                const openedUpdateForm = document.getElementById("updateForm");
                if (openedUpdateForm) openedUpdateForm.remove();
                const openedReplyForm = document.getElementById("replyForm");
                if (openedReplyForm) openedReplyForm.remove();

            });
        } else {
            // 대댓글이 하나도 없을 때에도 실행하고 싶은 로직
        }
    });




}

export function newCommentObjectHTML(data) {
    return `<div class="comment-box-container" data-comment-id="${data.id}">
                <div class="comment-box">                            
                    <div class="commentUpdateBTN-container"><div class="commentUpdateBTN" data-comment-id="${data.id}" data-comment-content="${data.content}">수정하기</div></div>
                    
                    <div>paired_comment_id: ${data.paired_comment_id}</div>
                    <div>id: ${data.id}</div>
                    <div class="content">${data.content}</div>
                    <div>${data.author.username}</div>
                    <div>${UTCtoKST(data.created_at)}</div>
                    <div class="replyBTN-container"><div class="replyBTN" data-comment-id="${data.id}">답글 달기</div></div>
                </div>
                <div class="updateReplyContainer mt-10">
                    <!--js를 이용해 동적으로 답글용 commentUpdate 및 Reply editor를 붙인다.-->
                </div>
            </div>`;
}

export function newReplyObjectHTML(data, pairedCommentID = null) {
    return `<div class="reply-box-container" data-comment-id="${data.id}">
                <div class="reply-box">                            
                    <div class="replyUpdateBTN-container"><div class="replyUpdateBTN" data-comment-id="${data.id}" data-comment-content="${data.content}">수정하기</div></div>
                    
                    <div>paired_comment_id: ${pairedCommentID}</div>
                    <div>id: ${data.id}</div>
                    <div class="content">${data.content}</div>
                    <div>${data.author.username}</div>
                    <div>${UTCtoKST(data.created_at)}</div>
                </div>
                <div class="replyUpdateContainer mt-10">
                    <!--js를 이용해 동적으로 답글용 commentUpdate 및 Reply editor를 붙인다.-->
                </div>
            </div>`;
}

export function formEditorDetach(formId, objectBTN, cancelBTN, objectBox = null) {
    const ok = confirm('작성취소하면, 작성중이던 내용이 저장되지 않습니다.');
    if (!ok) return;
    const formEditorElement = getTagById(formId);
    console.log("formEditorElement: ", formEditorElement);
    formEditorElement.remove();

    objectBTN.style.display = "block";
    cancelBTN.remove();
    if (objectBox) objectBox.style.display = "block";
}


export async function editorWorkManager(datas) {
    /////// 붙은 comment용 editor로 작업하기 //////////////////////////////////////////////
    const editorElement = datas.editorElement;
    const objectID = datas.objectID;
    const OBJECT_CONTENT = datas.OBJECT_CONTENT;
    const markID = datas.markID;
    const imageUploadUrl = datas.imageUploadUrl;
    const videoUploadUrl = datas.videoUploadUrl;
    const objectQuillContainer = datas.objectQuillContainer;
    const objectDropArea = datas.objectDropArea;
    const errorTag = datas.errorTag;
    const objectFormElement = datas.objectFormElement;
    const commentID = datas.commentID;
    const pairedCommentID = datas.pairedCommentID;
    console.log("editorWorkManager datas: ", datas);

    let objectQuill = null;
    if (editorElement && !objectID) { // 게시글 쓰기(create)
        // objectQuill = quillClient(editorElement, baseToolbar, QuillCustomizer);
        objectQuill = quillClient(editorElement, minimalToolbar, MinimalCustomizer);
    } else if (editorElement && objectID) { // 게시글 수정(update)
        // objectQuill = quillClient(editorElement, baseToolbar, QuillCustomizer, objectID, OBJECT_CONTENT);
        objectQuill = quillClient(editorElement, minimalToolbar, MinimalCustomizer, objectID, OBJECT_CONTENT);
    }

    const imageObs = startImageUploadObserver(editorElement, {
        markUrl: `/apis/wysiwyg/mark_delete_images/${markID}`,
        unmarkUrl: `/apis/wysiwyg/unmark_delete_images/${markID}`,
        getCsrfToken: () => getCookie('csrf_token') // 프로젝트 유틸 사용 가능
    });

    const videoObs = startVideoUploadObserver(editorElement, {
        markUrl: `/apis/wysiwyg/mark_delete_videos/${markID}`,
        unmarkUrl: `/apis/wysiwyg/unmark_delete_videos/${markID}`,
        getCsrfToken: () => getCookie('csrf_token')
    });

    // 필요 시 중단
    // imageObs.stop();
    // videoObs.stop();

    const objectQuillMediaHandler = new QuillImageVideoHandler(objectQuill, {
        imageUploadUrl: imageUploadUrl,
        videoUploadUrl: videoUploadUrl,
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
    setMediaHandlerInstance(objectQuillMediaHandler);

    // 켑쳐 and paste
    let objectUnregisterPaste = null;
    if (objectQuillContainer) {
        objectUnregisterPaste = await registerQuillPasteHandler(objectQuill, {
            pasteAsPlainText: true,
            insertImage: async (file) => {
                const handler = getMediaHandlerInstance();
                await handler.imageVideoInsertHandler(file, 'image');
            },
            capture: true, // Quill 기본 paste보다 먼저 가로채기
        });
    }
    // 드래그 & 드랍
    let objectUnregisterImageDnd = null;
    if (objectQuillContainer) {
        objectUnregisterImageDnd = registerImageDrop({
            container: objectQuillContainer,
            objectDropArea,
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
        if (objectUnregisterPaste) objectUnregisterPaste();
        if (objectUnregisterImageDnd) objectUnregisterImageDnd();
    });

    let error = null;
    if (!objectFormElement) return;
    objectFormElement.addEventListener("submit", async (ev) => {
        ev.preventDefault();
        if (!objectQuill) {
            console.error("에디터가 초기화되지 않았습니다.");
            return;
        }

        if (objectFormElement.dataset.submitting === "1") return;
        objectFormElement.dataset.submitting = "1";
        if (errorTag) errorTag.textContent = "";

        try {
            const hasText = objectQuill.getText().trim().length > 0;
            const hasImage = !!objectQuill.root.querySelector("img");
            if (!hasText && !hasImage) throw new Error("본문을 입력해 주세요.");
            //const hasVideo = !!articleQuill.root.querySelector("video");
            //if (!hasText && !hasImage && !hasVideo) throw new Error("본문을 입력해 주세요.");
            let params;
            if (commentID && !pairedCommentID) { //코멘트 업데이트
                params = {
                    comment_id: commentID,
                    content: objectQuill.root.innerHTML.trim() || '',
                };
            } else if (!commentID && pairedCommentID) { // reply(답글) 생성
                params = {
                    paired_comment_id: pairedCommentID,
                    content: objectQuill.root.innerHTML.trim() || '',
                };
            } else if (commentID && pairedCommentID) { //reply(답글) 업데이트
                params = {
                    comment_id: commentID,
                    paired_comment_id: pairedCommentID,
                    content: objectQuill.root.innerHTML.trim() || '',
                };
            } else { //코멘트 생성
                params = {
                    content: objectQuill.root.innerHTML.trim() || '',
                };
            }
            await commentSubmit(ev, {
                params, setError: (v) => (error = v)
            });

        } catch (e) {
            const msg = extractErrorMessage(e) || '저장 중에 오류가 발생했습니다.';

            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
            }
        } finally {
            objectFormElement.dataset.submitting = "0";
        }
    });
}