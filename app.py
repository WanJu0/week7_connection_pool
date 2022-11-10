import mysql.connector
from mysql.connector.pooling import MySQLConnectionPool
connection_pool = mysql.connector.pooling.MySQLConnectionPool(
    user='root',
    password='',
    host='127.0.0.1',
    database='website',
    pool_name = "week8_pool",
    pool_size = 32,
    pool_reset_session = True,
)
from flask import *
app=Flask(
    __name__,
    static_folder="static",
    static_url_path="/"
)
app.secret_key="any string but secret"
import json
from flask import jsonify

# 處理路由
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/member")
def member():
    if "name" in session:
        # 向connection pool 請求連接需使用get_connection()方法
        connection_object = connection_pool.get_connection()
        mycursor = connection_object.cursor()
        sql = "SELECT \
        member.name AS user, \
        message.content AS message \
        FROM member \
        INNER JOIN message ON member.id = message.member_id"
        mycursor.execute(sql)
        result = mycursor.fetchall()
        data=[]
        print(session["id"])  
        for i in range(0,len(result),1):
            data.append(result[i][0]+":"+result[i][1])
        mycursor.close()
        connection_object.close()
        return render_template("member.html",name=session["nickname"],data=data)
    else:
        return redirect("/")
    print(session["id"]) 

@app.route("/error")
def error():
    message=request.args.get("message","發生錯誤,請聯繫客服")
    return render_template("error.html",message=message)

@app.route("/signin",methods=["POST"])    
def signin():
    name=request.form["name"]
    password=request.form["password"]

    if name=="":
        return redirect("/error?message=請輸入帳號、密碼")
    if password=="":
        return redirect("/error?message=請輸入帳號、密碼")
    # 和資料庫做互動
    connection_object = connection_pool.get_connection()
    mycursor = connection_object.cursor()
    # 檢查帳號密碼是否正確
    mycursor.execute('SELECT * FROM member WHERE username=%s AND password =%s' ,(name, password))
    result = mycursor.fetchone()
    print(result)
    if result==None:
        mycursor.close()
        connection_object.close()
        return redirect("/error?message=帳號或密碼輸入錯誤")
    session["nickname"]=result[1]
    session["name"]=result[2]
    session["id"]=result[0]
    mycursor.close()
    connection_object.close()
    return redirect("/member")

@app.route("/signout")
def signout():
    del session["name"]
    return redirect("/")


@app.route("/signup",methods=["POST"])
def signup():
    # 從前端接收資料
    nickname=request.form["nickname"]
    name=request.form["name"]
    password=request.form["password"]
    #註冊帳號密碼不能為空
    if nickname=="":
        return redirect("/error?message=請輸入註冊內容")
    if name=="":
        return redirect("/error?message=請輸入註冊內容")
    if password=="":
        return redirect("/error?message=請輸入註冊內容")
    # 和資料庫做互動
    connection_object = connection_pool.get_connection()
    mycursor = connection_object.cursor()
    # 檢查姓名 帳號是否存在
    mycursor.execute('SELECT * FROM member WHERE name=%s or username =%s' ,(nickname, name))
    result = mycursor.fetchone()
    print(result)
    # 根據接收到的資料 和資料庫互動
    
    if result != None:
        mycursor.close()
        connection_object.close()
        return redirect("/error?message=信箱已經被註冊")
    # 把資料放進資料庫 完成註冊
    mycursor.execute("INSERT INTO member (name, username, password ) VALUES (%s, %s, %s)" ,(nickname,name,password))
    connection_object.commit()
    print(mycursor.rowcount, "record inserted.")
    mycursor.close()
    connection_object.close()
    return redirect("/")

@app.route("/message",methods=["POST"])
def message():
    message=request.form["message"]
    connection_object = connection_pool.get_connection()
    mycursor = connection_object.cursor()
    mycursor.execute("INSERT INTO message (member_id,content ) VALUES (%s, %s)" ,(session["id"],message))
    connection_object.commit()
    print(mycursor.rowcount, "record inserted.")
    mycursor.close()
    connection_object.close()
    return redirect("/member")

@app.route("/api/member",methods=["GET"])
def api_member():
    data={}
    name = request.args.get("username","請輸入查詢會員名稱")
    connection_object = connection_pool.get_connection()
    mycursor = connection_object.cursor()
    mycursor.execute("SELECT * FROM member WHERE username=%s",(name,))
    result = mycursor.fetchone()
    if result != None:
        data={
            "data": {
                "id":result[0],
                "name":result[1],
                "username":result[2]
            }
        }
    else:
        data={
            "data": None
        }
    json_result=jsonify(data)
    mycursor.close()
    connection_object.close()
    return json_result

@app.route("/api/member",methods=["PATCH"])
def api_update():
    if "name" in session:
        
        print(session["name"])
        # 用json格式
        data = request.get_json()
        response = make_response(jsonify(data,200))
        connection_object = connection_pool.get_connection()
        mycursor = connection_object.cursor()
        mycursor.execute("UPDATE member SET name=%s WHERE id=%s",(data["name"],session["id"]))
        connection_object.commit()
        print(mycursor.rowcount, "record affected")
        data={
            "ok":True
        }
        json_result=jsonify(data)
        mycursor.close()
        connection_object.close()
    else:
        data={
            "error":True
        }
        json_result=jsonify(data)
    return json_result

app.run(port=3000)