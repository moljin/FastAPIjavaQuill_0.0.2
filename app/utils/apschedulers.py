from apscheduler.schedulers.asyncio import AsyncIOScheduler

# 스케줄러 인스턴스 생성
scheduler = AsyncIOScheduler()


async def scheduled_lotto_update():
    """스케줄된 로또 업데이트 함수"""
    from app.core.database import get_db
    from app.lottos.utils import extract_latest_round, extract_first_win_num, latest_lotto
    from app.lottos.models import LottoNum, STATUS

    # 데이터베이스 세션 생성
    async for db in get_db():
        try:
            old_latest = await latest_lotto(db)
            latest_page = await extract_latest_round()

            # 기존 로직과 동일하게 처리
            if old_latest and old_latest.latest_round_num == latest_page:
                print(f"이미 최신 회차({latest_page})가 저장되어 있습니다.")
                return

            if int(latest_page):  # 최신 회차가 있다면
                lotto_num_list, top10_list = await extract_first_win_num(db)

                if old_latest:
                    old_latest.status = STATUS[0]
                    db.add(old_latest)
                    await db.commit()
                    await db.refresh(old_latest)

                new = LottoNum()
                new.title = latest_page + "회차"
                new.latest_round_num = latest_page
                new.extract_num = str(top10_list)
                new.lotto_num_list = str(lotto_num_list)
                db.add(new)
                await db.commit()
                await db.refresh(new)

                print(f"새로운 회차({latest_page}) 데이터가 저장되었습니다.")

        except Exception as e:
            print(f"스케줄된 업데이트 중 오류 발생: {e}")
        finally:
            await db.close()
