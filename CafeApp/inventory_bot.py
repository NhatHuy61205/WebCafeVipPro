import datetime
from apscheduler.schedulers.background import BackgroundScheduler

_scheduler = None


def start_inventory_scheduler(app, db):
    global _scheduler
    if _scheduler:
        return

    def _scan_and_notify_for_bot(bot):
        # import models ở đây để tránh circular import
        from CafeApp.models import (
            NguyenLieu, ThongBaoKho,
            LoaiThongBaoKhoEnum, TrangThaiThongBaoKhoEnum
        )

        today = datetime.date.today()

        if bot.last_run_date == today:
            return

        lows = []
        nls = NguyenLieu.query.all()

        for nl in nls:
            qty = float(getattr(nl, "soLuongTon", 0) or 0)
            min_qty = float(getattr(nl, "soLuongToiThieu", 0) or 0)
            if qty <= min_qty:
                lows.append((nl, qty, min_qty))

        if lows:
            for nl, qty, min_qty in lows:
                existed = ThongBaoKho.query.filter(
                    ThongBaoKho.loai == LoaiThongBaoKhoEnum.LOW_STOCK,
                    ThongBaoKho.nguyenLieu_id == nl.id,
                    ThongBaoKho.run_date == today
                ).first()

                if not existed:
                    unit = getattr(nl, "donViTinh", "") or ""
                    msg = f"{nl.name} chỉ còn {qty} {unit}, mau chóng nhập hàng."
                    db.session.add(ThongBaoKho(
                        message=msg,
                        loai=LoaiThongBaoKhoEnum.LOW_STOCK,
                        trang_thai=TrangThaiThongBaoKhoEnum.UNREAD,
                        nguyenLieu_id=nl.id,
                        run_date=today
                    ))
        else:
            msg = f"Không có nguyên liệu nào dưới ngưỡng ({bot.gioChayHangNgay.strftime('%H:%M')})."
            db.session.add(ThongBaoKho(
                message=msg,
                loai=LoaiThongBaoKhoEnum.DAILY_REPORT,
                trang_thai=TrangThaiThongBaoKhoEnum.UNREAD,
                run_date=today
            ))

        bot.last_run_date = today
        db.session.commit()

    def tick_every_minute():
        from CafeApp.models import SchedulerBot, TrangThaiEnum

        with app.app_context():
            now_dt = datetime.datetime.now()
            today = now_dt.date()
            print("[BOT TICK]", now_dt.strftime("%Y-%m-%d %H:%M:%S"))

            bots = SchedulerBot.query.filter(SchedulerBot.trangThai == TrangThaiEnum.ACTIVE).all()

            for bot in bots:
                if bot.last_run_date == today:
                    continue

                target_dt = datetime.datetime.combine(today, bot.gioChayHangNgay)
                delta_sec = (now_dt - target_dt).total_seconds()

                # cửa sổ 5 phút để tránh miss giờ
                if 0 <= delta_sec <= 300:
                    print("[BOT RUN]", bot.id, bot.gioChayHangNgay)
                    _scan_and_notify_for_bot(bot)

    _scheduler = BackgroundScheduler(daemon=True)
    _scheduler.add_job(tick_every_minute, "interval", minutes=1, id="kho_tick", replace_existing=True)
    _scheduler.start()
    print("[BOT] Scheduler started")
