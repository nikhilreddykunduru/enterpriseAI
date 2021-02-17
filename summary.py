from flask import Flask, render_template,request
import requests
import nltk
from nltk.corpus import stopwords 
from nltk.tokenize import word_tokenize, sent_tokenize
import moviepy.editor as mp
import speech_recognition as sr
from werkzeug.utils import secure_filename
import os
import pandas as pd

app = Flask(__name__)

def sumup(text):
    stopWords = set(stopwords.words("english")) 
    words = word_tokenize(text)
    freqTable = dict()
    for word in words:
        word = word.lower()
        if word in stopWords:
            continue
        if word in freqTable:
            freqTable[word] += 1
        else:
            freqTable[word] = 1
    sentences = sent_tokenize(text) 
    sentenceValue = dict() 
    for sentence in sentences:
        for word, freq in freqTable.items():
            if word in sentence.lower():
                if sentence in sentenceValue:
                    sentenceValue[sentence] += freq
                else:
                    sentenceValue[sentence] = freq   
    sumValues = 0
    for sentence in sentenceValue:
        sumValues += sentenceValue[sentence]
    average = int(sumValues / len(sentenceValue))
    summary = ''
    for sentence in sentences:
        if (sentence in sentenceValue) and (sentenceValue[sentence] > (1.2 * average)):
            summary += " " + sentence
    return summary

@app.route("/", methods = ["GET", "POST"])
def home():
    if request.method == "POST":
        txt = request.form.get("text")
        if(txt!=""):
            url_content = sumup(txt)
        else:
            f1=request.files['vid']
            f1.save(secure_filename(f1.filename))
            clip = mp.VideoFileClip(f1.filename)
            clip.audio.write_audiofile(r"out.wav")
            r = sr.Recognizer()
            with sr.AudioFile('out.wav') as source:
                audio_text = r.listen(source)
            txt = r.recognize_google(audio_text)
            os.remove('out.wav')
            #os.remove(f1.filename)
            print(txt)
            url_content=sumup(txt)
        return url_content
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