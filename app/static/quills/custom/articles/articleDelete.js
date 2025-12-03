import fastapiClient, {extractErrorMessage} from "../../../statics/js/fastapiClient.js";

document.addEventListener('DOMContentLoaded', async () => {
    const deleteBtn = document.getElementById("articleDeleteBtn");
    if (!deleteBtn) return;

    deleteBtn.addEventListener("click", async (ev) => {
        ev.preventDefault();

        const confirmed = window.confirm("정말 이 게시글을 삭제하시겠습니까?\n삭제 후에는 복구할 수 없습니다.");
        if (!confirmed) return;

        // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
        deleteBtn.setAttribute("aria-busy", "true");

        const articleIdValue = document.getElementById("article_id")?.value;
        if (!articleIdValue) {
            alert("게시글 ID를 찾을 수 없습니다.");
            deleteBtn.removeAttribute("aria-busy");
            return;
        }

        try {
            const data = await fastapiClient('delete', "/apis/articles/"+articleIdValue, {});
            console.log(data);
            console.log(data.detail);
            alert(data?.detail || `게시글 삭제가 완료되었습니다.`);
            window.location.href = `/views/articles/all`;
        } catch (err) {
            const msg = extractErrorMessage(err) || "게시글 삭제 요청이 실패했습니다.";
            alert(msg);
            console.error("catch withdraw error", err);
        } finally {
            deleteBtn.removeAttribute("aria-busy");
        }

    });
});