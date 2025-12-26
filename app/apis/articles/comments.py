from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, ARTICLE_COMMENT_EDITOR_USER_IMG_UPLOAD_DIR, ARTICLE_COMMENT_EDITOR_USER_VIDEO_UPLOAD_DIR
from app.core.redis import get_redis_client
from app.core.settings import APP_DIR
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.schemas.articles import comments as schema_comment
from app.services.articles.article_service import ArticleService, get_article_service
from app.services.articles.comment_service import ArticleCommentService, get_articlecomment_service
from app.utils.commons import remove_file_path, remove_empty_dir
from app.utils.exc_handler import CustomErrorException
from app.utils.wysiwyg import redis_delete_candidates, cleanup_unused_images, cleanup_unused_videos, extract_img_srcs, extract_video_srcs, object_delete_with_image_or_video

router = APIRouter()
' prefix="/apis/articles/comments"'

@router.post("/post/{article_id}", response_model=schema_comment.CommentOut,)
async def comment_create(article_id: int,
                         comment_in: schema_comment.CommentIn,
                         article_service: ArticleService = Depends(get_article_service),
                         articlecomment_service: ArticleCommentService = Depends(get_articlecomment_service),
                         current_user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)) -> schema_comment.CommentOut:
    article = await article_service.get_article(article_id)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="해당 질문을 찾을 수 없습니다."
        )
    created_comment = await articlecomment_service.create_comment(article, comment_in, current_user)

    comment_id = created_comment.id
    if not comment_id:
        raise HTTPException(status_code=502, detail="Invalid response from comment API: missing id")

    # img 임시 후보 키(0)를 실제 article_id 키로 이동
    temp_img_key = "delete_image_candidates:0"
    real_img_key = f"delete_image_candidates:{comment_id}"
    print("await redis_client.exists(temp_img_key)::", await redis_client.exists(temp_img_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_img_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_img_key, real_img_key)

    # video
    temp_video_key = "delete_video_candidates:0"
    real_video_key = f"delete_video_candidates:{comment_id}"
    print("await redis_client.exists(temp_video_key)::", await redis_client.exists(temp_video_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_video_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_video_key, real_video_key)
    # 최종 저장 시 삭제 예정 이미지 정리
    _type = "article_comment"
    ''' _type은 is_media_used_elsewhere 이 함수에서 적용된다. '''
    await cleanup_unused_images(_type, comment_id, comment_in.content, db)
    await cleanup_unused_videos(_type, comment_id, comment_in.content, db)

    return created_comment # ORM 객체를 그대로 반환해도 Pydantic이 변환해 줍니다.


@router.patch("/update/{comment_id}",
            response_model = schema_comment.CommentOut)
async def update_comment(comment_id: int,
                         comment_in: schema_comment.CommentIn,
                         articlecomment_service: ArticleCommentService = Depends(get_articlecomment_service),
                         current_user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):

    _comment = await articlecomment_service.get_comment(comment_id)
    old_quills_imgs = extract_img_srcs(_comment.content)
    old_quills_videos = extract_video_srcs(_comment.content)

    updated_comment = await articlecomment_service.update_comment(comment_id, comment_in, current_user)
    if updated_comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="답변 데이터를 찾을 수 없습니다."
        )
    if updated_comment is False:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Not authorized: 접근 권한이 없습니다."
        )

    comment_id = updated_comment.id
    if not comment_id:
        raise HTTPException(status_code=502, detail="Invalid response from comment API: missing id")

    # img 임시 후보 키(0)를 실제 article_id 키로 이동
    temp_img_key = "delete_image_candidates:0"
    real_img_key = f"delete_image_candidates:{comment_id}"
    print("await redis_client.exists(temp_img_key)::", await redis_client.exists(temp_img_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_img_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_img_key, real_img_key)

    # video
    temp_video_key = "delete_video_candidates:0"
    real_video_key = f"delete_video_candidates:{comment_id}"
    print("await redis_client.exists(temp_video_key)::", await redis_client.exists(temp_video_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_video_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_video_key, real_video_key)
    # 최종 저장 시 삭제 예정 이미지 정리
    _type = "article_comment"
    ''' _type은 is_media_used_elsewhere 이 함수에서 적용된다. '''
    await cleanup_unused_images(_type, comment_id, comment_in.content, db)
    await cleanup_unused_videos(_type, comment_id, comment_in.content, db)

    # quills content의 이미지 중에서 예전것만 골라서 삭제
    new_quills_imgs = extract_img_srcs(updated_comment.content)
    print("new_quills_imgs:", new_quills_imgs)
    # only_old_quills_imgs = old_quills_imgs - new_quills_imgs
    only_old_quills_imgs = old_quills_imgs.difference(new_quills_imgs)
    for url in only_old_quills_imgs:
        print("url:", url)
        quill_img_path = f'{APP_DIR}{url}'  # \\없어도 된다. url 맨 앞에 \\ 있다.
        await remove_file_path(quill_img_path)
        # 아래도 같은 작동을 한다.
        # file_path = Path(APP_DIR) / url.lstrip("/\\")
        # if file_path.exists():
        #     file_path.unlink()

    # 삭제후 폴더가 비어 있으면 폴더도 삭제
    img_dir = f'{ARTICLE_COMMENT_EDITOR_USER_IMG_UPLOAD_DIR}' + '/' + f'{current_user.id}'
    await remove_empty_dir(img_dir)

    # quills content의 동영상 중에서 예전것만 골라서 삭제
    new_quills_videos = extract_video_srcs(updated_comment.content)
    print("new_quills_videos:", new_quills_videos)
    only_old_quills_videos = old_quills_videos.difference(new_quills_videos)
    for url in only_old_quills_videos:
        print("url:", url)
        quill_video_path = f'{APP_DIR}{url}'  # \\없어도 된다. url 맨 앞에 \\ 있다.
        await remove_file_path(quill_video_path)

    # 삭제후 폴더가 비어 있으면 폴더도 삭제
    video_dir = f'{ARTICLE_COMMENT_EDITOR_USER_VIDEO_UPLOAD_DIR}' + '/' + f'{current_user.id}'
    await remove_empty_dir(video_dir)
    # #### end
    # return updated_comment
    # ORM -> Pydantic 변환
    return schema_comment.CommentOut.model_validate(updated_comment, from_attributes=True)


@router.delete("/{comment_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="게시글의 코멘트 삭제",
               description="특정 게시글의 특정 코멘트를 삭제합니다.",
               responses={200: {
                   "description": "코멘트 삭제 성공",
                   "content": {"application/json": {"example": {"detail": "코멘트이 성공적으로 삭제되었습니다."}}},
                   404: {
                       "description": "코멘트 삭제 실패",
                       "content": {"application/json": {"example": {"detail": "해당 코멘트을 찾을 수 없습니다."}}}
                   }
               }})
async def delete_comment(comment_id: int,
                         articlecomment_service: ArticleCommentService = Depends(get_articlecomment_service),
                         current_user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):

    _comment = await articlecomment_service.get_comment(comment_id)
    if not _comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글이 존재하지 않습니다."
        )


    """ # 댓글의 id가 다른 코멘트의 paired_comment_id 이면, 그 댓글은 삭제 불가
    query = (select(ArticleComment).where(ArticleComment.paired_comment_id == comment_id))
    result = await db.execute(query)
    replies_with_paired_comment_id = result.scalars().all()
    """
    replies_with_paired_comment_id = await articlecomment_service.get_replies_with_paired_comment_id(comment_id)
    print("replies_with_paired_comment_id:", [reply.id for reply in replies_with_paired_comment_id])
    if len(replies_with_paired_comment_id) > 0:
        raise CustomErrorException(status_code=416, detail="답글이 있는 댓글은 삭제할 수 없습니다.")

    # quills content 이미지
    img_key = f"delete_image_candidates:{comment_id}"
    await object_delete_with_image_or_video(_type="article_comment", # is_media_used_elsewhere 에서 사용
                                            _id=comment_id,
                                            html=_comment.content,
                                            _dir=ARTICLE_COMMENT_EDITOR_USER_IMG_UPLOAD_DIR,
                                            current_user_id=current_user.id,
                                            db=db,
                                            key=img_key)

    # quills content 동영상
    video_key = f"delete_video_candidates:{comment_id}"
    await object_delete_with_image_or_video(_type="article_comment", # is_media_used_elsewhere 에서 사용
                                            _id=comment_id,
                                            html=_comment.content,
                                            _dir=ARTICLE_COMMENT_EDITOR_USER_VIDEO_UPLOAD_DIR,
                                            current_user_id=current_user.id,
                                            db=db,
                                            key=video_key)

    comment = await articlecomment_service.delete_comment(comment_id, current_user)
    if comment is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    if comment is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: 접근 권한이 없습니다."
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/vote/{comment_id}")#, status_code=status.HTTP_204_NO_CONTENT)
async def comment_vote(comment_id: int,
                       articlecomment_service: ArticleCommentService = Depends(get_articlecomment_service),
                       current_user: User = Depends(get_current_user)):

    comment = await articlecomment_service.get_comment(comment_id)
    print("comment:", comment)
    if not comment:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="데이터를 찾을수 없습니다.")
    data = await articlecomment_service.vote_comment(comment_id, current_user)
    # return Response(status_code=status.HTTP_204_NO_CONTENT)
    return data