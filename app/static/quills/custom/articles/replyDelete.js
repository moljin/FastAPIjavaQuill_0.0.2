import {commentDeleteAPI} from "./commentDelete.js";

document.addEventListener('DOMContentLoaded', async () => {
    const replyDeleteBTNAll = document.querySelectorAll(".replyDeleteBTN");
    replyDeleteBTNAll.forEach(function (replyDeleteBTN) {
        replyDeleteBTN.addEventListener("click", async (ev) => {
            ev.preventDefault();

            const confirmed = window.confirm("정말 이 댓글을 삭제하시겠습니까?\n삭제 후에는 복구할 수 없습니다.");
            if (!confirmed) return;

            // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
            replyDeleteBTN.setAttribute("aria-busy", "true");

            const commentID = replyDeleteBTN.getAttribute("data-comment-id");
            if (!commentID) {
                alert("게시글 ID를 찾을 수 없습니다.");
                replyDeleteBTN.removeAttribute("aria-busy");
                return;
            }

            const _type = "답글";
            await commentDeleteAPI(commentID, _type);
            replyDeleteBTN.removeAttribute("aria-busy");

        });

    });
});