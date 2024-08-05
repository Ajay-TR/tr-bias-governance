from flask import Flask, render_template, request, session
# import text_extraction
import bias_functions
import asyncio
import augment_functions
import requests
import pandas as pd
import numpy as np
# import parse_jd_fast
import json
import os
import time
import tqdm

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak

app = Flask(__name__)
app.secret_key = 'kv-654c'
# APP Configs:
UPLOADS_DIR = './uploads/'
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)
UPLOADS_DIR = os.path.abspath(UPLOADS_DIR)

candidate_api = 'https://stg.api.talentmarx.in/api/v1/ml/generate-candidate-embeddings/'
job_api = 'https://stg.api.talentmarx.in/api/v1/ml/generate-job-embeddings/'

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return 'No file part'
    
    file = request.files["file"]
    FILENAME = file.filename
    filepath = os.path.join(UPLOADS_DIR, FILENAME)
    file.save(filepath)
    
    OUTPUT_REPORT_FILENAME = f"report_{FILENAME.split('.')[0]}_{int(time.time())}.pdf"
    doc = SimpleDocTemplate(OUTPUT_REPORT_FILENAME, pagesize=letter)
    elements = []
            
    df = pd.read_json(filepath)
    df.fillna("[]",inplace=True)
    df = df.sample(n=20)
    df.info()
    
    for index, row in df.iterrows():
        df.at[index, 'company'] = json.loads(df.at[index, 'candidateexperience'])[0]["companyname"] if len(json.loads(df.at[index, 'candidateexperience'])) != 0 else "nan"
        df.at[index, 'curr_title'] = json.loads(df.at[index, 'candidateexperience'])[0]["jobtitle"] if len(json.loads(df.at[index, 'candidateexperience'])) != 0 else "nan"
        df.at[index, 'location'] = json.loads(df.at[index, 'candidateexperience'])[0]["location"] if len(json.loads(df.at[index, 'candidateexperience'])) != 0 else "nan"
        df.at[index, 'degree'] = json.loads(df.at[index, 'candidateeducation'])[0]["degree"] if len(json.loads(df.at[index, 'candidateeducation'])) != 0 else "nan"
        df.at[index, 'college'] = json.loads(df.at[index, 'candidateeducation'])[0]["institution"] if len(json.loads(df.at[index, 'candidateeducation'])) != 0 else "nan"
    print(df['jobid'].unique().tolist())
    for job_id in df['jobid'].unique().tolist():
        print(job_id)
        job_df = df[df['jobid'] == job_id]
        job_des = str(job_df['description'].unique().tolist()[0])
        job_title = str(job_df['title'].unique().tolist()[0])
        job_data = {
            "skills" : job_des.split(','),
            "jobTitle" : job_title,
            "jobDescription" : job_des
        }
        job_embed = requests.post(job_api, json=job_data).text
        print()
        job_df = df.copy()
        job_df = job_df.drop(columns=['jobid', 'candidateid','description', 'title', 'candidateexperience', 'candidateeducation'])
        
        # print("Adding score columns")
        augment_functions.find_score(job_df, 'curr_title', job_embed, candidate_api)
        augment_functions.find_score(job_df, 'location', job_embed, candidate_api)
        augment_functions.find_score(job_df, 'college', job_embed, candidate_api)
        augment_functions.find_score(job_df, 'company', job_embed, candidate_api)
        augment_functions.find_score(job_df, 'degree', job_embed, candidate_api)
        
        # print(job_df.head())
        
        for col in ['curr_title', 'location', 'college', 'company', 'degree']:
            unique_vals = job_df[col].unique().tolist()
            if 'nan' in unique_vals:
                unique_vals.remove('nan')
            # print("Unique Values are ",unique_vals)
            if len(unique_vals) >= 2:
                print("The unique values are : ", unique_vals)
                col_elems, col_biased, col_max_elems = augment_functions.get_bias_score(job_df, col, job_id, unique_vals)
                elements.extend(col_elems)
    
    doc.build(elements)
    
    return {"message": "Files uploaded successfully"}

if __name__ == '__main__':
    app.run(debug=True, port=5001)