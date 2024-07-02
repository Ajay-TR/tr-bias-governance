from flask import Flask, render_template, request, session
import text_extraction
import bias_functions
import asyncio
import augment_functions
import requests
import pandas as pd
import numpy as np

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak

app = Flask(__name__)
app.secret_key = 'kv-654c'

similarity_api_url = 'https://dev.api.talentmarx.in/api/v1/ml/similarity/'

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
    return {"message": "Files uploaded successfully"}

@app.route('/check_bias', methods=['POST'])
def augment():
    data = request.json
    job_description = data.get('jd')

    df               = bias_functions.read_json_files('./uploads/parsed_json/')
    df['experience'] = augment_functions.process_column(df['experience'])
    df['age']        = augment_functions.clean_and_convert_column(df['age'])
    df['gender']     = augment_functions.clean_column(df['gender'])
    df['employer']   = augment_functions.clean_column(df['employer'])
    df['degree']     = augment_functions.clean_column(df['degree'])
    df['institute']  = augment_functions.clean_column(df['institute'])
    
    print("Adding score columns")
    augment_functions.find_score(df, 'gender', job_description, similarity_api_url)
    augment_functions.find_score(df, 'city', job_description, similarity_api_url)
    augment_functions.find_score(df, 'institute', job_description, similarity_api_url)
    augment_functions.find_score(df, 'employer', job_description, similarity_api_url)
    augment_functions.find_score(df, 'degree', job_description, similarity_api_url)
    augment_functions.find_score(df, 'age', job_description, similarity_api_url)

    doc = SimpleDocTemplate("report.pdf", pagesize=letter)
    elements = []
    
    gender_elems, gender_biased, gender_max_elements = augment_functions.get_bias_score(df, 'gender')
    institute_elems, institute_biased, institute_max_elements = augment_functions.get_bias_score(df, 'institute')
    city_elems, city_biased, city_max_elements = augment_functions.get_bias_score(df, 'city')
    employer_elems, employer_biased, employer_max_elements = augment_functions.get_bias_score(df, 'employer')
    degree_elems, degree_biased, degree_max_elements = augment_functions.get_bias_score(df, 'degree')
    age_elems, age_biased, age_max_elements = augment_functions.get_bias_score(df, 'age')

    elements.extend(gender_elems)
    elements.extend(institute_elems)
    elements.extend(city_elems)
    elements.extend(employer_elems)
    elements.extend(degree_elems)
    elements.extend(age_elems)

    doc.build(elements)

    return {"messages": "Bias checked", "age_bias":age_biased, "fav_age": age_max_elements, "gender_bias": gender_biased, "fav_gender": gender_max_elements, "institute_bias": institute_biased, "city_bias": city_biased, "degree_bias": degree_biased, "employer_bias": employer_biased, "fav_degrees": degree_max_elements, "fav_cities": city_max_elements, "fav_institutes": institute_max_elements, "fav_employers": employer_max_elements}