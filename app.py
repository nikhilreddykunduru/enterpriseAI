from flask import Flask, render_template,request,json
from flask_mysqldb import MySQL
import requests
from werkzeug.utils import secure_filename
import os
import pandas as pd
import nltk
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize, sent_tokenize
import re
import random
import pickle
import spacy
import string
import sklearn
import jsonify

punct = string.punctuation
from spacy.lang.en.stop_words import STOP_WORDS
stop_words = list(STOP_WORDS)
nlp = spacy.load('en_core_web_sm')

app = Flask(__name__)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = ''
app.config['MYSQL_DB'] = 'test'

mysql = MySQL(app)

def text_data_cleaning(sentence):
  doc = nlp(sentence)
  tokens = []
  for token in doc:
    if token.lemma_ != "-PRON-":
      temp = token.lemma_.lower().strip()
    else:
      temp = token.lower_
    tokens.append(temp)
 
  cleaned_tokens = []
  for token in tokens:
    if token not in stop_words and token not in punct:
      cleaned_tokens.append(token)
  return cleaned_tokens

pairs = [
    [
        r"my name is (.*)",
        ["Hello, How are you doing today ?",]
    ],
    [
        r"hi|hey|hello",
        ["Hello", "Hey there",]
    ], 
    [
        r"what is your name?",
        ["You can call me a Mr.Bot ?",]
    ],
    [
        r"how are you ?",
        ["I am fine, thank you! How can i help you?",]
    ],
    [
        r"i am fine, thank you",
        ["great to hear that, how can i help you?",]
    ],
    [
        r"i'm (.*) doing good",
        ["That's great to hear","How can i help you?:)",]
    ],
    [
        r"(.*) thank you so much, that was helpful|thank you",
        ["Iam happy to help", "No problem, you're welcome",]
    ],
    [
        r"quit",
    ["Bye, take care. See you soon :) ","It was nice talking to you. See you soon :)"]
],
]

@app.route("/bot", methods = ["GET", "POST"])
def chatbot():
    c=0
    if request.method == "POST":
        text=request.get_data()
        text=text.decode('utf-8')
        text=text.lower()
        for i in range(8):
            if(re.match(pairs[i][0],text)):
                result=random.choice(pairs[i][1])
                result='<p>'+result+'</p>'
                c=1
                break
        if(c==0):
            con = mysql.connection.cursor()
            stat="SELECT * FROM catalog"
            category=['laptop','book','car']
            pri_range=['low','mid','high','lowrange','midrange','highrange','lowpriced','midpriced','highpriced','costly','cheap','highend']
            subcat=['gaming','business','personal','sedan','convertible','SUV','comedy','fantasy','investment']
            authors=['jkrowling','buffett','shakespeare']
            stopWords = set(stopwords.words("english"))
            #punc = '''!()-[]{};:'"\,<>./?@#$%^&*_~'''
            for ele in text:  
                if ele in punct:  
                    text = text.replace(ele, "")
            words = word_tokenize(text)
            tok = [word for word in words if not word in stopwords.words()]
            result=""
            reslist=[]
            d=0
            au=0
            for i in tok:
                if(i in category):
                    reslist.append("category = '"+i+"'")
                    d=1
                if(i in pri_range):
                    reslist.append("pri_range = '"+i+"'")
                if(i in subcat):
                    reslist.append("subcat = '"+i+"'")
                if(i in authors):
                    reslist.append("author = '"+i+"'")
                    au=1
            if(len(reslist)>=1):
                stat+=" WHERE "+reslist[0]
                for j in range(1,len(reslist)):
                    stat+=" AND "+reslist[j]
            stat+="ORDER BY score DESC"
            try:
                con.execute(stat)
                fetchres=con.fetchone()
                if(au==1):
                    req=fetchres[6].upper()
                else:
                    req='₹'+str(fetchres[4])
                result="<div class='card'><img src='"+fetchres[0]+"' alt='NO IMAGE' style='width:100%'><div class='container'><h4><b>"+fetchres[1]+"</b></h4><h5><center>"+req+"</center></h5></div></div>"
            except:
                result="<p>Sorry, couldn't help due to some issues</p>"
            if(d==0):
                result="<p>Sorry, could not understand. Please check.</p>"
        return result

@app.route("/", methods = ["GET", "POST"])
def upload():
  con = mysql.connection.cursor()
  if request.method == "POST":
    prods = request.form.getlist('prod[]')
    files=request.files.getlist('f[]')
    cfiles=request.files.getlist('cf[]')
    for i in range(len(files)):
      filename = secure_filename(files[i].filename)
      files[i].save(secure_filename(filename))
      fname = 'model.sav'
      loaded_model = pickle.load(open(fname, 'rb'))
      test= pd.read_csv(filename, sep='\t',header=None,engine='python',error_bad_lines=False)
      test.columns=['review']
      xt=test['review']
      result = loaded_model.predict(xt)
      os.remove(filename)
      cfilename = secure_filename(cfiles[i].filename)
      cfiles[i].save(secure_filename(cfilename))
      ctest= pd.read_csv(cfilename, sep='\t',header=None,engine='python',error_bad_lines=False)
      ctest.columns=['review']
      cxt=ctest['review']
      cresult = loaded_model.predict(cxt)
      os.remove(cfilename)
      score=str(((round(sum(result)/len(result),3))*(0.5))+((round(sum(cresult)/len(cresult),3))*(0.5)))
      res="INSERT INTO products(productname, score) VALUES ('"+prods[i]+"',"+score+")"
      con.execute(res)
    con.execute("SELECT productname FROM products ORDER BY score DESC")
    fetchres=con.fetchall()
    di=dict()
    di[0]=len(fetchres)
    for j in range(len(fetchres)):
      di[j+1]=fetchres[j][0]
    return di
  return render_template("index.html")

@app.after_request
def after_request(response):
    header = response.headers
    header['Access-Control-Allow-Origin'] = '*'
    header['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
    header['Access-Control-Allow-Methods'] = 'OPTIONS, HEAD, GET, POST, DELETE, PUT'
    return response

if __name__ == "__main__":
    app.run(debug=True)