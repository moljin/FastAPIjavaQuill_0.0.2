import {extractErrorMessage, getCookie, getTagById} from "../../../statics/js/fastapiClient.js";
import {commentCreateFormAttach, editorWorkManager, formEditorDetach, openedFormRemove, updateFormAttach} from "./commentUtils.js";

document.addEventListener('DOMContentLoaded', async () => {
    const articleIDTag = getTagById("article_id");

    /////// commentCreate용 editor 붙이기 //////////////////////////////////////////////
    const commentBTN = getTagById("commentBTN");
    const commentContainer = getTagById("commentContainer");

    commentBTN.addEventListener("click", async () => {
        /////// comment용 editor 붙이기 /////////////////////////////////////////////////////
        openedFormRemove();
        commentCreateFormAttach(commentContainer, commentBTN);

        /////// 붙은 comment용 editor로 작업하기 //////////////////////////////////////////////
        const datas = {
            editorElement: document.getElementById('comment-editor'),
            objectID: null,
            OBJECT_CONTENT: window.COMMENT_CONTENT, //editor 안의 content, 생성시는 undefined
            markID: getTagById("commentMarkID")?.value,
            imageUploadUrl: '/apis/wysiwyg/article/comment/image/upload',
            videoUploadUrl: '/apis/wysiwyg/article/comment/video/upload',
            objectQuillContainer: getTagById('editor-container'),
            objectDropArea: getTagById("drop-area"),
            errorTag: getTagById("errorTag"),
            objectFormElement: document.getElementById("commentForm"),
            commentID: null,
            pairedCommentID: null // 답글 대상의 코멘트 ID

        };
        await editorWorkManager(datas);

        /////// 붙었던 comment용 editor 작성 취소하기 ///////////////////////////////////////
        const cancelBTN = getTagById("cancelBTN");
        cancelBTN.addEventListener("click", () => {
            formEditorDetach("commentForm", commentBTN, cancelBTN);
        });

    });


    /////// commentUpdate 로직 //////////////////////////////////////////////
    const commentBoxContainerAll = document.querySelectorAll(".comment-box-container");
    commentBoxContainerAll.forEach(function (commentBoxContainer) {
        let commentBox = commentBoxContainer.querySelector(".comment-box");
        let updateContainer = commentBoxContainer.querySelector(".updateReplyContainer");
        let commentUpdateBTN = commentBoxContainer.querySelector(".commentUpdateBTN");
        let commentID;
        if (commentUpdateBTN) commentID = commentUpdateBTN.getAttribute("data-comment-id");
        let commentContent;
        if (commentUpdateBTN) commentContent = commentUpdateBTN.getAttribute("data-comment-content");

        /////// commentUpdate용 editor 붙이기 /////////////////////////////////////////////////////
        let updateHTML = ``;
        if (commentUpdateBTN) {
            commentUpdateBTN.addEventListener("click", async () => {
                openedFormRemove();
                updateFormAttach(updateContainer, commentBox, commentUpdateBTN);

                /////// 붙은 commentUpdate용 editor로 작업하기 //////////////////////////////////////////////
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
                    pairedCommentID: null // 답글 대상의 코멘트 ID

                };
                await editorWorkManager(datas);

                /////// 붙었던 comment용 editor 작성 취소하기 ///////////////////////////////////////////////
                const cancelBTN = getTagById("cancelBTN");
                cancelBTN.addEventListener("click", () => {
                    formEditorDetach("updateForm", commentUpdateBTN, cancelBTN, commentBox);
                });

            });
        }


    });


});
