# -*- coding: utf-8 -*-
"""
Created on Mon May 18 2020
BoxのPython版SDKで、個別処理しなくてもトークン更新が行われAPI実行されることを確認するためのプログラム

"""

from boxsdk import OAuth2, Client
import webbrowser
import http.server
import socketserver
import csv
import os
from urllib.parse import urlparse, parse_qs

# BOXの管理画面から取ってくる
CLIENT_ID = ''
CLIENT_SECRET = ''

# BOXの管理画面に設定する
REDIRECT_URI = 'http://localhost:8080'

TOKEN_FILE = 'c:/temp/PyBoxTokens.csv'
ACCESS_TKN = ''
REFRESH_TKN = ''

HOST = '127.0.0.1'
PORT = 8080

# BOXが発行する認証コードを入れる変数
global auth_code

auth_code = None

# トークン生成用メソッドを集めたクラス    
class generate_token:
    
    def __init__(self, token_file, access_token, refresh_token):
        self.token_file = token_file
        self.access_token = access_token
        self.refresh_token = refresh_token
    
    def read_tokens(self):
        with open(self.token_file, 'r') as csv_file_read:
            reader = csv.DictReader(csv_file_read)
            for row in reader:
                self.access_token = row['access_token']
                self.refresh_token = row['refresh_token']
        return self.access_token, self.refresh_token
    
    def save_tokens(self, access_token, refresh_token):
        with open(self.token_file, 'w', newline="") as csv_file_write:
            fieldnames = ['access_token','refresh_token']
            writer = csv.DictWriter(csv_file_write, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerow({'access_token': access_token, 'refresh_token': refresh_token})
        print('access_token is {0}'.format(access_token))
        print('refresh_token is {0}'.format(refresh_token))
        
# メイン処理
TOKENS = generate_token(TOKEN_FILE, ACCESS_TKN, REFRESH_TKN)

# トークンを保管したファイルがあれば読み込んでOauthクラスインスタンス生成
# ここで、前回実行から60分以上経っていたら自動的にトークンリフレッシュが走り、トークン保管ファイルが更新されるはず！！
if(os.path.exists(TOKEN_FILE)):    
    ACCESS_TKN, REFRESH_TKN = TOKENS.read_tokens()
    oauth = OAuth2(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        access_token = ACCESS_TKN,
        refresh_token = REFRESH_TKN,
        store_tokens = TOKENS.save_tokens
        )
    
else:
    # 無ければ新たにOauｔｈ開始
    oauth = OAuth2(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        access_token = None,
        refresh_token = None,
        store_tokens = TOKENS.save_tokens
        )
        
    # OAuth開始
    auth_url, csrf_token = oauth.get_authorization_url(REDIRECT_URI)

    # ブラウザ起動してBOXのIDとパスワードを入力する
    # 入力するとREDIRECT_URIにリダイレクトされる
    webbrowser.open(auth_url)

    # REDIRECT_URIが叩かれた時の処理
    class ServerHandler(http.server.SimpleHTTPRequestHandler):
        def do_GET(self):
            global auth_code
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(b"<h1>Authenticated</h1>")
            parsed_path = urlparse(self.path)
            query = parse_qs(parsed_path.query)
            auth_code = query['code'][0]

    with socketserver.TCPServer((HOST, PORT), ServerHandler) as server:
        print('http server start')
        # server.serve_forever()    # Ctrl+Cが押されるなどの割り込みがあるまで処理し続ける
        server.handle_request()     # １回リクエストを処理したら抜ける
        print('http server shutdown')
    
    # auth_codeが取れたので、ここからAPIが使える
    ACCESS_TKN, REFRESH_TKN = oauth.authenticate(auth_code)

# API実行(ユーザID取得)
client = Client(oauth)
me = client.user().get()
print('My user ID is {0}'.format(me.id))