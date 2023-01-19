import streamlit as st
import random
import requests
import json
import datetime
import pandas as pd

page = st.sidebar.selectbox('Choose your page',['users', 'rooms', 'bookings'])

if page == 'users':
    st.title("ユーザー登録画面")

    with st.form(key = "user"):
        # user_id: int = random.randint(0, 10)
        username: str = st.text_input("ユーザー名", max_chars = 12)
        user_data = {
            # 'user_id': user_id,
            'username': username
        }
        submit_button = st.form_submit_button(label = 'ユーザー登録')

    # submit_buttonを押したら走る処理
    if submit_button:
        # st.write("## 送信データ")
        st.write("## レスポンス結果")
        url = "http://127.0.0.1:8000/users"
        res = requests.post(url, data = json.dumps(user_data))

        if res.status_code == 200:
            st.success('ユーザー登録完了')
        st.write(res.status_code)
        st.json(res.json())

elif page == 'rooms':
    st.title('会議室登録画面')

    with st.form(key = "room"):
        # room_id: int = random.randint(0, 10)
        room_name: str = st.text_input("room_name", max_chars = 12)
        capacity: int = st.number_input("capacity", step = 1)
        room_data = {
            # 'room_id': room_id,
            'room_name': room_name,
            'capacity': capacity
        }
        submit_button = st.form_submit_button(label = "会議室登録")

    # submit_buttonを押したら走る処理
    if submit_button:
        st.write("## レスポンス結果")
        url = "http://127.0.0.1:8000/rooms"
        res = requests.post(url, data = json.dumps(room_data))
        if res.status_code == 200:
            st.success('会議室登録完了')
        st.write(res.status_code)
        st.json(res.json())

elif page == 'bookings':
    st.title('会議室予約画面')

    # ユーザー一覧取得
    get_users_url = 'http://127.0.0.1:8000/users'
    res = requests.get(get_users_url)
    users = res.json()
    users_name = {}
    for user in users:
        users_name[user['username']] = user['user_id']


    # 会議室一覧取得
    get_rooms_url = 'http://127.0.0.1:8000/rooms'
    res = requests.get(get_rooms_url)
    rooms = res.json()
    rooms_name = {}
    for room in rooms:
        rooms_name[room['room_name']] = {
            'room_id': room['room_id'],
            'capacity': room['capacity']
        }

    st.write('### 会議室一覧')
    df_rooms = pd.DataFrame(rooms)
    df_rooms.columns = ['会議室名', '定員', '会議室ID']
    st.table(df_rooms)


    # 予約一覧取得
    get_bookings_url = 'http://127.0.0.1:8000/bookings'
    res = requests.get(get_bookings_url)
    bookings = res.json()
    df_bookings = pd.DataFrame(bookings)

    users_id = {}
    for user in users:
        users_id[user['user_id']] = user['username']

    rooms_id = {}
    for room in rooms:
        rooms_id[room['room_id']] = {
            'room_name': room['room_name'],
            'capacity': room['capacity'],
        }

    # IDを書く値に変更
    to_username = lambda x: users_id[x]
    to_room_name = lambda x: rooms_id[x]['room_name'] 
    to_datetime = lambda x: datetime.datetime.fromisoformat(x).strftime('%y/%m/%d %H:%M') 

    # 特定の列にlambda関数を適用
    df_bookings['user_id'] = df_bookings['user_id'].map(to_username)
    df_bookings['room_id'] = df_bookings['room_id'].map(to_room_name)
    df_bookings['start_datetime'] = df_bookings['start_datetime'].map(to_datetime)
    df_bookings['end_datetime'] = df_bookings['end_datetime'].map(to_datetime)
    
    df_bookings = df_bookings.rename(columns={
        'user_id': '予約者名',
        'room_id': '会議室名',
        'booked_num': '予約人数',
        'start_datetime': '開始時刻',
        'end_datetime': '終了時刻',
        'booking_id': '予約ID'
    })

    st.write('### 予約一覧')
    st.table(df_bookings)



    with st.form(key = "booking"):
        username: str = st.selectbox('予約者', users_name.keys())
        room_name: str = st.selectbox('会議室', rooms_name.keys())
        booked_num: int = st.number_input('予約人数', step = 1, min_value = 1)
        date: datetime.date = st.date_input('日付:', min_value = datetime.date.today())
        start_time: datetime.datetime = st.time_input('開始時間:',value = datetime.time(hour = 9, minute = 0))
        end_time: datetime.datetime = st.time_input('終了時間:',value = datetime.time(hour = 20, minute = 0))
        submit_button = st.form_submit_button(label = "予約")

    # submit_buttonを押したら走る処理
    if submit_button:
        user_id: int = users_name[username]
        room_id: int = rooms_name[room_name]['room_id']
        capacity: int = rooms_name[room_name]['capacity']

        booking_data = {
            'user_id': user_id,
            'room_id': room_id,
            'booked_num': booked_num ,
            'start_datetime': datetime.datetime(
                year = date.year,
                month = date.month,
                day = date.day,
                hour = start_time.hour,
                minute = start_time.minute
            ).isoformat(),
            'end_datetime': datetime.datetime(
                year = date.year,
                month = date.month,
                day = date.day,
                hour = end_time.hour,
                minute = end_time.minute
            ).isoformat(),
        }

        # 定員を超えたとき
        if booked_num > capacity:
            st.error(f'{room_name}の定員は{capacity}名です。予約人数が定員を超えています。')
        # 開始時刻が終了時刻より遅いとき
        elif start_time >= end_time:
            st.error('開始時刻が終了時刻を超えています。')
        # 利用時間が9時~20時以外のとき
        elif start_time < datetime.time(hour=9, minute=0, second=0) or end_time > datetime.time(hour=20, minute=0, second=0):
            st.error('利用時間は9:00~20:00です。')
        else:
            # 会議室予約処理
            url = "http://127.0.0.1:8000/bookings"
            res = requests.post(url, data = json.dumps(booking_data))
            if res.status_code == 200:
                st.success('予約完了')
            elif res.status_code == 404 and res.json()['detail'] == 'Already booked.' :
                st.error('指定の時刻に既に予約が入っています。')

            st.json(res.json())