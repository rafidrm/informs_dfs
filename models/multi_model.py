import pandas as pd
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpStatus
import pulp
import pudb


class MultiModel(object):
    """
    Stores general optimization model. We can modify this model to add stacking
    constraints or anything else that shows up.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'DFSModel')
        self.salary_cap = kwargs.get('salary_cap', 50000)
        self.number_of_portfolios = kwargs.get('num_portfolios', 10)
        self.overlap_parameter = kwargs.get('overlap_parameter', 2)
        self.model = LpProblem(self.name, LpMaximize)


    def load(self, df):
        self.df = df
        self.players = LpVariable.dicts(
            "p",
            (player for player in df.index),
            cat="Binary"
        )


    def build_model(self):
        self.build_default_objective()
        self.build_default_constraints()


    def build_default_objective(self):
        self.obj = lpSum([
            self.players[player_name] * self.df.loc[player_name].points
            for player_name in self.df.index])
        self.model += self.obj


    def build_default_constraints(self):
        # salary constraint
        self.salary_constraint = lpSum([
            self.players[player_name] * self.df.loc[player_name].salary
            for player_name in self.df.index]) <= self.salary_cap
        self.model += self.salary_constraint
 
        # QB constraint
        self.QB_constraint = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'QB'].index]) == 1
        self.model += self.QB_constraint

        # RB constraint
        self.RB_constraint_ub = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'RB'].index]) <= 3
        self.model += self.RB_constraint_ub

        self.RB_constraint_lb = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'RB'].index]) >= 2
        self.model += self.RB_constraint_lb

        # WR constraint
        self.WR_constraint_ub = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'WR'].index]) <= 4
        self.model += self.WR_constraint_ub

        self.WR_constraint_lb = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'WR'].index]) >= 3
        self.model += self.WR_constraint_lb

        # TE constraint
        self.TE_constraint_ub = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'TE'].index]) <= 2
        self.model += self.TE_constraint_ub

        self.TE_constraint_lb = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'TE'].index]) >= 1
        self.model += self.TE_constraint_lb

        # DST constraint
        self.DST_constraint = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'DST'].index]) == 1
        self.model += self.DST_constraint

        # full roster constraint (ensures that only 1 flex player selected)
        self.full_roster_constraint = lpSum([
            self.players[player_name] for player_name in self.df.index]) == 9
        self.model += self.full_roster_constraint


    def solve(self):
        # run the solver  
        for roster_number in range(self.number_of_portfolios):
            # self.model.solve()
            self.model.solve(pulp.GLPK())
            self.LpStatus = LpStatus[self.model.status]
            self.print_solution(roster_number)


    def print_solution(self, roster_number):
        output = []
        for player_name in self.players:
            output.append({
                'player': player_name,
                'position': self.df.loc[player_name].position,
                'value': self.players[player_name].varValue
            })
        self.output_df = pd.DataFrame(output)
        self.add_to_df(self.output_df, roster_number)

        print(self.output_df[self.output_df.value == 1])

    def add_to_df(self, output_df, roster_number):
        # updates self.df with the roster and then adds a constraint
        tmp = output_df.drop(columns=['position'])
        tmp = tmp.set_index('player')
        roster_col = 'roster{}'.format(roster_number)
        tmp.columns = [roster_col]
        self.df = pd.concat([self.df, tmp], axis=1)

        # add an overlap constraint 
        overlap_constraint = lpSum([
            self.players[player_name] * self.df.loc[player_name][roster_col]
            for player_name in self.df.index]) <= self.overlap_parameter
        self.model += overlap_constraint


