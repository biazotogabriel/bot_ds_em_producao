import pandas as pd
import json
import requests
from flask import Flask, request, Response

TOKEN = '6286526193:AAETd6pMQKyrpRlEJV9Sjn6VYDuR3dLStdk'

# info about the bot
update_bot_url = 'https://api.telegram.org/bot6286526193:AAETd6pMQKyrpRlEJV9Sjn6VYDuR3dLStdk/getUpdates'
#setwebhook
webhook_bot_url = 'https://api.telegram.org/bot6286526193:AAETd6pMQKyrpRlEJV9Sjn6VYDuR3dLStdk/setWebhook?url=https://72b5789292f935.lhr.life/' #using localhost.run
# info about the bot
info_bot_url = 'https://api.telegram.org/bot6286526193:AAETd6pMQKyrpRlEJV9Sjn6VYDuR3dLStdk/getMe'

def parse_message(message):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    store_id = store_id.replace('/', '')
    try:
        store_id = int(store_id)
    except ValueError:
        store_id = 'error'
    return chat_id, store_id

def load_dataset(sotre_id):   
    df_test_raw = pd.read_csv('datasets/test.csv')
    df_stores_raw = pd.read_csv('datasets/store.csv')
    df_test = df_test_raw.merge(df_stores_raw, how='left', on='Store')
    #choose store for prediction
    df_test = df_test[df_test['Store'] == sotre_id]
    if not(df_test.empty):
        df_test = df_test[df_test['Open'] != 0]
        df_test = df_test[~df_test['Open'].isnull()]
        df_test = df_test.drop('Id', axis=1)
        data = json.dumps(df_test.to_dict(orient='records'))
    else:
        data = 'error'
    return data

def predict(data):
    #API Call
    url = 'https://ds-em-producao-deploy.onrender.com/rossmann/predict'
    header = {'Content-type': 'application/json'}
    r = requests.post(url, data=data, headers=header)
    print('Status Code {}'.format(r.status_code))
    d1 = pd.DataFrame(r.json(), columns=r.json()[0].keys())
    return d1

def send_message(chat_id, text):
    #API Call
    url = f'https://api.telegram.org/bot{TOKEN}/sendMessage'
    data = {'chat_id': chat_id,
            'text': text}
    r = requests.post(url, data=data)
    print('Status Code {}'.format(r.status_code))
    return None

# api initialize
app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    print(request.get_json())
    if request.method == 'POST':
        message = request.get_json()
        chat_id, message = parse_message(message)
        if message != 'error':
            data = load_dataset(message)
            if data != 'error':
                d1 = predict(data)
                d2 = d1[['store', 'prediction']].groupby('store').sum().reset_index()

                msg = 'Loja número {} venderá R$ {:,.2f} nas próximas 6 semanas'.format(
                        d2['store'].values[0],
                        d2['prediction'].values[0])
                # calculation
                send_message(chat_id, msg)
                return Response('OK', status=200)
            else:
                send_message(chat_id, 'Loja não existe')
                return Response('OK', status=200)
        else:
            send_message(chat_id, 'Código da loja inválido')
            return Response('OK', status=200)
    else:
        return '<h1>Rossmann Telegram BOT</h1>'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)


