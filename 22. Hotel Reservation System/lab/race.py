import os, threading, psycopg
from psycopg import errors

DSN = f"host={os.environ['PGHOST']} user={os.environ['PGUSER']} " \
      f"password={os.environ['PGPASSWORD']} dbname={os.environ['PGDATABASE']}"
barrier = threading.Barrier(2)
results = {}

CHECK = """SELECT count(*) FROM bookings
           WHERE room_id=101 AND status IN ('HELD','CONFIRMED')
             AND daterange(check_in,check_out) && daterange('2026-10-25','2026-10-27')"""
INSERT = """INSERT INTO bookings(room_id,guest,check_in,check_out,status)
            VALUES (101,%s,'2026-10-25','2026-10-27','CONFIRMED')"""

def book(guest):
    with psycopg.connect(DSN) as conn:
        cur = conn.cursor()
        free = cur.execute(CHECK).fetchone()[0] == 0   # app-level check
        barrier.wait()                                  # ép 2 bên cùng check xong rồi mới insert
        if not free:
            results[guest] = "REJECTED (check)"; return
        try:
            cur.execute(INSERT, (guest,)); conn.commit()
            results[guest] = "OK"
        except errors.ExclusionViolation:
            conn.rollback(); results[guest] = "REJECTED (exclusion_violation)"

ts = [threading.Thread(target=book, args=(g,)) for g in ("A", "B")]
[t.start() for t in ts]; [t.join() for t in ts]
print(results)