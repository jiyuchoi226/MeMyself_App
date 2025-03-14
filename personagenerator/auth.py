from fastapi import HTTPException, status, Request

# 현재 로그인된 사용자의 id반환
async def get_current_user(request: Request) -> str:
    try:
        user_id = request.state.user_id
        print("현재 로그인 된 사용자: " , user_id)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="로그인이 필요합니다",
            )
        return user_id
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="로그인이 필요합니다",
        ) 