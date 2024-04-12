import requests
import pandas as pd
import numpy as np
import os
import json
from datetime import date 

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
                    
                    gender = gender if gender != '' else np.nan
                    degree = degree if degree != '' else np.nan
                    institute = institute if institute != '' else np.nan
                    year = year if year != '' else np.nan
                    city = city if city != '' else np.nan

                    row = pd.DataFrame([{
                        'gender' : gender,
                        'degree' : degree,
                        'institute' : institute,
                        'year' : year,
                        'city' : city,
                        'employer' : employer,
                        'experience' : experience,
                        'experience_range' : exp_range
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

def check_bias(colname, group):
    temp_df = df[[colname, 'Selected']]
    temp_df = temp_df.dropna()
    parity_diff = metrics.statistical_parity_difference(temp_df['Selected'], prot_attr=temp_df[colname], priv_group=group)
    disparate_impact = metrics.disparate_impact_ratio(temp_df['Selected'], prot_attr=temp_df[colname], priv_group=group)
    kl_divergence = metrics.kl_divergence(y_true=temp_df['Selected'], prot_attr=temp_df[colname], priv_group=group)
    if parity_diff > 0.05 or parity_diff < -0.05:
        print("Statical Parity difference bias exists at {}".format(parity_diff))
    if disparate_impact > 1.2 or parity_diff < 0.8:
        print("Disparate impact ratio bias exists at {}".format(disparate_impact))
    print("The distributions differ by {}".format(kl_divergence))