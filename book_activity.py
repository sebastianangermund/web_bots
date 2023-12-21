import requests
import json

from datetime import datetime

from secret import password, domain


def get_booking_timestamps(booking_times):
    today = datetime.utcnow()
    booking_day = today.replace(day=today.day+6)
    timestamps = []
    for booking_time in booking_times:
        hour, minute, second = booking_time.split(':')
        booking_time = booking_day.replace(hour=int(hour), minute=int(minute), second=int(second), microsecond=0)
        timestamps.append(booking_time)
    return timestamps


def get_uuids(html):
    find_text = 'Boka sporthallen 30min'
    uuids = []
    while True:
        index = html.find(find_text)
        if index == -1:
            break
        uuids.append(html[index-39:index-3])
        html = html[index+len(find_text):]
    return uuids


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


def find_activity_id(session, booking_date, booking_open):
    id_location = '5e1c2e70-1090-41b5-a766-854c0a00022d'    # my location
    id_type = '618a65cd-4144-4ddc-85fa-002c0a10050f'        # relevant activity
    id_facility = '60a7ac3f-b774-4228-a9a3-056c0a10010d'    # relevant facility
    adr = f'https://{domain}/w_booking/activities/list?from={booking_date}&to={booking_date}&today=0&location={id_location}&user=&mine=0&type={id_type}&only_try_it=0&facility={id_facility}'

    headers = {
        'Accept': 'application/json',
    }
    response = session.get(adr, headers=headers)
    print('FETCH STATUS: ', response.status_code)
    resp_string = response.text
    resp_dict = json.loads(resp_string)
    activities = resp_dict['activities']
    # print(json.dumps(resp_dict, indent=4, sort_keys=True))
    for activity in activities:
        for key, value in activity.items():
            if key == "Activity":
                # print(key, value, '\n')
                id = value['id']
                start_time = value['start']
                # print('CANDIDATE: ', id, start_time, '\n')
                activity_date, activity_time = start_time.split()
                if booking_date == activity_date and booking_open == activity_time:
                    print('BOOKING ID FOUND: ', id, '\n')
                    id_activity = id
    return id_activity


def book_activity(id_booking, session, timestamps):
    headers = {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'Referer': f'https://{domain}/schema'
    }
    booking_address = f'https://{domain}/w_booking/activities/participate/{id_booking}/?force=1'
    for timestamp in timestamps:
        if not timestamp:
            continue
        payload = {"ActivityBooking": {"book_start": str(int(timestamp.timestamp())), "book_length": "30", "extras": {}, "resources": {}, "participants": 1}}
        response = session.post(booking_address, data=payload, headers=headers)
        print(f'BOOKING STATUS {timestamp}: ', response.status_code)
        print(response.headers)
        print(response.text)


def main():
    # setup
    username = 'sebastian.angermund@seb.se'
    booking_times = ['18:00:00']
    timestamps = get_booking_timestamps(booking_times)
    print(timestamps[0].timestamp())
    booking_date = timestamps[0].strftime('%Y-%m-%d')
    booking_open = '13:00:00'

    # run session
    session = get_session(username, password)
    id_activity = find_activity_id(session, booking_date, booking_open)
    print('ACTIVITY ID: ', id_activity, '\n')
    book_activity(id_activity, session, timestamps)


if __name__ == '__main__':
    main()
