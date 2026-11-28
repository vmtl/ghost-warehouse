"""One atomic operating day. Requires migration 007 and the imported pilot.
Run: python scripts/simulate_day.py --date YYYY-MM-DD
No replenishment yet. Packing/shipping durations are conceptual, not resource constrained.
"""
import argparse
import os
from collections import defaultdict
from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo
import psycopg
from generate_daily_orders import generate
from pick_paths import build_network, read_locations, route

TZ = ZoneInfo('America/Chicago')
PILOT = date(2026, 11, 23)


def next_day(day):
    day += timedelta(days=1)
    if day.weekday() == 6:
        day += timedelta(days=1)
    return day


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def run(day):
    with psycopg.connect(os.environ['DATABASE_URL']) as conn, conn.cursor() as c:
        c.execute('SELECT pg_advisory_xact_lock(612006)')
        c.execute('LOCK TABLE ghost.inventory_movements, ghost.orders IN SHARE ROW EXCLUSIVE MODE')
        if c.execute('SELECT 1 FROM ghost.daily_operations WHERE operating_date=%s', (day,)).fetchone():
            return f'{day}: already processed; no changes made.'
        require(c.execute("SELECT 1 FROM ghost.pilot_imports WHERE batch_id='pilot-2026-11-23'").fetchone(), 'Import pilot first')
        last = c.execute('SELECT max(operating_date) FROM ghost.daily_operations').fetchone()[0] or PILOT
        require(day == next_day(last), f'Next operating date is {next_day(last)}')
        start = datetime.combine(day, time(6), tzinfo=TZ)
        close = datetime.combine(day, time(22), tzinfo=TZ)
        require(not c.execute("SELECT 1 FROM ghost.orders WHERE status NOT IN ('NEW','BACKORDER','SHIPPED','CANCELLED') LIMIT 1").fetchone(), 'Unexpected in-progress order')
        require(not c.execute('SELECT 1 FROM ghost.orders WHERE placed_at >= %s LIMIT 1', (start,)).fetchone(), 'Future orders already exist')
        stock = defaultdict(dict)
        for pid, lid, q, code in c.execute('SELECT b.product_id,b.location_id,b.on_hand,l.location_code FROM ghost.inventory_balance b JOIN ghost.locations l USING(location_id) ORDER BY b.product_id,l.location_code'):
            require(q >= 0, 'Negative opening stock')
            stock[pid][lid] = [q, code]
        opening = sum(v[0] for locs in stock.values() for v in locs.values())
        backlog = c.execute("SELECT count(*) FROM ghost.orders WHERE status IN ('NEW','BACKORDER')").fetchone()[0]
        customers = c.execute("SELECT customer_id,channel FROM ghost.customers WHERE status='ACTIVE' ORDER BY customer_id").fetchall()
        products = c.execute('SELECT product_id,retail_price FROM ghost.products WHERE active ORDER BY product_id').fetchall()
        demand = generate(day, customers, products, TZ)
        for number, customer, channel, placed, lines in demand:
            oid = c.execute("INSERT INTO ghost.orders(order_number,customer_id,placed_at,status,channel,currency,simulated) VALUES (%s,%s,%s,'NEW',%s,'USD',true) RETURNING order_id", (number,customer,placed,channel)).fetchone()[0]
            for i,(pid,qty,price) in enumerate(lines,1):
                c.execute('INSERT INTO ghost.order_lines(order_id,product_id,quantity,unit_price,source_line_code) VALUES (%s,%s,%s,%s,%s)', (oid,pid,qty,price,f'{number}-{i:02d}'))
        graph, coords, _ = build_network(read_locations())
        workers = {}
        for eid, ss, se in c.execute("SELECT employee_id,shift_start,shift_end FROM ghost.employees WHERE department='Picking' AND status='ACTIVE' ORDER BY employee_id"):
            a = max(start, datetime.combine(day,ss,tzinfo=TZ))
            b = min(close, datetime.combine(day,se,tzinfo=TZ))
            if a < b:
                workers[eid] = [a,b]
        require(workers, 'No active pickers with valid same-day shifts')
        shipped = units = 0
        pending = c.execute("SELECT order_id,order_number,placed_at FROM ghost.orders WHERE status IN ('NEW','BACKORDER') AND placed_at < %s ORDER BY placed_at,order_id", (close,)).fetchall()
        for oid, number, placed in pending:
            lines = c.execute('SELECT order_line_id,product_id,quantity FROM ghost.order_lines WHERE order_id=%s ORDER BY order_line_id',(oid,)).fetchall()
            require(lines, 'Order has no lines')
            allocations = []
            reserved = defaultdict(int)
            complete = True
            for line,pid,qty in lines:
                need = qty
                for lid,(q,code) in stock[pid].items():
                    take = min(need,q-reserved[pid,lid])
                    if take > 0:
                        allocations.append((line,pid,lid,take,code))
                        reserved[pid,lid] += take
                        need -= take
                    if not need:
                        break
                if need:
                    complete = False
                    break
            if not complete:
                c.execute("UPDATE ghost.orders SET status='BACKORDER' WHERE order_id=%s",(oid,))
                continue
            trip = route(graph,coords,[a[4] for a in allocations],optimize=True)
            distance = float(trip['distance_ft'])
            pick_minutes = max(1,len(allocations)*1.5) + distance/240
            duration = timedelta(minutes=pick_minutes)
            options = []
            for eid,(available,end) in workers.items():
                begin = max(start,placed,available)
                picked = begin + duration
                if picked <= end and picked + timedelta(minutes=12) <= close:
                    options.append((begin,eid,picked))
            if not options:
                c.execute("UPDATE ghost.orders SET status='BACKORDER' WHERE order_id=%s",(oid,))
                continue
            begin,eid,picked = min(options)
            workers[eid][0] = picked
            packed = picked + timedelta(minutes=5)
            ship = packed + timedelta(minutes=7)
            c.execute('INSERT INTO ghost.pick_tasks VALUES (%s,%s,%s,%s,%s,%s,%s)',(f'{number}-PICK',oid,eid,'COMPLETED',round(distance,2),round(pick_minutes,2),'NEAREST_NEIGHBOR_CONCEPTUAL'))
            for kind,at,worker in [('ALLOCATED',begin,eid),('PICKED',picked,eid),('PACKED',packed,None),('SHIPPED',ship,None)]:
                c.execute('INSERT INTO ghost.fulfillment_events VALUES (%s,%s,%s,%s,%s)',(f'{number}-{kind}',oid,kind,at,worker))
            for i,(line,pid,lid,q,_) in enumerate(allocations,1):
                c.execute('INSERT INTO ghost.allocations VALUES (%s,%s,%s,%s)',(line,lid,q,'FULFILLED'))
                c.execute("INSERT INTO ghost.inventory_movements(product_id,from_location_id,quantity,movement_type,occurred_at,reference_type,reference_id) VALUES (%s,%s,%s,'SHIP',%s,'DAILY_SHIPMENT',%s)",(pid,lid,q,ship,f'{number}-{i:03d}'))
                stock[pid][lid][0] -= q
                units += q
            c.execute("UPDATE ghost.orders SET status='SHIPPED' WHERE order_id=%s",(oid,))
            shipped += 1
        closing, negatives = c.execute('SELECT coalesce(sum(on_hand),0),count(*) FILTER (WHERE on_hand<0) FROM ghost.inventory_balance').fetchone()
        remaining = c.execute("SELECT count(*) FROM ghost.orders WHERE status IN ('NEW','BACKORDER')").fetchone()[0]
        require(negatives==0 and closing==opening-units, 'Inventory reconciliation failed')
        require(backlog+len(demand)==shipped+remaining,'Order reconciliation failed')
        actual = {(p,l):q for p,l,q in c.execute('SELECT product_id,location_id,on_hand FROM ghost.inventory_balance')}
        require(actual=={(p,l):v[0] for p,locs in stock.items() for l,v in locs.items()},'Location-level reconciliation failed')
        c.execute('INSERT INTO ghost.daily_operations(operating_date,opening_inventory,opening_backlog,new_orders,shipped_orders,shipped_units,closing_backlog,closing_inventory) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)',(day,opening,backlog,len(demand),shipped,units,remaining,closing))
    return f'{day}: {len(demand)} new orders, {shipped} shipped, {remaining} backlog, {units} units shipped, {closing} inventory remaining.'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',required=True,type=date.fromisoformat)
    print(run(parser.parse_args().date))
