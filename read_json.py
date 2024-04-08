import os
import json
import pandas as pd
import numpy as np

def read_json_files(directory):
    df = pd.DataFrame(columns=['gender', 'degree', 'institute', 'year'])
    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            file_path = os.path.join(directory, filename)
            with open(file_path, 'r') as file:
                try:
                    data = json.load(file)
                    gender = data['ResumeParserData']['Gender']
                    if len(data['ResumeParserData']['SegregatedCertification']) > 0:
                        degree = data['ResumeParserData']['SegregatedCertification'][0]['Degree']['NormalizeDegree']
                        institute = data['ResumeParserData']['SegregatedCertification'][0]['Institute']['Name']
                    else:
                        degree, institute = '', ''
                    year = data['ResumeParserData']['DateOfBirth'][-4:]

                    gender = gender if gender != '' else np.nan
                    degree = degree if degree != '' else np.nan
                    institute = institute if institute != '' else np.nan
                    year = year if year != '' else np.nan

                    row = pd.DataFrame([{
                        'gender' : gender,
                        'degree' : degree,
                        'institute' : institute,
                        'year' : year
                    }])
                    df = pd.concat([df, row], ignore_index=True)
                except json.JSONDecodeError as e:
                    print(f"Error reading {file_path}: {e}")
    return df

# Example usage
directory_path = 'resumes/parsed_json'
df = read_json_files(directory_path)
print(df)