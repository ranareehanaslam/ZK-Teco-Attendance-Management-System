from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional, List, Dict
from datetime import datetime
from zk import ZK
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from starlette.concurrency import run_in_threadpool
from collections import defaultdict

def calculate_total_minutes(check_in, check_out):
    if check_in and check_out:
        return int((check_out - check_in).total_seconds() / 60)
    return 0

app = FastAPI()

# Global data structures
user_info_global = {}
attendance_records_global = []



@app.get("/")
async def read_index():
    return FileResponse('index.html')

# Utility functions for fetching attendance records
def fetch_attendance_by_month(records, year, month):
    return [record for record in records if record.timestamp.year == year and record.timestamp.month == month]

## PDF generation logic centralized
def generate_attendance_pdf(attendance, user_id_list, title):
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=landscape(letter), rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=18)
    styles = getSampleStyleSheet()
    elements = [Paragraph(f"Attendance Report - {title}", styles['Title'])]

    # If user_id_list is provided, filter the attendance records
    if user_id_list:
        attendance = [record for record in attendance if str(record.user_id) in user_id_list]

    all_dates = sorted(set(record.timestamp.strftime('%Y-%m-%d') for record in attendance))
    date_chunks = [all_dates[i:i + 8] for i in range(0, len(all_dates), 8)]

    # Prepare data
    user_attendance = {user_id: {date: {'check-in': None, 'check-out': None} for date in all_dates} for user_id in user_id_list}
    user_total_minutes = {user_id: 0 for user_id in user_id_list}  # Total minutes spent

    for record in attendance:
        date_key = record.timestamp.strftime('%Y-%m-%d')
        user_id = str(record.user_id)
        if user_id in user_attendance:
            if user_attendance[user_id][date_key]['check-in'] is None or record.timestamp < user_attendance[user_id][date_key]['check-in']:
                user_attendance[user_id][date_key]['check-in'] = record.timestamp
            if user_attendance[user_id][date_key]['check-out'] is None or record.timestamp > user_attendance[user_id][date_key]['check-out']:
                user_attendance[user_id][date_key]['check-out'] = record.timestamp

    # Calculate total minutes
    for user_id, dates in user_attendance.items():
        total_minutes = 0
        for date, times in dates.items():
            if times['check-in'] and times['check-out']:
                total_minutes += int((times['check-out'] - times['check-in']).total_seconds() / 60)
        user_total_minutes[user_id] = total_minutes

    elements.append(Paragraph("Attendance Report - Generated on " + datetime.now().strftime("%Y-%m-%d %H:%M"), styles['Title']))

    # Generate tables for each user
    for user_id, dates in user_attendance.items():
        elements.append(Paragraph(f"ID: {user_id}, Username: {user_info_global.get(user_id, 'Unknown')}, Total Minutes Spent: {user_total_minutes[user_id]}", styles['Heading2']))

        for date_chunk in date_chunks:
            data = [['Date'] + date_chunk]
            row = ['Check-in/Check-out']
            for date in date_chunk:
                check_in = dates[date]['check-in'].strftime('%I:%M%p').lstrip('0').replace('AM', 'am').replace('PM', 'pm') if dates[date]['check-in'] else '--'
                check_out = dates[date]['check-out'].strftime('%I:%M%p').lstrip('0').replace('AM', 'am').replace('PM', 'pm') if dates[date]['check-out'] else '--'
                row.append(f"{check_in}/{check_out}")
            data.append(row)
            table = Table(data)
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ]))
            elements.append(table)

    doc.build(elements)
    pdf_buffer.seek(0)
    return pdf_buffer

# FastAPI endpoints
@app.get("/download-attendance/{time_period}", response_class=StreamingResponse)
async def download_attendance_pdf(time_period: str, user_ids: Optional[str] = Query(None)):
    # Handle time period logic
    now = datetime.now()
    if time_period == "current-month":
        attendance = fetch_attendance_by_month(attendance_records_global, now.year, now.month)
    elif time_period == "last-month":
        last_month = now.month - 1 if now.month > 1 else 12
        last_month_year = now.year if now.month > 1 else now.year - 1
        print(last_month)
        print(last_month_year)
        attendance = fetch_attendance_by_month(attendance_records_global, last_month_year, last_month)
    else:
        attendance = attendance_records_global

    # Handle user IDs
    user_id_list = user_ids.split(',') if user_ids else [str(user_id) for user_id in user_info_global.keys()]

    pdf_buffer = generate_attendance_pdf(attendance, user_id_list, time_period.replace('-', ' ').title())
    filename = f"attendance_report_{time_period}.pdf"
    return StreamingResponse(pdf_buffer, media_type="application/pdf", headers={'Content-Disposition': f'attachment;filename={filename}'})

# Simplified endpoint for refreshing users
@app.get("/refresh_users")
async def refresh_users():
    zk = ZK('192.168.100.253', port=4370, timeout=50)
    try:
        conn = await run_in_threadpool(zk.connect)
        users = await run_in_threadpool(conn.get_users)
        global user_info_global
        user_info_global = {str(user.user_id): user.name for user in users}
        await run_in_threadpool(conn.disconnect)
        return {"status": "success", "users": user_info_global}
    except Exception as exc:
        return {"status": "failed", "reason": str(exc)}
    
@app.get("/get_users")
async def refresh_users():
    try:
        return {"status": "success", "users": user_info_global}
    except Exception as exc:
        return {"status": "failed", "reason": str(exc)}


def fetch_last_two_months_attendance(attendance_records):
    now = datetime.now()
    current_year, current_month = now.year, now.month
    previous_month = current_month - 1 if current_month > 1 else 12
    previous_year = current_year if current_month > 1 else current_year - 1

    return [record for record in attendance_records if 
            ((record.timestamp.year == current_year and record.timestamp.month == current_month) or 
            (record.timestamp.year == previous_year and record.timestamp.month == previous_month))]

# Endpoint to display formatted attendance
@app.get("/refresh-attendance", response_model=List[Dict[str, str]])
async def refresh_attendance():
    zk = ZK('192.168.100.253', port=4370, timeout=900)
    try:
        conn = await run_in_threadpool(zk.connect)
        attendance_records = await run_in_threadpool(conn.get_attendance)
        global attendance_records_global
        attendance_records_global = fetch_last_two_months_attendance(attendance_records)
        await run_in_threadpool(conn.disconnect)
        return [{"user_id": str(record.user_id), "check-in": record.timestamp.strftime('%Y-%m-%d %I:%M%p'), "check-out": record.timestamp.strftime('%Y-%m-%d %I:%M%p')} for record in attendance_records_global]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))




@app.get("/user-attendance/{user_id}")
async def get_user_attendance(user_id: str, time_period: Optional[str] = Query("current-month")):
    now = datetime.now()
    target_year, target_month = now.year, now.month

    if time_period == "last-month":
        target_month = now.month - 1 if now.month > 1 else 12
        target_year = now.year if now.month > 1 else now.year - 1

    # Filter records for the specified month and user
    attendance_internal=[{"user_id": str(record.user_id), "check-in": record.timestamp.strftime('%Y-%m-%d %I:%M%p'), "check-out": record.timestamp.strftime('%Y-%m-%d %I:%M%p')} for record in attendance_records_global]
    filtered_records = [record for record in attendance_internal
                        if datetime.strptime(record['check-in'], '%Y-%m-%d %I:%M%p').year == target_year and
                        datetime.strptime(record['check-in'], '%Y-%m-%d %I:%M%p').month == target_month and
                        record['user_id'] == user_id]

    # Sort records by time to calculate duration
    filtered_records.sort(key=lambda x: datetime.strptime(x['check-in'], '%Y-%m-%d %I:%M%p'))

    # Calculate total minutes
    total_minutes = 0
    last_timestamp = None
    for i in range(len(filtered_records) - 1):
        check_in_time = datetime.strptime(filtered_records[i]['check-in'], '%Y-%m-%d %I:%M%p')
        check_out_time = datetime.strptime(filtered_records[i + 1]['check-out'], '%Y-%m-%d %I:%M%p')
        if last_timestamp and last_timestamp != check_in_time:
            total_minutes += (check_out_time - check_in_time).total_seconds() / 60

        last_timestamp = check_out_time

    # User information
    user_info = user_info_global.get(user_id, "Unknown")

    # Format response
    records = [{
        "date": rec['check-in'].split(' ')[0],
        "check_in": rec['check-in'],
        "check_out": rec['check-out']
    } for rec in filtered_records]

    return {
        "user_id": user_id,
        "username": user_info,
        "total_minutes": int(total_minutes),
        "records": records
  }
