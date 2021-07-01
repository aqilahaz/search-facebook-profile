from flask import Flask, request, stream_with_context, Response
from flask_restful import Resource, Api
import timeline
from datetime import datetime
import mysql.connector
from timeline import SearchUser
from config import accountfacebook

app = Flask(__name__)
api = Api(app)

@app.route('/')
#test server
def index():
    return 'Server works!'

@app.route('/user', methods=['POST','GET'])
#example usage http://127.0.0.1:5000/user?name=Aqila, default name *
def get_query():
    if request.method == 'GET':
        input_name = request.args.get('name', type=str, default='*')
        SearchUser0 = SearchUser(accountfacebook.EMAIL,accountfacebook.PWD)
        SearchUser0.check_cookies()
        SearchUser0.search_people(input_name)
        result = SearchUser0.get_profil()
        sql = "INSERT INTO `facebook` (`url`,`nama`, `keterangan`, `gambar`) VALUES (%(links)s, %(names)s, %(notes)s, %(picture)s )"
        cur, mydb = SearchUser0.init_db()
        cur.executemany(sql, result)
        mydb.commit()
        print(cur.rowcount, "record inserted")
        cur.close()
        return 'Hello : {name}'.format(name=input_name)

if __name__ == "__main__":
    app.run(debug=True)
