import pandas as pd
from pulp import LpProblem, LpVariable, LpMaximize, lpSum, LpStatus
import pulp
import pudb
import xlsxwriter 
from openpyxl import load_workbook

class MultiModel(object):
    """
    Stores general optimization model. We can modify this model to add stacking
    constraints or anything else that shows up.
    """

    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'DFSModel')
        self.salary_cap = kwargs.get('salary_cap', 50000)
        self.number_of_portfolios = kwargs.get('num_portfolios', 10)
        self.overlap_parameter = kwargs.get('overlap_parameter', 1)
        self.model = LpProblem(self.name, LpMaximize)

    def load(self, df):
        self.df = df
        self.players = LpVariable.dicts("p",(player for player in df.index),cat="Binary")
        teams = df.team.unique()
        self.stack = LpVariable.dicts("v",(team for team in teams),cat="Binary")
        self.teams = LpVariable.dicts("t",(team for team in teams),cat="Binary")
              
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
        
        # WR constraint and --- C6 --- 
        self.WR_constraint_b = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'WR'].index]) == 3
        self.model += self.WR_constraint_b  

        # TE constraint       
        self.TE_constraint_b = lpSum([
            self.players[player_name]
            for player_name in self.df[self.df.position == 'TE'].index]) == 1
        self.model += self.TE_constraint_b

        # DST constraint
        self.DST_constraint = lpSum([
            self.players[player_name] for player_name in self.df[self.df.position == 'DST'].index]) == 1
        self.model += self.DST_constraint

        # full roster constraint (ensures that only 1 flex player selected)
        self.full_roster_constraint = lpSum([
            self.players[player_name] for player_name in self.df.index]) == 9
        self.model += self.full_roster_constraint

        # --- C2 --- DST doesn't face any offensive players Constraint
        teams = self.df.team.unique()

        for x in teams:
            self.dst_opponent_constraint = 4*lpSum([self.players[player_name] for player_name in self.df[(self.df.position == 'DST') & (self.df.team == x) ].index]) + lpSum([self.players[player_name] for player_name in self.df[self.df.opponent == x].index]) <= 4
        self.model += self.dst_opponent_constraint

    def solve(self):
        # run the solver  
        book = load_workbook('INFORMS_Final_Rosters.xlsx', data_only=False)
        
        for roster_number in range(self.number_of_portfolios):
            self.model.solve()
            self.LpStatus = LpStatus[self.model.status]
            self.print_solution(roster_number, book)      
           
    def print_solution(self, roster_number, book):
        output = []
        for player_name in self.players:
            output.append({
                'player': player_name,
                'position': self.df.loc[player_name].position,
                'team': self.df.loc[player_name].team,
                'opponent': self.df.loc[player_name].opponent,
                'points': self.df.loc[player_name].points,
                'value': self.players[player_name].varValue })
            
        self.output_df = pd.DataFrame(output)
        self.add_to_df(self.output_df, roster_number)
        
        print(self.output_df[self.output_df.value == 1])
                  
        writer = pd.ExcelWriter('INFORMS_Final_Rosters.xlsx', engine = 'openpyxl')
        writer.book = book
        writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
        temp = self.output_df[self.output_df.value == 1]
        temp.to_excel(writer,sheet_name = 'Rosters',startrow = 11*roster_number, startcol = 0)
        writer.save()

    def add_to_df(self, output_df, roster_number):
        # updates self.df with the roster and then adds a constraint
        tmp = output_df.drop(columns=['position', 'team', 'opponent', 'points'])
        tmp = tmp.set_index('player')
        roster_col = 'roster{}'.format(roster_number)
        tmp.columns = [roster_col]
                     
        self.df = pd.concat([self.df, tmp], axis=1)

        # add an overlap constraint 
        overlap_constraint = lpSum([
            self.players[player_name] * self.df.loc[player_name][roster_col]
            for player_name in self.df.index]) <= self.overlap_parameter
        self.model += overlap_constraint
        
        
        
# ----------------- EXTRA CONSTRAINTS ----------------
        
        # --- C3 --- QB WR and RB from same team Constraint
        teams = self.df.team.unique()
    
#         for x in teams: #Ensure each lineup as atleast one team with 3 players from same team
#             self.qb_wr_rb_team_constraint = lpSum([
#                 self.players[player_name] 
#                 for player_name in self.df[self.df.team == x].index]) >= 3*self.stack[x]
#             self.model += self.qb_wr_rb_team_constraint 
            
#         for x in teams: #ensure the QB is one of those 3 players
#             self.qb_stacked_constraint = lpSum([
#                 self.players[player_name] for player_name in self.df[(self.df.team == x) & (self.df.position == 'QB') ].index]) >= self.stack[x]
#             self.model += self.qb_stacked_constraint
            
#         for x in teams: #ensure the WR is one of those 3 players
#             self.wr_stacked_constraint = lpSum([
#                 self.players[player_name] for player_name in self.df[(self.df.team == x) & (self.df.position == 'WR') ].index]) >= self.stack[x]
#             self.model += self.wr_stacked_constraint
            
#         for x in teams: #ensure the RB is one of those 3 players
#             self.rb_stacked_constraint = lpSum([
#                 self.players[player_name] for player_name in self.df[(self.df.team == x) & (self.df.position == 'RB') ].index]) >= self.stack[x]
#             self.model += self.rb_stacked_constraint
        
#         self.one_stacked_team_constraint = lpSum([
#             self.stack[team_name] for team_name in teams]) >= 1     #ensure its only 1 team with 3 players
#         self.model += self.one_stacked_team_constraint
               
    
#         # --- C4 --- QB WR and WR from same team Constraint
        teams = self.df.team.unique()
    
#         for x in teams: #Ensure each lineup as atleast one team with 3 players from same team
#             self.qb_wr_rb_team_constraint = lpSum([
#                 self.players[player_name] 
#                 for player_name in self.df[self.df.team == x].index]) >= 3*self.stack[x]
#             self.model += self.qb_wr_rb_team_constraint 
            
#         for x in teams: #ensure the QB is one of those 3 players
#             self.qb_stacked_constraint = lpSum([
#                 self.players[player_name] for player_name in self.df[(self.df.team == x) & (self.df.position == 'QB') ].index]) >= self.stack[x]
#             self.model += self.qb_stacked_constraint
            
#         for x in teams: #ensure the WR is two of those 3 players
#             self.wr_stacked_constraint = lpSum([
#                 self.players[player_name] for player_name in self.df[(self.df.team == x) & (self.df.position == 'WR') ].index]) >= 2*self.stack[x]
#             self.model += self.wr_stacked_constraint
        
#         self.one_stacked_team_constraint = lpSum([
#             self.stack[team_name] for team_name in teams]) >= 1     #ensure its only 1 team with 3 players
#         self.model += self.one_stacked_team_constraint

        
        # --- C5 --- Minimum budget for TE constraint
        
#         self.te_budget_constraint = lpSum([
#             self.players[player_name] * self.df.loc[player_name].salary
#             for player_name in self.df[self.df.position == 'TE'].index]) >= 5900
#         self.model += self.te_budget_constraint 


        # --- C7 --- Specifying Number of Teams Constraint
        
#         for x in teams:
#             self.players_teams_constraint = lpSum([self.players[player_name] for player_name in self.df[self.df.team == x].index]) >= self.teams[x]
#             self.players_teams_constraint = lpSum([self.players[player_name] for player_name in self.df[self.df.team == x].index]) <= 4*self.teams[x]
#             self.model += self.players_teams_constraint

#         self.num_teams_constraint = lpSum([self.teams[team_name] for team_name in teams]) == 4
#         self.model += self.num_teams_constraint




