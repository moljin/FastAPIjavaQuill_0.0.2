import {extractErrorMessage, getCookie, getTagById} from "../../../statics/js/fastapiClient.js";
import {replyCreateFormAttach, editorWorkManager, formEditorDetach, updateFormAttach, openedFormRemove} from "./commentUtils.js";

document.addEventListener('DOMContentLoaded', async () => {
    const articleIDTag = getTagById("article_id");

    /////// reply 달기용 editor 붙이기 /////////////////////////////////////////////////////
    const commentBoxContainerAll = document.querySelectorAll(".comment-box-container");
    commentBoxContainerAll.forEach(function (commentBoxContainer) {
        let replyContainer = commentBoxContainer.querySelector(".updateReplyContainer");
        let replyBTN = commentBoxContainer.querySelector(".replyBTN");
        let commentID;
        if (replyBTN) {
            commentID = replyBTN.getAttribute("data-comment-id");
        }

        if (replyBTN) {
            replyBTN.addEventListener("click", async () => {
            /////// reply용 editor 붙이기 /////////////////////////////////////////////////////
            openedFormRemove();
            replyContainer.style.display = "block";
            replyCreateFormAttach(replyContainer, replyBTN);

            /////// 붙은 reply용 editor로 작업하기 //////////////////////////////////////////////
            const datas = {
                editorElement: document.getElementById('reply-editor'),
                objectID: null,
                OBJECT_CONTENT: window.COMMENT_CONTENT, //editor 안의 content, 생성시는 undefined
                markID: getTagById("commentMarkID")?.value,
                imageUploadUrl: '/apis/wysiwyg/article/comment/image/upload',
                videoUploadUrl: '/apis/wysiwyg/article/comment/video/upload',
                objectQuillContainer: getTagById('editor-container'),
                objectDropArea: getTagById("drop-area"),
                errorTag: getTagById("errorTag"),
                objectFormElement: document.getElementById("replyForm"),
                commentID: null,
                pairedCommentID: commentID // 답글 대상의 코멘트 ID

            };
            await editorWorkManager(datas);

            /////// 붙었던 comment용 editor 작성 취소하기 ///////////////////////////////////////
            const cancelBTN = getTagById("cancelBTN");
            cancelBTN.addEventListener("click", () => {
                formEditorDetach("replyForm", replyBTN, cancelBTN);
            });


        });
        }

    });


    /////// replyUpdate용 로직 /////////////////////////////////////////////////////
    const replyBoxContainerAll = document.querySelectorAll(".reply-box-container");
    replyBoxContainerAll.forEach(function (replyBoxContainer) {
        let replyBox = replyBoxContainer.querySelector(".reply-box");
        let updateContainer = replyBoxContainer.querySelector(".replyUpdateContainer");
        let replyUpdateBTN = replyBoxContainer.querySelector(".replyUpdateBTN");
        let commentID;
        if (replyUpdateBTN) commentID = replyUpdateBTN.getAttribute("data-comment-id");
        let pairedCommentID;
        if (replyUpdateBTN) pairedCommentID = replyUpdateBTN.getAttribute("data-paired_comment-id");
        let commentContent;
        if (replyUpdateBTN) commentContent = replyUpdateBTN.getAttribute("data-comment-content");

        /////// replyCommentUpdate용 editor 붙이기 /////////////////////////////////////////////////////
        if (replyUpdateBTN) {
            replyUpdateBTN.addEventListener("click", async () => {
                openedFormRemove();
                // .reply-box-container가 우측으로 붙이느라 display: flex; justify-content: right 해놨고,
                // .replyUpdateContainer(updateContainer)가 기본 display:none으로 되어있기 때문에...
                updateContainer.style.display = "block";
                updateFormAttach(updateContainer, replyBox, replyUpdateBTN);

                /////// 붙은 replyCommentUpdate용 editor로 작업하기 //////////////////////////////////////////////
                const datas = {
                    editorElement: document.getElementById('update-editor'),
                    objectID: commentID,
                    OBJECT_CONTENT: commentContent, //editor 안의 content
                    markID: getTagById("commentMarkID")?.value,
                    imageUploadUrl: '/apis/wysiwyg/article/comment/image/upload',
                    videoUploadUrl: '/apis/wysiwyg/article/comment/video/upload',
                    objectQuillContainer: getTagById('editor-container'),
                    objectDropArea: getTagById("drop-area"),
                    errorTag: getTagById("errorTag"),
                    objectFormElement: document.getElementById("updateForm"),
                    commentID: commentID,
                    pairedCommentID: pairedCommentID // 답글 대상의 코멘트 ID
                };
                await editorWorkManager(datas);

                /////// 붙었던 replyCommentUpdate용 editor 작성 취소하기 ///////////////////////////////////////////////
                const cancelBTN = getTagById("cancelBTN");
                cancelBTN.addEventListener("click", () => {
                    updateContainer.style.display = "none";
                    formEditorDetach("updateForm", replyUpdateBTN, cancelBTN, replyBox);

                });


            });
        }


    });

});
