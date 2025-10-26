import csv
import pandas as pd
def getData():
    df = pd.read_csv("data/data.csv")
    return df 



def FilterData():
    df = getData()
    filtered_df = df[df['Access Code Redemption Status'] == "No"]
    return filtered_df

def getEmailList():
    filtered_df = FilterData()
    email_list = filtered_df['User Email'].tolist()
    return email_list

