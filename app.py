import streamlit as st
import datetime
import random
import requests
import json
import pandas as pd
from bidict import bidict

page = st.sidebar.selectbox('Choose your page', ['users', 'rooms', 'bookings'])

if page == 'users':
    st.title("ユーザ登録画面")

    with st.form(key='user'):
        # user_id: int = random.randint(0, 10)
        user_name: str = st.text_input('ユーザ名', max_chars=12)

        data = {
            'user_name': user_name 
        }
        submit_button = st.form_submit_button(label='ユーザ登録')

    if submit_button:
        st.write('## レスポンス結果')
        url = "http://127.0.0.1:8000/users"
        res = requests.post(
            url, 
            data=json.dumps(data)
        )
        if res.status_code == 200:
            st.success("ユーザ登録完了")
        st.write(res.status_code)
        st.json(res.json())
elif page == 'rooms':

    st.title("会議室登録画面")

    with st.form(key='room'):
        room_name: str = st.text_input('会議室名', max_chars=12)
        capacity: int = st.number_input('定員', step=1)

        data = {
            'room_name': room_name,
            'capacity': capacity 
        }
        submit_button = st.form_submit_button(label='会議室登録')

    if submit_button:
        st.write('## 送信データ')
        st.json(data)
        st.write('## レスポンス結果')
        url = "http://127.0.0.1:8000/rooms"
        res = requests.post(
            url, 
            data=json.dumps(data)
        )
        if res.status_code == 200:
            st.success("会議室登録完了")
        st.write(res.status_code)
        st.json(res.json())
elif page == 'bookings':

    st.title("会議室予約画面")

    # ユーザ一覧取得
    url_users = "http://127.0.0.1:8000/users"
    res = requests.get(url_users)
    users = res.json()
    users_dict = bidict()
    for user in users:
        users_dict[user["user_name"]] = user["user_id"]
    
    # 会議室一覧取得
    url_rooms = "http://127.0.0.1:8000/rooms"
    res = requests.get(url_rooms)
    rooms = res.json()
    rooms_dict = dict()
    for room in rooms:
        rooms_dict[room["room_name"]] = {
            "room_id": room["room_id"],
            "capacity": room["capacity"]
        }
    room_id_dict = bidict()
    for room in rooms:
        room_id_dict[room["room_name"]] = room["room_id"]

    # IDを各値に変更
    ### bidict.inverseでvalue(user_id)=>key(user_name)に変換。room_nameも同様。
    to_user_name = lambda x: users_dict.inverse[x]
    to_room_name = lambda x: room_id_dict.inverse[x]
    to_datetime = lambda x: datetime.datetime.fromisoformat(x).strftime('%Y/%m/%d %H:%M')

    # 予約一覧取得
    url_bookings = "http://127.0.0.1:8000/bookings"
    res = requests.get(url_bookings)
    bookings = res.json()
    df_bookings = pd.DataFrame(bookings)
    df_bookings['user_id'] = df_bookings['user_id'].map(to_user_name)
    df_bookings['room_id'] = df_bookings['room_id'].map(to_room_name)
    df_bookings['start_datetime'] = df_bookings['start_datetime'].map(to_datetime)
    df_bookings['end_datetime'] = df_bookings['end_datetime'].map(to_datetime)
    df_bookings.columns = ["予約者名名", "会議室名", "予約人数", "開始時刻", "終了時刻", "予約番号"]

    ## 予約画面
    st.write("### 会議室一覧")
    df_rooms = pd.DataFrame(rooms)
    df_rooms.columns=["会議室名", "定員", "会議室ID"]
    st.table(df_rooms)

    st.write("### 予約一覧")
    st.table(df_bookings)


    with st.form(key='booking'):

        user_name: str = st.selectbox("予約者名", users_dict.keys())
        room_name: str = st.selectbox("会議室名", rooms_dict.keys())
        booked_num: int = st.number_input('予約人数', step=1, min_value=1)
        date: datetime.date =  st.date_input('日付を入力', min_value=datetime.date.today())
        start_time: datetime.time =  st.time_input('開始時刻: ', value=datetime.time(hour=9, minute=0))
        end_time: datetime.time =  st.time_input('終了時刻: ', value=datetime.time(hour=20, minute=0))
        submit_button = st.form_submit_button(label='予約登録')

    if submit_button:
        user_id = users_dict[user_name]
        room_id = rooms_dict[room_name]["room_id"]
        capacity = rooms_dict[room_name]["capacity"]

        data = {
            'user_id': user_id,
            'room_id': room_id,
            'booked_num': booked_num,
            'start_datetime': datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=start_time.hour,
                minute=start_time.minute
            ).isoformat(),
            'end_datetime': datetime.datetime(
                year=date.year,
                month=date.month,
                day=date.day,
                hour=end_time.hour,
                minute=end_time.minute
            ).isoformat()
        }
        # 予約人数が定員より多い場合
        if booked_num > capacity:
            st.error(f"{room_name}の定員は、{capacity}名です。{capacity}名以下の定員人数のみ受け付けております")
        # 開始時刻 >= 終了時刻
        elif start_time >= end_time:
            st.error("開始時刻が終了時刻を超えています")
        # 開始時刻 < 9:00 or 20:00 < 終了時刻
        elif start_time < datetime.time(hour=9, minute=0, second=0) or end_time > datetime.time(hour=20, minute=0, second=0):
            st.error("利用時間は9:00～20:00になります")
        else:
            st.write('## 送信データ')
            st.json(data)
            st.write('## レスポンス結果')
            url = "http://127.0.0.1:8000/bookings"
            res = requests.post(
                url, 
                data=json.dumps(data)
            )
            if res.status_code == 200:
                st.success("予約完了しました")
            elif res.status_code == 404 and res.json()["detail"] == "Already booked":
                st.error("指定の時間にはすでに予約が入っています")