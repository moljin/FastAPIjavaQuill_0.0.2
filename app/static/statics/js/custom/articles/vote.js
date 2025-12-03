import fastapiClient, {extractErrorMessage} from "../../fastapiClient.js";

document.addEventListener('DOMContentLoaded', function () {
    const articleVoteBtn = document.getElementById('article-vote');
    const commentVoteBtn = document.getElementById('comment-vote');
    const replyVoteBtn = document.getElementById('reply-vote');

    if (articleVoteBtn) {
        articleVoteBtn.addEventListener('click', async (ev) => {
            ev.preventDefault();

            // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
            articleVoteBtn.setAttribute("aria-busy", "true");

            const articleID = articleVoteBtn.getAttribute("data-comment-id");
            console.log("articleID: ", articleID);
            if (!articleID) {
                alert("게시글 ID를 찾을 수 없습니다.");
                articleVoteBtn.removeAttribute("aria-busy");
                return;
            }

            const voteUrl = `/apis/articles/vote/${articleID}`;
            const svgPaths = articleVoteBtn.querySelectorAll('svg path');
            const countEl = document.getElementById('article-vote-count');

            await voteAPI(voteUrl, countEl, svgPaths);
            articleVoteBtn.removeAttribute("aria-busy");

        });
    }
    if (commentVoteBtn) {
        commentVoteBtn.addEventListener('click', async (ev) => {
            ev.preventDefault();

            // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
            commentVoteBtn.setAttribute("aria-busy", "true");

            const commentID = commentVoteBtn.getAttribute("data-comment-id");
            console.log("commentID: ", commentID);
            if (!commentID) {
                alert("게시글 ID를 찾을 수 없습니다.");
                commentVoteBtn.removeAttribute("aria-busy");
                return;
            }

            const voteUrl = `/apis/articles/comments/vote/${commentID}`;
            const svgPaths = commentVoteBtn.querySelectorAll('svg path');
            const countEl = document.getElementById('comment-vote-count');

            await voteAPI(voteUrl, countEl, svgPaths);
            commentVoteBtn.removeAttribute("aria-busy");

        });
    }
    if (replyVoteBtn) {
        replyVoteBtn.addEventListener('click', async (ev) => {
            ev.preventDefault();

            // 중복 클릭 방지 표시(필요 시 클래스/스타일은 프로젝트에 맞게 조정)
            replyVoteBtn.setAttribute("aria-busy", "true");

            const commentID = replyVoteBtn.getAttribute("data-comment-id");
            console.log("commentID: ", commentID);
            if (!commentID) {
                alert("게시글 ID를 찾을 수 없습니다.");
                replyVoteBtn.removeAttribute("aria-busy");
                return;
            }

            const voteUrl = `/apis/articles/comments/vote/${commentID}`;
            const countEl = document.getElementById('reply-vote-count');
            const svgPaths = replyVoteBtn.querySelectorAll('svg path');

            await voteAPI(voteUrl, countEl, svgPaths);
            replyVoteBtn.removeAttribute("aria-busy");

        });
    }


});

async function voteAPI(voteUrl, countEl, paths) {
    try {
        const data = await fastapiClient('post', voteUrl, {});
        console.log("data.result: ", data.result); // delete 혹은 insert
        console.log("data.voter_count: ", data.voter_count);
        countEl.textContent = data.voter_count;
        if (data.result === 'delete') {
            paths.forEach(path => {
                path.style.stroke = '';
                path.style.fill = '';
            });
        } else {
            // 찾은 모든 path 요소에 스타일을 적용합니다.
            paths.forEach(path => {
                path.style.stroke = '#c23616';
                path.style.fill = '#c23616';
            });
        }
        ;


    } catch (e) {
        const msg = extractErrorMessage(e) || "좋아요 요청이 실패했습니다.";
        alert(msg);
        console.error("catch withdraw error", e);
    }
}