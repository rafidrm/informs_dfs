import numpy as np
import pandas as pd
from pathlib import Path
from models.base_model import BaseModel
from models.multi_model import MultiModel


import pudb


def load_and_preprocess_data(fname):
    """
    We can put any pre-processing of the data set here if needed.
    """
    df = pd.read_csv(fname)
    df = df.dropna(subset=['salary'])
    df = merge_duplicates(df)
    df = df.set_index('player')
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
    fname = Path.cwd() / 'data' / 'ffa_customrankings2019-2.csv'
    df = load_and_preprocess_data(fname)

    mdl = MultiModel()
    # mdl = BaseModel()
    mdl.load(df)
    mdl.build_model()
    mdl.solve()
