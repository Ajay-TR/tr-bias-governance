import requests
import pandas as pd
import numpy as np
import os
import shutil
import json
from datetime import date 
import base64
from aif360.sklearn import metrics

def read_json_files(directory):
    df = pd.DataFrame(columns=['gender', 'degree', 'institute', 'year'])
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
                    experience = data['ResumeParserData']["WorkedPeriod"]["TotalExperienceInYear"]
                    exp_range = data['ResumeParserData']["WorkedPeriod"]["TotalExperienceRange"]
                    keywords = data['ResumeParserData']['SkillKeywords']
                    #religion = data['ResumeParserData']
                    
                    gender = gender if gender != '' else np.nan
                    degree = degree if degree != '' else np.nan
                    institute = institute if institute != '' else np.nan
                    year = year if year != '' else np.nan
                    city = city if city != '' else np.nan
                    employer = employer if employer != '' else np.nan
                    experience = experience if experience != '' else np.nan
                    exp_range = exp_range if exp_range != '' else np.nan
                    keywords = keywords.split(',')
                    
                    row = pd.DataFrame([{
                        'gender' : gender,
                        'degree' : degree,
                        'institute' : institute,
                        'year' : year,
                        'city' : city,
                        'employer' : employer,
                        'experience' : experience,
                        'experience_range' : exp_range,
                        'keywords' : keywords
                    }])
                    df = pd.concat([df, row], ignore_index=True)
                    todays_date = date.today() 
                    current_year = todays_date.year
                    for index, row in df.iterrows():
                        born = df.at[index, 'year']
                        years = df.at[index, 'experience']
                        try:
                            df.at[index, 'age'] =  1 if((current_year - int(born)) > 35) else 0
                        except (ValueError, TypeError):
                            df.at[index, 'age'] = born
                        try:
                            df.at[index, 'experience'] = 1 if(float(years) > 4) else 0
                        except (ValueError, TypeError):
                            df.at[index, 'experience'] = years
                except json.JSONDecodeError as e:
                    print(f"Error reading {file_path}: {e}")
    return df

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

def check_bias_binary(df, colname, group):
    temp_df = df[[colname, 'selected']]
    temp_df = temp_df.dropna()
    parity_diff = metrics.statistical_parity_difference(temp_df['selected'], prot_attr=temp_df[colname], priv_group=group)
    disparate_impact = metrics.disparate_impact_ratio(temp_df['selected'], prot_attr=temp_df[colname], priv_group=group)
    if ((parity_diff > 0.05 or parity_diff < -0.05) or (disparate_impact > 1.2 or parity_diff < 0.8)):
        return 1
    else:
        return 0
    

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
