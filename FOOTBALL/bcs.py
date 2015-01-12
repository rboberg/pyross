# -*- coding: utf-8 -*-
"""
Created on Tue Jan 06 15:10:54 2015

@author: Ross
"""

from bs4 import BeautifulSoup
import urllib2
import pandas as pd
import re

year = 2014
url = 'http://www.sports-reference.com/cfb/years/' + str(year) + '-schedule.html'

content = urllib2.urlopen(url).read()

soup = BeautifulSoup(content)

table = soup.find('table', attrs={'id':'schedule'})

thead = table.find('thead')
fields = [th.attrs['data-stat'] for th in thead.find('tr').findAll('th')]

tbody = table.find('tbody')

valid_tr = tbody.findAll(lambda tag:tag.name == 'tr' and not('thead' in tag['class']))

rows = []
for tr in valid_tr:
    row_vals = [td.getText() for td in tr.findAll('td')]
    rows.append(dict(zip(fields,row_vals)))

df = pd.DataFrame(rows)

reg = re.compile('^\(.*\)\W*')

# remove postponed games
completed = df['winner_points'].map(lambda x: x != '')
df = df[completed]
df = df.reindex(index=range(df.shape[0]))

df['winner_school_name'] = df['winner_school_name'].replace(reg,'')
df['loser_school_name'] = df['loser_school_name'].replace(reg,'')
df['winner_points'] = df['winner_points'].astype(float)
df['loser_points'] = df['loser_points'].astype(float)

# see how many games each team played
team_games = df['winner_school_name'].append(df['loser_school_name']).value_counts()

# check ot distributon of team games
team_games.value_counts()

# introduce number of game cutoff for team inclusion
cutoff = 10

# check valid teams
valid_teams = team_games.index[team_games > cutoff]

# restrict to valid teams
valid_win = df['winner_school_name'].isin(valid_teams)
valid_loss = df['loser_school_name'].isin(valid_teams)

df = df[(valid_win) & (valid_loss)]
df = df.reindex(index=range(df.shape[0]))

# Make unique list of team names
teams = df['winner_school_name'].append(df['loser_school_name']).unique().tolist()
nteam = len(teams)
ngame = df.shape[0]

# Create data frame with a row for each game, column for each team
regdf = pd.DataFrame([[0]*nteam]*ngame,columns=teams)

# Add +1 for winners, -1 for losers
windex = [teams.index(team) for team in df['winner_school_name']]
losdex = [teams.index(team) for team in df['loser_school_name']]

for i in range(len(windex)):
    regdf.iloc[i,windex[i]] = 1
    regdf.iloc[i,losdex[i]] = -1

# Get results winner points - loser points
results = df['winner_points'] - df['loser_points']

# Run regression
ols_out = pd.ols(y=results, x=regdf)

ols_out.beta
ols_out.beta.order()

res = pd.DataFrame({'beta':ols_out.beta, 'se':ols_out.std_err})

res.order('beta')