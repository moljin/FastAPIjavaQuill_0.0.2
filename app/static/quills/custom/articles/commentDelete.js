import fastapiClient, {extractErrorMessage, getTagById} from "../../../statics/js/fastapiClient.js";

document.addEventListener('DOMContentLoaded', async () => {
    const commentDeleteBTNAll = document.querySelectorAll(".commentDeleteBTN");
    commentDeleteBTNAll.forEach(function (commentDeleteBTN) {
        commentDeleteBTN.addEventListener("click", async (ev) => {
            ev.preventDefault();

            const confirmed = window.confirm("정말 이 댓글을 삭제하시겠습니까?\n삭제 후에는 복구할 수 없습니다.");
            if (!confirmed) return;

            // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
            commentDeleteBTN.setAttribute("aria-busy", "true");

            const commentID = commentDeleteBTN.getAttribute("data-comment-id");
            if (!commentID) {
                alert("게시글 ID를 찾을 수 없습니다.");
                commentDeleteBTN.removeAttribute("aria-busy");
                return;
            }
            const _type = "댓글";
            await commentDeleteAPI(commentID, _type);
            commentDeleteBTN.removeAttribute("aria-busy");

        });


    });
});

export async function commentDeleteAPI(commentID, _type) {
    try {
        const data = await fastapiClient('delete', '/apis/articles/comments/' + commentID, {});
        console.log(data);
        alert(data?.detail || `${_type} 삭제가 완료되었습니다.`);
        window.location.reload();
    } catch (e) {
        const msg = extractErrorMessage(e) || "댓글 삭제 요청이 실패했습니다.";
        alert(msg);
        console.error("catch withdraw error", e);
    }

}