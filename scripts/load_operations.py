"""Import the validated 25-order pilot atomically; requires migration 006."""
import csv
import os
from collections import Counter
from pathlib import Path
import psycopg

DATA = Path(__file__).resolve().parents[1] / 'data'

def read(name):
    with (DATA / (name + '.csv')).open(encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))

def require(condition, message):
    if not condition:
        raise ValueError(message)

def main():
    with psycopg.connect(os.environ['DATABASE_URL']) as conn, conn.cursor() as c:
        c.execute('SELECT pg_advisory_xact_lock(612006)')
        if c.execute("SELECT 1 FROM ghost.pilot_imports WHERE batch_id='pilot-2026-11-23'").fetchone():
            print('Pilot already imported; no changes made.')
            return
        c.execute('LOCK TABLE ghost.inventory_movements, ghost.orders IN SHARE ROW EXCLUSIVE MODE')
        require(c.execute('SELECT count(*) FROM ghost.orders').fetchone()[0] == 0, 'Expected empty orders table')
        def balances():
            return {(s,l):q for s,l,q in c.execute('SELECT p.sku,l.location_code,b.on_hand FROM ghost.inventory_balance b JOIN ghost.products p USING(product_id) JOIN ghost.locations l USING(location_id)')}
        expected = read('fulfillment_balances')
        require(balances() == {(r['sku'],r['location_code']):int(r['opening_quantity']) for r in expected}, 'Opening balances differ from pilot')
        employees, suppliers, customers = map(read, ('employees','suppliers','customers'))
        require(len(employees)==75 and len(suppliers)==30, 'Unexpected master data counts')
        for r in employees:
            c.execute('INSERT INTO ghost.employees VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)', tuple(r[k] for k in ('employee_id','employee_name','department','job_title','shift','shift_start','shift_end','hourly_rate_usd','status','simulated')))
        for r in suppliers:
            c.execute('INSERT INTO ghost.suppliers(supplier_code,supplier_name,lead_time_days,supplier_type,primary_manufacturer,on_time_delivery_target_pct,minimum_order_usd,currency,status,simulated) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)',tuple(r[k] for k in ('supplier_id','supplier_name','lead_time_days','supplier_type','primary_manufacturer','on_time_delivery_target_pct','minimum_order_usd','currency','status','simulated')))
        for r in customers:
            c.execute('INSERT INTO ghost.customers(customer_code,company_name,customer_type,channel,payment_terms,status,simulated) VALUES (%s,%s,%s,%s,%s,%s,%s)',tuple(r[k] for k in ('customer_id','customer_name','customer_type','channel','payment_terms','status','simulated')))
        def mapping(table, key, val):
            return dict(c.execute(f'SELECT {key},{val} FROM ghost.{table}').fetchall())
        customer=mapping('customers','customer_code','customer_id')
        product=mapping('products','sku','product_id')
        location=mapping('locations','location_code','location_id')
        orders, lines, outcomes = map(read, ('orders','order_lines','fulfillment_order_status'))
        require(len(orders)==len(outcomes)==25 and all(r['status']=='SHIPPED' for r in outcomes), 'Unexpected pilot order outcomes')
        require({r['order_id'] for r in orders}=={r['order_id'] for r in outcomes}, 'Order outcome mismatch')
        for r in orders:
            c.execute('INSERT INTO ghost.orders(order_number,customer_id,placed_at,status,channel,currency,simulated) VALUES (%s,%s,%s,%s,%s,%s,%s)',(r['order_id'],customer[r['customer_id']],r['order_placed_at'],r['order_status'],r['channel'],r['currency'],r['simulated']))
        order=mapping('orders','order_number','order_id')
        line_data={r['order_line_id']:r for r in lines}
        require(len(line_data)==len(lines), 'Duplicate order line')
        for r in lines:
            c.execute('INSERT INTO ghost.order_lines(order_id,product_id,quantity,unit_price,source_line_code) VALUES (%s,%s,%s,%s,%s)',(order[r['order_id']],product[r['sku']],r['quantity_ordered'],r['unit_price_usd'],r['order_line_id']))
        line=mapping('order_lines','source_line_code','order_line_id')
        allocated, shipped = Counter(), Counter()
        for r in read('fulfillment_allocations'):
            src=line_data[r['order_line_id']]
            require((src['order_id'],src['sku'])==(r['order_id'],r['sku']) and r['reservation_status']=='FULFILLED','Invalid allocation')
            q=int(r['quantity_reserved']); allocated[(r['order_id'],r['sku'],r['location_code'])]+=q
            c.execute('INSERT INTO ghost.allocations VALUES (%s,%s,%s,%s)',(line[r['order_line_id']],location[r['location_code']],q,r['reservation_status']))
        tasks, events = map(read, ('fulfillment_pick_tasks','fulfillment_events'))
        require(len(tasks)==25 and len(events)==100,'Unexpected task/event count')
        for r in tasks:
            c.execute('INSERT INTO ghost.pick_tasks VALUES (%s,%s,%s,%s,%s,%s,%s)',(r['pick_task_id'],order[r['order_id']],r['employee_id'],r['task_status'],r['estimated_route_ft'],r['estimated_pick_minutes'],r['route_method']))
        for r in events:
            c.execute('INSERT INTO ghost.fulfillment_events VALUES (%s,%s,%s,%s,%s)',(r['event_id'],order[r['order_id']],r['event_type'],r['occurred_at'],r['employee_id'] or None))
        for r in read('fulfillment_movements'):
            q=-int(r['quantity_delta']); require(q>0 and r['movement_type']=='SHIPMENT','Invalid shipment')
            shipped[(r['order_id'],r['sku'],r['location_code'])]+=q
            c.execute("INSERT INTO ghost.inventory_movements(product_id,from_location_id,quantity,movement_type,occurred_at,reference_type,reference_id) VALUES (%s,%s,%s,'SHIP',%s,'PILOT_SHIPMENT',%s)",(product[r['sku']],location[r['location_code']],q,r['occurred_at'],r['movement_id']))
        require(allocated==shipped and sum(shipped.values())==50,'Shipment reconciliation failed')
        for r in outcomes:
            c.execute('UPDATE ghost.orders SET status=%s WHERE order_id=%s',(r['status'],order[r['order_id']]))
        actual=balances()
        require(actual=={(r['sku'],r['location_code']):int(r['ending_quantity']) for r in expected} and min(actual.values())>=0 and sum(actual.values())==19820,'Ending inventory reconciliation failed')
        c.execute("INSERT INTO ghost.pilot_imports(batch_id) VALUES ('pilot-2026-11-23')")
    print('Pilot committed: 25 shipped orders, 50 units shipped, 19820 units remaining.')

if __name__=='__main__':
    main()
