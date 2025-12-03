import fastapiClient, {extractErrorMessage, getCookie, getTagById} from '../../../static/statics/js/fastapiClient.js';

const errorTag = getTagById("errorTag");
const articleIDTag = getTagById("article_id");

export const articleSubmit = async (event, {params, setError}) => {
    event.preventDefault();
    let url;
    let method;
    if (!articleIDTag) {
        url = '/apis/articles/post';
        method = 'post';
    } else {
        url = '/apis/articles/update/' + articleIDTag.value;
        method = 'patch';
    }

    try {
        const data = await fastapiClient(method, url, params);
        window.location.href = '/views/articles/article/' + data.id;
    } catch (err) {
        console.log("article submit 실패", err);           // 실패 시 error/response 로그
        if (setError) {
            const msg = extractErrorMessage(err) || '게시글 저장에 실패했습니다.';
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch article submit error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }
};


export const commentSubmit = async (event, {params, setError}) => {
    const pairedCommentID = params.paired_comment_id;
    const commentID = params.comment_id;

    event.preventDefault();
    let url;
    let method;
    if (!commentID && !pairedCommentID) {
        url = '/apis/articles/comments/post/' + articleIDTag.value;
        method = 'post';
    } else if (!commentID && pairedCommentID) {
        url = '/apis/articles/comments/post/' + articleIDTag.value;
        method = 'post';
    } else {
        delete params.comment_id; // 데이터 업데이트에는 필요없으니 comment_id는 삭제....
        url = '/apis/articles/comments/update/' + commentID;
        method = 'patch';
    }

    try {
        const data = await fastapiClient(method, url, params);
        window.location.reload();

    } catch (err) {
        console.log("comment submit 실패", err);           // 실패 시 error/response 로그
        if (setError) {
            const msg = extractErrorMessage(err) || '질문/댓글 저장에 실패했습니다.';
            if (errorTag) {
                errorTag.style.display = 'block';
                errorTag.innerText = msg;
                console.error("1. catch comment submit error", err);
            }
        }
        throw err; // 필요하면 에러 다시 던지기
    }
};





