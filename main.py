import numpy as np
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import xlsxwriter 
from models.base_model import BaseModel
from models.multi_model import MultiModel
import pudb


def load_and_preprocess_data(fname):
    """
    We can put any pre-processing of the data set here if needed.
    """
    df = pd.read_csv(fname)
    df = df.dropna(subset=['salary'])
    df = drop_inactive_teams(df)
    df = drop_injured_players(df)
    df = merge_duplicates(df)
    df = find_opponents(df)
    df = df.set_index('player')
    return df

def drop_inactive_teams(df):
    df = df[df.team != 'FA'] #drop free agents from data
    df = df[(df.team != 'KC')] #following teams aren't playing in the Gameset
    df = df[(df.team != 'DEN')] 
    df = df[(df.team != 'NE')] 
    df = df[(df.team != 'NYJ')] 
    df = df[(df.team != 'CAR')] 
    df = df[(df.team != 'CLE')] 
    df = df[(df.team != 'PIT')] 
    df = df[(df.team != 'TB')]
    df = df[(df.team != 'PHI')]  
    df = df[(df.team != 'DAL')]  
    return df

def drop_injured_players(df):
    df = df[(df.player != 'Jakeem Grant')] 
    df = df[(df.player != 'Xavien Howard')] 
    df = df[(df.player != 'Marqise Lee')] 
    df = df[(df.player != 'Geoff Swaim')] 
    df = df[(df.player != 'Dede Westbrook')] 
    df = df[(df.player != 'Tyrell Williams')] 
    df = df[(df.player != 'Davante Adams')] 
    df = df[(df.player != 'Geronimo Allison')] 
    df = df[(df.player != 'Marquez Valdes-Scantling')] 
    df = df[(df.player != 'Malcolm Brown')] 
    df = df[(df.player != 'Parris Campbell')] 
    df = df[(df.player != 'Deebo Samuel')] 
    df = df[(df.player != 'Raheem Mostert')] 
    df = df[(df.player != 'Chris Thompson')] 
    df = df[(df.player != 'Vernon Davis')] 
    df = df[(df.player != 'David Johnson')] 
    df = df[(df.player != 'Christian Kirk')] 
    df = df[(df.player != 'Maxx Williams')] 
    df = df[(df.player != 'Sterling Shepard')] 
    df = df[(df.player != 'Delanie Walker')] 
    df = df[(df.player != 'Drew Brees')] 
    df = df[(df.player != 'Alvin Kamara')] 
    df = df[(df.player != 'Jared Cook')] 
    df = df[(df.player != 'Mitch Trubisky')] 
    df = df[(df.player != 'Marquise Brown')] 
    df = df[(df.player != 'Will Dissly')] 
    return df

def find_opponents(df):
    df['opponent'] = np.nan
    df.loc[df.team == 'MIA', 'opponent'] = "BUF"
    df.loc[df.team == 'BUF', 'opponent'] = "MIA"
    df.loc[df.team == 'JAX', 'opponent'] = "CIN"
    df.loc[df.team == 'CIN', 'opponent'] = "JAX"
    df.loc[df.team == 'MIN', 'opponent'] = "DET"
    df.loc[df.team == 'DET', 'opponent'] = "MIN"
    df.loc[df.team == 'OAK', 'opponent'] = "GB"
    df.loc[df.team == 'GB', 'opponent'] = "OAK"
    df.loc[df.team == 'LAR', 'opponent'] = "ATL"
    df.loc[df.team == 'ATL', 'opponent'] = "LAR"
    df.loc[df.team == 'HOU', 'opponent'] = "IND"
    df.loc[df.team == 'IND', 'opponent'] = "HOU"
    df.loc[df.team == 'SF', 'opponent'] = "WAS"
    df.loc[df.team == 'WAS', 'opponent'] = "SF"
    df.loc[df.team == 'ARI', 'opponent'] = "NYG"
    df.loc[df.team == 'NYG', 'opponent'] = "ARI"
    df.loc[df.team == 'LAC', 'opponent'] = "TEN"
    df.loc[df.team == 'TEN', 'opponent'] = "LAC"
    df.loc[df.team == 'NO', 'opponent'] = "CHI"
    df.loc[df.team == 'CHI', 'opponent'] = "NO"
    df.loc[df.team == 'BAL', 'opponent'] = "SEA"
    df.loc[df.team == 'SEA', 'opponent'] = "BAL"
    return df

def merge_duplicates(df):
    """
    There are duplicates in the data set if one player is eligible for
    multiple positions. For simplicity, we just remove the position with the 
    lowest expected number of points.
    """
    df['position2'] = np.nan
    multiple_positions = df.groupby('player').size()
    multiple_positions = multiple_positions[multiple_positions > 1]
    for player in multiple_positions.index:
        best_position = df[df.player == player].points.idxmax()
        rows_to_drop = df[df.player == player].index.tolist()
        rows_to_drop.remove(best_position)
        df = df.drop(rows_to_drop, axis=0)
    return df


if __name__ == "__main__":
    fname = Path.cwd() / 'data' / 'ffa_customrankings2019-7.csv'
    df = load_and_preprocess_data(fname)

    mdl = MultiModel()
    # mdl = BaseModel()
    mdl.load(df)
    mdl.build_model()
    mdl.solve()
    
    
    
    
