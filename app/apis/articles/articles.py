from fastapi import APIRouter, Depends, HTTPException, status, Response, Form, UploadFile, File
from pydantic import ValidationError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db, ARTICLE_THUMBNAIL_UPLOAD_DIR, ARTICLE_EDITOR_USER_IMG_UPLOAD_DIR, ARTICLE_EDITOR_USER_VIDEO_UPLOAD_DIR
from app.core.redis import get_redis_client
from app.core.settings import APP_DIR, MEDIA_DIR
from app.dependencies.auth import get_current_user
from app.models.articles import ArticleComment
from app.models.users import User
from app.schemas.articles import articles as schema_article
from app.services.articles.article_service import ArticleService, get_article_service
from app.utils.commons import upload_single_image, old_image_remove, remove_file_path, remove_empty_dir
from app.utils.exc_handler import CustomErrorException
from app.utils.wysiwyg import redis_delete_candidates, cleanup_unused_images, cleanup_unused_videos, extract_img_srcs, object_delete_with_image_or_video, extract_video_srcs

router = APIRouter()
"""prefix="/apis/articles"""

@router.post("/post",
             response_model=schema_article.ArticleOut,
             summary="새 게시글 작성",
             description="새로운 게시글을 생성합니다.",
             responses={400: {
                 "description": "Bad Request: 잘못된 요청입니다.",
                 "content": {"application/json": {"example": {"detail": "Bad Request: 잘못된 요청을 하였습니다."}}}
             }})
async def create_article(title: str = Form(...),
                         content: str = Form(...),
                         imagefile: UploadFile | None = File(None),
                         article_service: ArticleService = Depends(get_article_service),
                         current_user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):

    try:
        article_in = schema_article.ArticleIn(title=title, content=content)
    except ValidationError as e:
        # 요청 본문에 대한 자동 422 변환이 아닌, 수동으로 422로 변환해 주는 것이 좋습니다.
        raise HTTPException(status_code=422, detail=e.errors())

    img_path = None
    if imagefile:
        img_path = await upload_single_image(ARTICLE_THUMBNAIL_UPLOAD_DIR, current_user, imagefile)

    created_article = await article_service.create_article(article_in, current_user, img_path=img_path)

    # 생성된 게시글 ID 확인
    article_id = created_article.id
    if not article_id:
        raise HTTPException(status_code=502, detail="Invalid response from article API: missing id")

    # img 임시 후보 키(0)를 실제 article_id 키로 이동
    temp_img_key = "delete_image_candidates:0"
    real_img_key = f"delete_image_candidates:{article_id}"
    print("await redis_client.exists(temp_img_key)::", await redis_client.exists(temp_img_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_img_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_img_key, real_img_key)

    # video
    temp_video_key = "delete_video_candidates:0"
    real_video_key = f"delete_video_candidates:{article_id}"
    print("await redis_client.exists(temp_video_key)::", await redis_client.exists(temp_video_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_video_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_video_key, real_video_key)
    # 최종 저장 시 삭제 예정 이미지 정리
    _type = "article"
    ''' _type은 is_media_used_elsewhere 이 함수에서 적용된다. '''
    await cleanup_unused_images(_type, article_id, content, db)
    await cleanup_unused_videos(_type, article_id, content, db)

    return created_article


@router.patch("/update/{article_id}",
              response_model=schema_article.ArticleOut,
              summary="게시글 수정",
              description="특정 게시글을 수정합니다.",
              responses={404: {
                  "description": "게시글 수정 실패",
                  "content": {"application/json": {"example": {"detail": "해당 게시글을 찾을 수 없습니다."}}},
                  403: {
                      "description": "게시글 수정 권한 없슴",
                      "content": {"application/json": {"example": {"detail": "접근 권한이 없습니다."}}}
                  }
              }})
async def update_article(article_id: int,
                         title: str = Form(...),
                         content: str = Form(...),
                         imagefile: UploadFile | None = File(None),
                         article_service: ArticleService = Depends(get_article_service),
                         current_user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):

    try:
        article_update = schema_article.ArticleUpdate(title=title, content=content)
    except ValidationError as e:
        # 요청 본문에 대한 자동 422 변환이 아닌, 수동으로 422로 변환해 주는 것이 좋습니다.
        raise HTTPException(status_code=422, detail=e.errors())

    _article = await article_service.get_article(article_id)
    old_quills_imgs = extract_img_srcs(_article.content)
    old_quills_videos = extract_video_srcs(_article.content)

    if len(imagefile.filename.strip()) > 0:
        ## My Add ############## 이미지 교체하면, 예전에 있던 이미지 삭제하기
        await old_image_remove(imagefile.filename, _article.img_path)
        ## Add End ##############
        print("upload_image 직전==========:", imagefile.filename)
        img_path = await upload_single_image(ARTICLE_THUMBNAIL_UPLOAD_DIR, current_user, imagefile)
        print("img_path===================:", img_path)
    else:
        img_path = _article.img_path

    updated_article = await article_service.update_article(article_id, article_update, current_user, img_path=img_path)
    if not updated_article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    if updated_article is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized: 접근 권한이 없습니다."
        )

    # 생성된 게시글 ID 확인
    article_id = updated_article.id
    if not article_id:
        raise HTTPException(status_code=502, detail="Invalid response from article API: missing id")

    # img 임시 후보 키(0)를 실제 article_id 키로 이동
    temp_img_key = "delete_image_candidates:0"
    real_img_key = f"delete_image_candidates:{article_id}"
    print("await redis_client.exists(temp_img_key)::", await redis_client.exists(temp_img_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_img_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_img_key, real_img_key)

    # video
    temp_video_key = "delete_video_candidates:0"
    real_video_key = f"delete_video_candidates:{article_id}"
    print("await redis_client.exists(temp_video_key)::", await redis_client.exists(temp_video_key))
    """quills content에 이미지를 로드했다가 지우면, 
    await redis_client.exists(temp_video_key)이 1이 되고, if 문을 지나간다. 
    이미지를 로드하지 않거나, 로드했다가 지운 이미지가 없으면 그냥 if 문을 우회한다."""
    await redis_delete_candidates(temp_video_key, real_video_key)

    # 최종 저장 시 삭제 예정 이미지 정리
    _type = "article"
    ''' _type은 is_media_used_elsewhere 이 함수에서 적용된다. '''
    await cleanup_unused_images(_type, article_id, content, db)
    await cleanup_unused_videos(_type, article_id, content, db)

    # quills content의 이미지 중에서 예전것만 골라서 삭제
    new_quills_imgs = extract_img_srcs(updated_article.content)
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
    img_dir = f'{ARTICLE_EDITOR_USER_IMG_UPLOAD_DIR}'+'/'+f'{current_user.id}'
    await remove_empty_dir(img_dir)

    # quills content의 동영상 중에서 예전것만 골라서 삭제
    new_quills_videos = extract_video_srcs(updated_article.content)
    print("new_quills_videos:", new_quills_videos)
    only_old_quills_videos = old_quills_videos.difference(new_quills_videos)
    for url in only_old_quills_videos:
        print("url:", url)
        quill_video_path = f'{APP_DIR}{url}'  # \\없어도 된다. url 맨 앞에 \\ 있다.
        await remove_file_path(quill_video_path)

    # 삭제후 폴더가 비어 있으면 폴더도 삭제
    video_dir = f'{ARTICLE_EDITOR_USER_VIDEO_UPLOAD_DIR}' + '/' + f'{current_user.id}'
    await remove_empty_dir(video_dir)
    # #### end

    return updated_article


@router.delete("/{article_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="게시글 삭제",
               description="특정 게시글을 삭제합니다.",
               responses={200: {
                   "description": "게시글 삭제 성공",
                   "content": {"application/json": {"example": {"detail": "게시글이 성공적으로 삭제되었습니다."}}},
                   404: {
                       "description": "게시글 삭제 실패",
                       "content": {"application/json": {"example": {"detail": "해당 게시글을 찾을 수 없습니다."}}}
                   }
               }})
async def delete_article(article_id: int,
                         article_service: ArticleService = Depends(get_article_service),
                         current_user: User = Depends(get_current_user),
                         db: AsyncSession = Depends(get_db)):

    _article = await article_service.get_article(article_id)
    if not _article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글이 존재하지 않습니다."
        )

    query = (select(ArticleComment).where(ArticleComment.article_id == article_id))
    result = await db.execute(query)
    comments_of_article = result.scalars().all()
    if len(comments_of_article) > 0:
        raise CustomErrorException(status_code=416, detail="댓글이 있는 게시글은 삭제할 수 없습니다.")

    # thumbnail 이미지 파일 삭제
    thumbnail_img_path = _article.img_path
    full_img_path = f'{MEDIA_DIR}'+'/'+f'{thumbnail_img_path}'
    await remove_file_path(full_img_path)

    img_dir = f'{ARTICLE_THUMBNAIL_UPLOAD_DIR}'+'/'+f'{current_user.id}'
    await remove_empty_dir(img_dir) # 삭제후 폴더가 비어 있으면 폴더도 삭제

    # quills content 이미지
    img_key = f"delete_image_candidates:{article_id}"
    await object_delete_with_image_or_video(_type="article", # is_media_used_elsewhere 에서 사용
                                            _id=article_id,
                                            html=_article.content,
                                            _dir=ARTICLE_EDITOR_USER_IMG_UPLOAD_DIR,
                                            current_user_id=current_user.id,
                                            db=db,
                                            key=img_key)

    # quills content 동영상
    video_key = f"delete_video_candidates:{article_id}"
    await object_delete_with_image_or_video(_type="article", # is_media_used_elsewhere 에서 사용
                                            _id=article_id,
                                            html=_article.content,
                                            _dir=ARTICLE_EDITOR_USER_VIDEO_UPLOAD_DIR,
                                            current_user_id=current_user.id,
                                            db=db,
                                            key=video_key)

    article = await article_service.delete_article(article_id, current_user)
    if article is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="게시글을 찾을 수 없습니다."
        )
    if article is False:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
                detail="Not authorized: 접근 권한이 없습니다."
        )

    return Response(status_code=status.HTTP_204_NO_CONTENT)

@router.post("/vote/{article_id}")#, status_code=status.HTTP_204_NO_CONTENT)
async def article_vote(article_id: int,
                  article_service: ArticleService = Depends(get_article_service),
                  current_user: User = Depends(get_current_user)):
    article = await article_service.get_article(article_id)
    if not article:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,
                            detail="데이터를 찾을수 없습니다.")
    data = await article_service.vote_article(article_id, current_user)
    # return Response(status_code=status.HTTP_204_NO_CONTENT)
    return data