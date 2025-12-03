from typing import List

from fastapi import status, UploadFile, Depends, APIRouter, Body, File, HTTPException

from app.core.database import ARTICLE_EDITOR_USER_VIDEO_UPLOAD_DIR, ARTICLE_EDITOR_USER_IMG_UPLOAD_DIR, ARTICLE_COMMENT_EDITOR_USER_IMG_UPLOAD_DIR, ARTICLE_COMMENT_EDITOR_USER_VIDEO_UPLOAD_DIR
from app.dependencies.auth import get_current_user
from app.models.users import User
from app.utils.commons import file_write_return_url
from app.utils.wysiwyg import redis_add, redis_rem

router = APIRouter()
"""prefix="/apis/wysiwyg"""

@router.post("/article/image/upload")
async def article_image_upload(imagefile: UploadFile,
                       current_user: User = Depends(get_current_user)):
    try:
        upload_dir = f'{ARTICLE_EDITOR_USER_IMG_UPLOAD_DIR}' + '/' + f'{current_user.id}' + '/'  # d/t Linux
        url = await file_write_return_url(upload_dir, current_user, imagefile, "app", _type="image")
        return {"url": url}

    except Exception as e:
        print("upload_image error:::", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="에디터의 이미지 파일이 제대로 Upload되지 않았습니다. ")


@router.post("/article/video/upload")
async def article_video_upload(videofile: UploadFile = File(...),
                       current_user: User = Depends(get_current_user)):
    try:
        upload_dir = f'{ARTICLE_EDITOR_USER_VIDEO_UPLOAD_DIR}' + '/' + f'{current_user.id}' + '/'  # d/t Linux
        url = await file_write_return_url(upload_dir, current_user, videofile, "app", _type="video")
        return {"url": url}
    except Exception as e:
        print("upload_video error:::", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="에디터의 동영상 파일이 제대로 Upload되지 않았습니다. ")


@router.post("/article/comment/image/upload")
async def article_comment_image_upload(imagefile: UploadFile,
                       current_user: User = Depends(get_current_user)):
    try:
        upload_dir = f'{ARTICLE_COMMENT_EDITOR_USER_IMG_UPLOAD_DIR}' + '/' + f'{current_user.id}' + '/'  # d/t Linux
        url = await file_write_return_url(upload_dir, current_user, imagefile, "app", _type="image")
        return {"url": url}

    except Exception as e:
        print("upload_image error:::", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="에디터의 이미지 파일이 제대로 Upload되지 않았습니다. ")


@router.post("/article/comment/video/upload")
async def article_comment_video_upload(videofile: UploadFile = File(...),
                       current_user: User = Depends(get_current_user)):
    try:
        upload_dir = f'{ARTICLE_COMMENT_EDITOR_USER_VIDEO_UPLOAD_DIR}' + '/' + f'{current_user.id}' + '/'  # d/t Linux
        url = await file_write_return_url(upload_dir, current_user, videofile, "app", _type="video")
        return {"url": url}
    except Exception as e:
        print("upload_video error:::", e)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                            detail="에디터의 동영상 파일이 제대로 Upload되지 않았습니다. ")


#############################################################################################################
@router.post("/mark_delete_images/{mark_id}")
async def mark_delete_images(mark_id: int, srcs: List[str] = Body(...)):
    print("mark_delete_images:::mark_id:::", mark_id)
    key = f"delete_image_candidates:{mark_id}"
    added_count = await redis_add(srcs, key)
    return {"marked": srcs, "added": added_count}


@router.post("/unmark_delete_images/{mark_id}")
async def unmark_delete_images(mark_id: int, srcs: List[str]):
    print("unmark_delete_images:::mark_id:::", mark_id)
    key = f"delete_image_candidates:{mark_id}"
    removed_count = await redis_rem(srcs, key)
    return {"unmarked": srcs, "removed": removed_count}


###############################################################################################################
@router.post("/mark_delete_videos/{mark_id}")
async def mark_delete_videos(mark_id: int, srcs: List[str] = Body(...)):
    print("mark_delete_videos:::mark_id:::", mark_id)
    key = f"delete_video_candidates:{mark_id}"
    added_count = await redis_add(srcs, key)

    return {"marked": srcs, "added": added_count}


@router.post("/unmark_delete_videos/{mark_id}")
async def unmark_delete_videos(mark_id: int, srcs: List[str]):
    print("unmark_delete_videos:::mark_id:::", mark_id)
    key = f"delete_video_candidates:{mark_id}"
    removed_count = await redis_rem(srcs, key)

    return {"unmarked": srcs, "removed": removed_count}
