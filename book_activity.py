import requests
import json
import secret

from datetime import datetime
from config import domain


def get_booking_timestamps(booking_times, booking_day):
    timestamps = []
    for booking_time in booking_times:
        hour, minute, second = booking_time.split(':')
        booking_time = booking_day.replace(hour=int(hour), minute=int(minute), second=int(second), microsecond=0)
        timestamps.append(booking_time)
    return timestamps


def get_session(username, password):
    login_data = {
        '_method': 'POST',
        'data[User][email]': username,
        'data[User][password]': password
    }
    session = requests.Session()
    response = session.post(f'https://{domain}', data=login_data)
    if response.status_code != 200:
        raise Exception('Login failed with status code: ', response.status_code)
    return session


def find_activity_id(session, booking_date, booking_opens):
    id_location = '5e1c2e70-1090-41b5-a766-854c0a00022d'    # my location
    id_type = '618a65cd-4144-4ddc-85fa-002c0a10050f'        # relevant activity
    id_facility = '60a7ac3f-b774-4228-a9a3-056c0a10010d'    # relevant facility
    adr = f'https://{domain}/w_booking/activities/list?from={booking_date}&to={booking_date}&today=0&location={id_location}&user=&mine=0&type={id_type}&only_try_it=0&facility={id_facility}'

    headers = {
        'Accept': 'application/json',
    }
    response = session.get(adr, headers=headers)
    if response.status_code != 200:
        raise Exception('find_activity_id failed with status code: ', response.status_code)
    resp_string = response.text
    resp_dict = json.loads(resp_string)
    activities = resp_dict['activities']
    for activity in activities:
        for key, value in activity.items():
            if key == "Activity":
                id = value['id']
                start_time = value['start']
                activity_date, activity_time = start_time.split()
                if booking_date == activity_date and booking_opens == activity_time:
                    print('BOOKING ID FOUND: ', id, '\n')
                    id_activity = id
    return id_activity


def book_activity(id_booking, session, timestamps):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Referer': f'https://{domain}/schema'
    }
    address_pre_booking = f'https://{domain}/w_booking/activities/participate/{id_booking}?pre=1'
    address_booking = f'https://{domain}/w_booking/activities/participate/{id_booking}/?force=1'
    for timestamp in timestamps:
        if not timestamp:
            continue
        payload = {"ActivityBooking": {"book_start": str(int(timestamp.timestamp())), "book_length": "30", "participants": 1}}
        response_pre_booking = session.post(address_pre_booking, json=payload, headers=headers)
        print(f'PRE BOOKING STATUS {timestamp}: ', response_pre_booking.status_code)
        response_booking = session.post(address_booking, json=payload, headers=headers)
        print(f'BOOKING STATUS {timestamp}: ', response_booking.status_code)
        print(response_booking.headers)
        print(response_booking.text)


def main(booking_times, booking_day, booking_opens, username, password):
    # setup booking
    timestamps = get_booking_timestamps(booking_times, booking_day)
    booking_date = timestamps[0].strftime('%Y-%m-%d')
    # run session
    session = get_session(username, password)
    id_activity = find_activity_id(session, booking_date, booking_opens)
    book_activity(id_activity, session, timestamps)


if __name__ == '__main__':
    # setup credentials
    username = secret.login['username']
    password = secret.login['password']
    # setup booking date and times
    today = datetime.utcnow()
    days_until_booking = 3
    booking_opens = '13:00:00'
    booking_day = today.replace(day=today.day+days_until_booking, hour=0, minute=0, second=0, microsecond=0)
    booking_times = ['13:00:00', '13:30:00']
    main(booking_times, booking_day, booking_opens, username, password)
