import json 
import requests
from flask import Flask, request, render_template
from django.http import JsonResponse
from functools import partial
import string
import csv
import datetime
import pandas as pd
import json
import plotly
import plotly.express as px
import ast
import matplotlib.pyplot as plt
import os
from dotenv import load_dotenv

load_dotenv()

TELEGRAM_URL = os.environ.get("TELEGRAM_URL")
TUTORIAL_BOT_TOKEN = os.environ.get("TUTORIAL_BOT_TOKEN")
csvDBFile = os.environ.get("CSV_DBFile")

app = Flask(__name__)

def getDataFrame(csv):
    return pd.read_csv(csv, index_col=0)

def checkIfLastRowFromDate(dataFrame, date):
    index = dataFrame.index
    dates = list(index)
    dateStr = dates[len(dates) - 1]
    print(dateStr)
    dateFromDataFrame = datetime.datetime.strptime(dateStr, '%d/%m/%Y')
    if(dateFromDataFrame.date() < date.date()):
        return False
    return True

def getEntryOfDate(columnName, date):
    global csvDBFile
    columnNameUpper = columnName.upper()
    df = getDataFrame(csvDBFile)
    dateStr = date.strftime('%d/%m/%Y')
    # if(checkIfLastRowFromDate(df, date) == False):
    #     return False
    if(dateStr in df.index):
        return df.loc[dateStr, columnNameUpper]
    else:
        return False

def visualizeHeadacheStatistics1():
    global csvDBFile
    df = getDataFrame(csvDBFile)
    date = datetime.datetime.now()
    food = getEntryOfDate("BREAKFAST", date) + getEntryOfDate("LUNCH", date) + getEntryOfDate("DINNER", date) + getEntryOfDate("SNACK", date)

    fig = px.bar(df, x=df.index, y='HEADACHE', color="EYE EXERCISE")
    #fig = px.histogram(x=food, y = )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('diary.html', graphJSON=graphJSON)

def visualizeHeadacheStatistics():
    global csvDBFile
    df = getDataFrame(csvDBFile)
    date = datetime.datetime.now()
    food = getEntryOfDate("BREAKFAST", date) + getEntryOfDate("LUNCH", date) + getEntryOfDate("DINNER", date) + getEntryOfDate("SNACK", date)

    fig = px.bar(df, x=df.index, y='HEADACHE', color="EYE EXERCISE")
    result = map(lambda x: str(x), df['HEADACHE'])
    print(df['HEADACHE'])
    result2 = map(lambda x: str(x), df['EYE EXERCISE'])
    fig = df.plot.scatter(x = 'HEADACHE', y = 'EYE EXERCISE')
    #fig = px.histogram(x=food, y = )

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('diary.html', graphJSON=graphJSON)

def saveDataInCsv(dataToSave, date, columnName):
    global csvDBFile
    print(saveDataInCsv)
    columnNameUpper = columnName.upper()
    dateStr = date.strftime("%d/%m/%Y")
    print(dateStr)
    print("dataToSave", dataToSave)
    df = getDataFrame(csvDBFile)

    if(checkIfLastRowFromDate(df, date) == False):
        print("add row")

        cols = [[{'amount': 0, 'food': []}, [], [], 0, None, [], [], None, None]]
            
        df2 = pd.DataFrame(cols, columns=list(df.columns), index=[dateStr])
        print(df2)
        df = df.append(df2)
        print(df)

        print("-------------------", dataToSave, type(dataToSave))
        if(isinstance(dataToSave, list) and len(dataToSave)):
            df.at[df.index[-1], columnNameUpper] = str(list(dataToSave))
        else:
            df.at[df.index[-1], columnNameUpper] = dataToSave
        print(df.at[df.index[-1], columnNameUpper])
    else:
        #print(df.loc[[dateStr]])
        if(isinstance(dataToSave, list) and len(dataToSave)):
            df.loc[dateStr, columnNameUpper] = str(list(dataToSave))
        else:
            df.loc[dateStr, columnNameUpper] = dataToSave
    df.to_csv(csvDBFile)
    return True

def saveFoods(meal, dateTime, args):
    foodArray = args
    print(meal, dateTime, foodArray)
    
    if(len(foodArray) == 0):
        return False

    previousData = getEntryOfDate(meal, dateTime)
    print(previousData, type(previousData))
    
    if(isinstance(previousData, list)):
        foodArray = foodArray + ast.literal_eval(previousData)

    return saveDataInCsv(foodArray, dateTime, meal)

def saveEntry(dateTime, args, columnName):
    dataToSave = datetime.datetime.strftime(dateTime, '%H:%M:%S')
    return saveDataInCsv(dataToSave, dateTime, columnName)

def savePeriod(dateTime, args, columnName):
    dataToSave = args[0]
    return saveDataInCsv(dataToSave, dateTime, columnName)

def saveAntihistamine(arrayOfFoodAfterPill, dateTime, columnName):
    print(arrayOfFoodAfterPill, dateTime)
    if(len(arrayOfFoodAfterPill) == 0):
        return False
    previousData = getEntryOfDate(columnName, dateTime)

    amount = 1
    food = arrayOfFoodAfterPill

    if(isinstance(previousData, list)):
        previousData = previousData.replace("'", '"')
        previousData = json.loads(previousData)
        amount = previousData["amount"] + 1
        food = previousData["food"] + arrayOfFoodAfterPill
        print(amount)
        print(food)

    dataToSave = {
        "amount" : amount,
        "food" : food
    }
    print(dataToSave)
    return saveDataInCsv(json.dumps(dataToSave), dateTime, columnName)

def saveEyeExercise(dateTime, args, columnName):
    previousData = getEntryOfDate(columnName, dateTime)

    #print(previousData, type(previousData), type(ast.literal_eval(previousData)))
    amount = previousData + 1
    print(amount)

    return saveDataInCsv(amount, dateTime, columnName)

def send_message(message, chat_id):
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown",
    }

    response = requests.post(f"{TELEGRAM_URL}{TUTORIAL_BOT_TOKEN}/sendMessage", data=data)
    return response

actions = {
    "/breakfast": partial(saveFoods, meal="breakfast"),
    "/lunch": partial(saveFoods, meal="lunch"),
    "/dinner": partial(saveFoods, meal="dinner"),
    "/snack": partial(saveFoods, meal="snack"),
    "/headache": partial(saveEntry, columnName="headache"),
    "/sport": partial(saveEntry, columnName="sport"),
    "/eye": partial(saveEyeExercise, columnName="eye exercise"),
    "/antihistamine": partial(saveAntihistamine, columnName="antihistamine"),
    "/period": partial(savePeriod, columnName="period"),
}

@app.route('/', methods=['GET'])
def home():
    return "<h1 style='color: red;'>Go to /DiaryBot</h1>"

@app.route('/DiaryBot', methods=['GET'])
def getDiaryBot():
    global userChatId
    msg = "Your diary was opened"
    #resp = send_message(msg, userChatId)
    
    # TODO read from .svg and give statisticks with plotly

    return visualizeHeadacheStatistics()

@app.route('/', methods=['POST'])
def postDiaryBot():
    global userChatId
    global actions

    tData = request.json
    telegramMessage = tData["message"] # chat, message text, date, from, id,
    userChatId = telegramMessage["chat"]["id"]
    try:
        text = telegramMessage["text"].strip().lower()
    except Exception as e:
        print(e)
        return JsonResponse({"ok": "POST request processed"})

    text = " ".join(text.split())
    words = text.split(' ')

    commandList = list(filter(lambda x: '/' in x, words))
    if(len(commandList) == 1) :
        command = commandList[0]
        
        print("command: ", command)

        dateTime = telegramMessage["date"] 
        print("------dateTime", dateTime)
        date = datetime.datetime.fromtimestamp(dateTime)
        
        args = text.replace(command, "").split(',')
        args = [i.strip() for i in args]

        while("" in args) :
            args.remove("")

        if(command in actions) :
            isAccepted = False
            if(command == "/antihistamine"):
                isAccepted = actions[command](dateTime=date, arrayOfFoodAfterPill=args)
            else:
                isAccepted = actions[command](dateTime=date, args=args)
            if(isAccepted != True):
                msg = "Error. No parameters provided for " + command
                send_message(msg, userChatId)   
                return "OK"  
        else:
            print(actions.keys())
            msg = "No such command. Commands: \n" + "\n".join(actions.keys())
            send_message(msg, userChatId) 
            return "OK"

        msg = "I got your entry"
        resp = send_message(msg, userChatId)
        return "OK"
    else:
        msg = "No such command. Commands: \n" + "\n".join(actions.keys())
        send_message(msg, userChatId) 
        return "OK"    

if __name__ == '__main__':
    #saveEyeExercise(16093646, [], "EYE EXERCISE")
    global userChatId
    userChatId = 39930052
    app.run(host='0.0.0.0', port=5002, debug=True, use_reloader=False)
