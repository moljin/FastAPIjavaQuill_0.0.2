import fastapiClient, {getTagById, extractErrorMessage} from '../../fastapiClient.js';

document.addEventListener('DOMContentLoaded', () => {
    const withDrawBtn = document.getElementById("withDrawBtn");
    if (!withDrawBtn) return;
    withDrawBtn.addEventListener('click', async (ev) => {
        ev.preventDefault();

        const confirmed = window.confirm("정말로 회원을 탈퇴하시겠습니까?\n관련 모든 데이터가 삭제되고, 작업 후 되돌릴 수 없습니다.");
        if (!confirmed) {
            return;
        }

        // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
        withDrawBtn.setAttribute("aria-busy", "true");

        const userIdValue = document.getElementById("user_id")?.value;
        const errorTag = getTagById("errorTag");

        if (!userIdValue) {
            alert("게시글 ID를 찾을 수 없습니다.");
            withDrawBtn.removeAttribute("aria-busy");
            return;
        }

        try {
            const data = await fastapiClient('delete', '/apis/accounts/account/delete/'+userIdValue, {});
            console.log(data);
            alert(data?.detail || "회원 탈퇴가 완료되었습니다.");
            window.location.href = `/`;
        } catch (e) {
            const msg =extractErrorMessage(e) || "회원 탈퇴 요청이 실패했습니다.";
            errorTag.style.display = 'block';
            errorTag.innerText = msg;
            console.error("catch withdraw error", e);
        } finally {
            withDrawBtn.removeAttribute("aria-busy");
        }
    });
});
