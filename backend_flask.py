from flask import Flask, render_template, request
import text_extraction
import bias_functions
import asyncio
import requests
import pandas as pd
import numpy as np
import os
import json
from datetime import date 
import base64

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'files' not in request.files:
        return 'No file part'
    
    files = request.files.getlist('files')
    
    for file in files:
        file.filename = file.filename.split('/')[1]
        file.save('./uploads/' + file.filename)
            
    asyncio.run(text_extraction.start_extraction())
    df = bias_functions.read_json_files('./uploads/parsed_json/')
    print(df)
    return 'Files uploaded successfully'

#@app.route('/extract_files', methods=['GET'])
#def extract_text():

@app.route('./score_resums', method=['POST'])
def score():
    

if __name__ == '__main__':
    app.run(debug=True)
    
# {
# "filename": "<name of the file. extension is imp>"
# "filedata": "<base64 encoded filedata>"
# }