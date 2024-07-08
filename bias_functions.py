import requests
import pandas as pd
import numpy as np
import os
import shutil
import json
from datetime import date 
import base64

def read_json_files(directory):
    df = pd.DataFrame(columns=['gender', 'degree', 'institute', 'year', 'city', 'employer', 'experience', 'keywords'])
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    gender = data['ResumeParserData']['Gender']
                    if len(data['ResumeParserData']['SegregatedQualification']) > 0:
                        degree = data['ResumeParserData']["SegregatedQualification"][0]["Degree"]["NormalizeDegree"]
                        institute = data['ResumeParserData']["SegregatedQualification"][0]['Institution']['Name']
                    else:
                        degree, institute = '', ''
                    year = data['ResumeParserData']['DateOfBirth'][-4:]
                    city = data['ResumeParserData']['Address'][0]['City']
                    employer = data['ResumeParserData']["CurrentEmployer"]
                    role = data['ResumeParserData']["JobProfile"]
                    experience = data['ResumeParserData']["WorkedPeriod"]["TotalExperienceInMonths"]
                    keywords = data['ResumeParserData']['SkillKeywords']
                    
                    gender = gender if gender != '' else np.nan
                    degree = degree if degree != '' else np.nan
                    institute = institute if institute != '' else np.nan
                    year = year if year != '' else np.nan
                    city = city if city != '' else np.nan
                    employer = employer if employer != '' else np.nan
                    role = role if role != '' else np.nan
                    experience = experience if experience != '' else np.nan
                    keywords = keywords.split(',')
                    
                    row = pd.DataFrame([{
                        'gender' : gender,
                        'degree' : degree,
                        'institute' : institute,
                        'year' : year,
                        'city' : city,
                        'employer' : employer,
                        'role' : role,
                        'experience' : experience,
                        'keywords' : keywords
                    }])
                    df = pd.concat([df, row], ignore_index=True)
                    todays_date = date.today() 
                    current_year = todays_date.year
                    for index, row in df.iterrows():
                        born = df.at[index, 'year']
                        years = df.at[index, 'experience']
                        try:
                            df.at[index, 'age'] =  current_year - int(born)
                        except (ValueError, TypeError):
                            df.at[index, 'age'] = np.nan
                        try:
                            df.at[index, 'experience'] = int(years)
                        except (ValueError, TypeError):
                            df.at[index, 'experience'] = years
                except json.JSONDecodeError as e:
                    print(f"Error reading {file_path}: {e}")
    return df

def extract_job_info(folder_path):
    json_file_path = os.path.join(folder_path, 'job_description.json')  # Replace with your JSON file name
    with open(json_file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    job_info = {
        'skills': data['JDParsedData']['Skills']['Required'] + data['JDParsedData']['Skills']['Preferred'],
        'jobTitle': data['JDParsedData']['JobProfile']['Title'],
        'jobDescription': data['JDParsedData']['JobDescription']
    }
    
    return job_info

def extract_text(directory):
    url = 'https://dev.api.talentmarx.in/api/v1/ml/extract-text'
    texts = []
    for filename in os.listdir(directory):
        if filename.endswith('.pdf') or filename.endswith('.docx') or filename.endswith('.doc'):
            filepath = os.path.join(directory, filename)
            with open(filepath, "rb") as file:
                encoded_string_val = base64.b64encode(file.read())
            filedata = encoded_string_val.decode('UTF-8')
            payload = {
                "filename": filename,
                "filedata": filedata
            }
            response = requests.post(url, json=payload)
            response_data = response.text
            texts.append(response_data)
    return texts 

def check_bias_multi(df, colname, threshold):
    temp_df = df[[colname, 'selected']]
    temp_df = temp_df.dropna()
    unique_categories = []
    value_counts_tuples = list(temp_df[colname].value_counts().items())
    for i in range(len(value_counts_tuples)):
        if(value_counts_tuples[i][1] < threshold):
            break
        unique_categories.append(value_counts_tuples[i][0])
    if((len(unique_categories) == 0) or (len(unique_categories) == temp_df.shape[0])):
        return (0,[])
    probabilities = []
    for category in unique_categories:
        selected = temp_df[temp_df[colname] == category]['selected'].sum()
        total = temp_df[temp_df[colname] == category].shape[0]
        probability = selected / total
        probabilities.append(probability)
    
    probabilities = list(enumerate(probabilities))
    index = 0
    probabilities.sort(key = lambda i:i[1], reverse = True)
    for i in range(len(probabilities)):
        if((probabilities[i][1] - probabilities[i+1][1]) > 0.05):
            index = i
            break
    if index == (len(probabilities)-1):
        return (0,[])
    else:
        city_index = probabilities[0][0]
        favoured_list = [unique_categories[city_index]]
        return (1, favoured_list)
    
def store_results(df):
    selected = df[df['selected'] == 1]
    not_selected = df[df['selected'] == 0]
    dir_path = "results/"
    if os.path.exists(dir_path):
        shutil.rmtree(dir_path)
    os.mkdir(dir_path)
    selected.to_csv('results/selected_candidates.csv', index=False)
    not_selected.to_csv('results/non_selected_candidates.csv', index=False)
