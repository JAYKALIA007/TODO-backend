from urllib import response
from flask import Flask
from flask import jsonify
from flask import request
from flask_cors import CORS
from flask_pymongo import PyMongo
from uuid import uuid4
import hashlib
from queue import Queue
import datetime

q = Queue(maxsize = 10)
app = Flask(__name__)
CORS(app)
app.config["MONGO_URI"] = "mongodb://localhost:27017/User_db"   
app.config['MONGO_DBNAME'] = 'User_db'
mongo = PyMongo(app)

@app.route('/')
def hello_world():
    response = jsonify(message="Flask is running")
    response.headers.add("Access-Control-Allow-Origin", "*")
    return response


@app.route('/demoGet', methods=['GET'])
def demo_get():
    response = jsonify(message="Demo get request performed")
    return response

@app.route('/demoPost', methods=['POST'])
def demo_post():
    r=request.json
    print(r)
    response = jsonify(r)
    return response

@app.route('/demoPut',methods=['PUT'])    
def demo_put():
    r=request.json
    print(r)
    response=jsonify(r)
    return response

@app.route('/demoPatch',methods=['PATCH'])    
def demo_patch():
    r=request.json
    print(r)
    response=jsonify(r)
    return response

@app.route('/demoDelete',methods=['DELETE'])    
def demo_delete():
    response = jsonify(message="Demo delete request performed")
    return response       

@app.route('/addUser',methods=['POST']) 
def addUser():
    mycol = "users"
    try:
        userInfo = request.json   
        if mongo.db[mycol].find_one({"email": userInfo['email']}) :
            return jsonify("User already added")
        elif userInfo['firstName'] != '' and userInfo['lastName'] != '' and userInfo['email'] != '' and userInfo['password'] != '' :

            # SHA 256 encryption for password, store the hex equivalent as password
            myPassword = userInfo['password']
            result = hashlib.sha256(myPassword.encode())
            userInfo['password'] =result.hexdigest()
            # print(type(userInfo['password'])) #str
            mongo.db[mycol].insert_one(userInfo)
            return jsonify('User successfully added')
        else :
            return jsonify('Cannot add user, enter valid details')  
    except:
        return jsonify("Can't add empty user body")            

@app.route('/getUsers',methods=['GET'])
def getUsers():
    mycol = "users"
    userInfo =[]
    for i in mongo.db[mycol].find():
        user={}
        user['firstName'] = i["firstName"]
        user['lastName'] = i["lastName"]
        user['email'] = i["email"]
        user['password'] = i["password"]
        if 'todos' in i : 
            user['todos'] = i["todos"]
               
        userInfo.append(user)
    return jsonify(userInfo) 

@app.route('/editUser',methods=['PUT'])
def editUser():
       mycol = "users"
       user = request.json 
       userInfo ={} 
       result =  mongo.db[mycol].find_one({"email": user['email']}) 
       print(result)

       if result:
        #    changes will be done here
            userInfo = {}
            if 'firstName' in user:
                userInfo["firstName"] = user['firstName']
                userInfo["lastName"]= result['lastName']
                userInfo["email"]= result['email']
                userInfo["password"]= result['password']
            elif 'lastName' in user:
                userInfo["firstName"] = result['firstName']
                userInfo["lastName"]= user['lastName']
                userInfo["email"]= result['email']
                userInfo["password"]= result['password']
            elif 'password' in user:
                userInfo["firstName"] = result['firstName']
                userInfo["lastName"]= result['lastName']
                userInfo["email"]= result['email']
                userInfo["password"]= user['password']  

            if 'todos' in result:
                userInfo["todos"] = result['todos']
            mongo.db[mycol].update_one({"email":user['email']},{"$set":userInfo})
            resp=jsonify('User updated successfully!')
            return resp
       else:
            resp=jsonify("User doesn't exist!")
            return resp

@app.route('/deleteUser',methods=['DELETE'])
def deleteUser():
    mycol = "users"
    userInfo = request.json 
    result = mongo.db[mycol].find_one({'email':userInfo['email']})
    if result:
        mongo.db[mycol].delete_one({"email":userInfo['email']})
        resp=jsonify('User deleted!')
        print('user deleted successfully!')
        return resp
    else:
        resp=jsonify("User doesn't exist!")
        return resp

@app.route('/login',methods=['POST'])  
def login():
    mycol = "users"
    userInfo = request.json
    result = mongo.db[mycol].find_one({'email':userInfo['email']})
    if result:
        # SHA 256 encryption for password, store the hex equivalent as password
        encodedPassword = hashlib.sha256(userInfo['password'].encode())
        userInfo['password'] =encodedPassword.hexdigest()

        check_password = userInfo['password'] == result ['password']
        if check_password : 
            userInfo['firstName'] = result['firstName']
            userInfo['lastName'] = result['lastName']
            return userInfo
        else :
            return jsonify('Wrong password entered')  
    else :
        return jsonify('User not registered')  


@app.route('/addTodo', methods=['POST'])
def addTodo():
    mycol = "users"
    todo  = request.json['todo']
    unique_id = str(uuid4())
    todo['id'] = unique_id
    todo['vote'] = 0
    # print(todo)
    userEmail = request.json['email'];
    addTodoToTimeline(todo,userEmail)
    userInfo = {}
    result = mongo.db[mycol].find_one({'email':userEmail})
    try:
        userInfo['todos'] = result['todos']
    except:
        userInfo['todos'] = [] 

    # if else not reqd because user email will be read automatically 
    # in frontend and will be sent along with the form body

    userInfo['firstName'] = result['firstName']
    userInfo['lastName'] = result['lastName']
    userInfo['email'] = result['email']
    userInfo['password'] = result['password']
    userInfo['todos'].append(todo) 
    mongo.db[mycol].update_one({"email":userEmail},{"$set":userInfo})

    return jsonify('Added todo to current user')

@app.route('/getTodos',methods=['GET'])
def getTodos():
    userEmail = request.args.get('user')
    mycol = "users"
    result = mongo.db[mycol].find_one({'email':userEmail})
    if result:
        if 'todos' in result:
            todos = result['todos']
            resp = jsonify(todos)
            return resp
        else:
            resp = jsonify('No todos present')
            return resp
    else:
        resp = jsonify('Invalid request')
        return resp


@app.route('/voteTodo',methods=['PUT']) 
def voteTodo():
       mycol = "users"
       userEmail = request.json['email']
       newTodoId = request.json['todoId']
       voteType =  request.json['voteType']
       userInfo ={} 
       result =  mongo.db[mycol].find_one({"email": userEmail}) 

       if result:
            userInfo = {}
            newTodoList = []

            for todo in result['todos'] :
                if todo['id'] == newTodoId:
                    # todo['item'] = newTodo['item']
                    # todo['imp'] = newTodo['imp']
                    if voteType == 'up':
                        todo['vote'] = todo['vote'] + 1
                    else:
                        todo['vote'] = todo['vote'] - 1

                newTodoList.append(todo) 

            userInfo['firstName'] = result['firstName']
            userInfo['lastName'] = result['lastName']
            userInfo['email'] = result['email']
            userInfo['password'] = result['password']
            userInfo['todos'] = newTodoList 
            mongo.db[mycol].update_one({"email":userEmail},{"$set":userInfo}) 
            handleVoteTimeline(userEmail,newTodoId,voteType)   
            resp=jsonify('Todo updated successfully!')
            return resp
       else:
            resp=jsonify("User doesn't exist!")
            return resp  

def handleVoteTimeline(userEmail,newTodoId,voteType):
    print(userEmail," ",newTodoId," ",voteType)
    userInfo ={} 
    # result =  mongo.db[mycol].find_one({"email": userEmail})

@app.route('/deleteTodo',methods=['DELETE'])
def deleteTodo():
    userEmail = request.args.get('user')
    todoId = request.args.get('id')
    mycol='users'
    result = mongo.db[mycol].find_one({'email':userEmail})
    if result:
        myTodoArr = result['todos']
        for todo in myTodoArr:
            if todo['id'] == todoId :
                # print(todo)
                newTodoList = result['todos']
                newTodoList.remove(todo)
                userInfo = {}
                userInfo['firstName'] = result['firstName']
                userInfo['lastName'] = result['lastName']
                userInfo['email'] = result['email']
                userInfo['password'] = result['password']
                userInfo['todos'] = newTodoList
                mongo.db[mycol].update_one({"email":userEmail},{"$set":userInfo})

    return jsonify('todo deleted successfully')
   

def addTodoToTimeline(todo,userEmail):
    myEntry={}
    myEntry['email']= userEmail
    myEntry['time']=  datetime.datetime.now().strftime('%Y-%m-%d %H:%M')
    myEntry['id']= todo['id']
    myEntry['vote']= todo['vote']
    myEntry['item']= todo['item']
    # print(myEntry)
    if q.full():
        q.get()
        print('Removed an entry from queue')

    q.put(myEntry)
    return jsonify("Added an entry to queue")


@app.route("/getTimeline",methods=["GET"])
def getTimeline():
    myTimelineArray = []
    for i in q.queue:
        myTimelineArray.insert(0,i)
    return jsonify(myTimelineArray)    

# how to hash a string (SHA 256)
@app.route('/tempAdd', methods=['POST'])
def tempAdd():
    userInfo = request.json  
    print(userInfo)
    myPassword = userInfo['password']
    result = hashlib.sha256(myPassword.encode())
    userInfo['password'] =str(result.hexdigest())
    print(userInfo['password'])
    return jsonify('tempAdded successfully')

if __name__ == '__main__':
    app.run()