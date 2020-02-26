#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 08:09:12 2020

@author: liyuan
"""

import numpy as np
import matplotlib.pyplot as plt


global player_counter
player_counter = 0

global match_counter
match_counter = 0

class Player:
	def __init__(self):
		'''assume players mmr follow a normal distribution centered around 3k with 1k variance. 
		Distribution seems reasonable from histogram - tails around 0 and 6k'''
		
		self.mmr = round(np.random.normal(0,1)*1000,-1)+3000
		self.waitingTime = 0
		global player_counter
		player_counter = player_counter+1		
		self.index = player_counter

	def __str__(self):
		a = '{:>20s} : {:<10f}'.format('mmr',self.mmr)
		b = '{:>20s} : {:<10f}'.format('wait time',self.waitingTime)
		c = '{:>20s} : {:<10f}'.format('index',self.index)
#		print('{:>20s}:{:<10f}'.format('mmr',self.mmr))
#		print('{:>20s}:{:<10f}'.format('wait time',self.waitingTime))
		return a+'\n'+b + '\n' +c



class Matchmaker:
	def __init__(self, num_players = 5000):
		self.players = []
		for i in range(num_players):
			self.players.append(Player())
		self.sort()
		self.hist()
		
	def sort(self):
		idx = np.argsort(self.get_mmr())
		self.players = [self.players[i] for i in idx]
			
	def hist(self):
		plt.hist(self.get_mmr(),bins = 30)
		
	def get_mmr(self):
		return np.array([p.mmr for p in self.players])
	
	def pop(self,i):
		p = self.players.pop(i)
		return p 
	
	
class Match:
	def __init__(self):
		global match_counter
		match_counter = match_counter + 1
		self.match_id = match_counter
		self.players = []
		
	def add_player(self,player):
		self.players.append(player)
	
	def __str__(self):
		a = '{:>20s} : {:<10f}'.format('match id',self.match_id)
		b = '{:>20s} : {}'.format('mmr',','.join([str(int(p.mmr)) for p in self.players]))		
		c = '{:>20s} : {}'.format('player id',','.join([str(p.index) for p in self.players]))

		return a+'\n'+b + '\n' + c
	


matchmaker = Matchmaker(50)

matches = []

## matchmaking
'''matchmaking: randomly choose a player and get 9 more players with nearest mmr'''


while len(matchmaker.players)>=10:
	match = Match()
	idx = np.random.randint(len(matchmaker.players))
	player_mmr = matchmaker.players[idx].mmr
	match.add_player(matchmaker.pop(idx))
	
	for _ in range(9):
		centered_mmr = abs(matchmaker.get_mmr() - player_mmr)
		nearest_mmr = np.argmin(centered_mmr)
		match.add_player(matchmaker.pop(nearest_mmr))
	
	print(match)
	print('')
	matches.append(match)
	
print('finished matching players.. remaining players in queue:{}'.format(len(matchmaker.players)))