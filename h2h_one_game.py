import pandas as pd
import sys

class Draft:

	def __init__(self, draft_order, players, drafter_one, drafter_two):
		self.draft_order = draft_order
		self.players = players
		self.drafter_one = drafter_one
		self.drafter_two = drafter_two

	def run_rounds(self):
		for on_the_clock in self.draft_order:
			if (on_the_clock == 1):
				self.players = self.drafter_one.draft_player(self.players, drafter_two)
			elif (on_the_clock == 2):
				self.players = self.drafter_two.draft_player(self.players, drafter_one)
		print("Player 1 Team")
		print()
		print(drafter_one.players)
		print()
		d_one_proj_points = drafter_one.roster_points()
		print("P1 Total Projected Points: " + str(d_one_proj_points))
		print()
		print()
		print(drafter_two.players)
		print()
		d_two_proj_points = drafter_two.roster_points()
		print("P2 Total Projected Points: " + str(d_two_proj_points))
		print()
		print()
		print("Total Expected Difference: " + str(d_one_proj_points - d_two_proj_points))


class Drafter:

	def __init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num):
		self.max_qb = max_qb
		self.max_wr = max_wr
		self.max_rb = max_rb
		self.max_te = max_te
		self.max_flex = max_flex
		self.roster_max = max_qb + max_wr + max_rb + max_te + max_flex
		self.players = pd.DataFrame()
		self.drafted_qbs = 0
		self.drafted_wrs = 0
		self.drafted_rbs = 0
		self.drafted_tes = 0
		self.drafted_flex = 0
		self.draft_num = draft_num

	def draft_player(self, remaining_players, opponent):
		eligible_players = self.remove_uneligible(remaining_players)
		drafted_player = self.drafter_logic(eligible_players, opponent)
		updated_players = remaining_players[remaining_players['name'] != drafted_player['name']]
		self.players = pd.concat([self.players, drafted_player], axis = 1)
		self.update_roster(drafted_player['position'])
		print("Player " + str(self.draft_num) + " drafted:")
		print(drafted_player[0:3])
		print()
		return updated_players

	def remove_uneligible(self, remaining_players):
		is_flex_maxed = (self.drafted_flex == self.max_flex)
		if self.max_qb == self.drafted_qbs:
			remaining_players = remaining_players[remaining_players['position'] != 'QB']
		if (self.max_wr == self.drafted_wrs) and is_flex_maxed:
			remaining_players = remaining_players[remaining_players['position'] != 'WR']
		if (self.max_rb == self.drafted_rbs) and is_flex_maxed:
			remaining_players = remaining_players[remaining_players['position'] != 'RB']
		if (self.max_te == self.drafted_tes) and is_flex_maxed:
			remaining_players = remaining_players[remaining_players['position'] != 'TE']
		return remaining_players

	def drafter_logic(self, eligible_players, opponent):
		max_index = eligible_players['projected_points'].idxmax()
		max_player = eligible_players.loc[max_index]
		return max_player
	
	def update_roster(self, player_position):
		match player_position:
			case 'QB':
				self.drafted_qbs += 1
				return
			case 'WR':
				if self.drafted_wrs == self.max_wr:
					self.drafted_flex += 1
				else:
					self.drafted_wrs += 1
			case 'RB':
				if self.drafted_rbs == self.max_rb:
					self.drafted_flex += 1
				else:
					self.drafted_rbs += 1
			case 'TE':
				if self.drafted_tes == self.max_te:
					self.drafted_flex += 1
				else:
					self.drafted_tes += 1

	def roster_points(self):
		print(self.players.shape[1])
		print(self.players.shape[0])
		self.roster_total = self.players.iloc[1].sum(axis=0)
		return self.roster_total

	def new_draft(self, draft_num):
		self.drafted_qbs = 0
		self.drafted_wrs = 0
		self.drafted_rbs = 0
		self.drafted_tes = 0
		self.drafted_flex = 0
		self.players = pd.DataFrame()
		self.draft_num - draft_num


class QB_Logical_Drafter(Drafter):

	def __init__ (self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num):
		Drafter.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num)
	
	def drafter_logic(self, eligible_players, opponent):
		if (self.drafted_qbs == 0) and (opponent.drafted_qbs == 1) and (self.players.shape[1] < (self.roster_max - 1)):
			remove_qb = eligible_players[eligible_players['position'] != 'QB']
			return Drafter.drafter_logic(self, remove_qb, opponent)
		return Drafter.drafter_logic(self, eligible_players, opponent)

class RB_Thief(QB_Logical_Drafter):

	def __init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, rb_start_poach):
		QB_Logical_Drafter.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num)
		self.rb_start_poach = rb_start_poach
		if (draft_num == 1):
			self.thief_sequence_start = [1,3]
		elif (draft_num == 2):
			self.thief_sequence_start = [0,2,4]

	def drafter_logic(self, eligible_players, opponent):
		if self.players.shape[1] >= self.rb_start_poach and self.drafted_flex == 0:
			if opponent.drafted_rbs == 0:
				if self.players.shape[1] in self.thief_sequence_start:
					return self.rb_steal_logic(eligible_players, opponent)
				elif self.drafted_rbs == 1:
					return self.rb_steal_logic(eligible_players, opponent)

		return QB_Logical_Drafter.drafter_logic(self, eligible_players, opponent)

	def rb_steal_logic(self, eligible_players, opponent):
		rbs = eligible_players.loc[eligible_players['position'] == 'RB']
		max_index = rbs['projected_points'].idxmax()
		max_player = rbs.loc[max_index]
		return max_player

class TE_Thief(QB_Logical_Drafter):

	def __init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, te_start_poach):
		QB_Logical_Drafter.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num)
		self.te_start_poach = te_start_poach
		if (draft_num == 1):
			self.thief_sequence_start = [1,3]
		elif (draft_num == 2):
			self.thief_sequence_start = [0,2,4]

	def drafter_logic(self, eligible_players, opponent):
		if self.players.shape[1] >= self.te_start_poach and self.drafted_flex == 0:
			if opponent.drafted_tes == 0:
				if self.players.shape[1] in self.thief_sequence_start:
					return self.te_steal_logic(eligible_players, opponent)
				elif self.drafted_tes == 1:
					return self.te_steal_logic(eligible_players, opponent)

		return QB_Logical_Drafter.drafter_logic(self, eligible_players, opponent)

	def te_steal_logic(self, eligible_players, opponent):
		tes = eligible_players.loc[eligible_players['position'] == 'TE']
		max_index = tes['projected_points'].idxmax()
		max_player = tes.loc[max_index]
		return max_player

class General_Thief(RB_Thief, TE_Thief):

	def __init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, te_start_poach, rb_start_poach, preference):
		RB_Thief.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, rb_start_poach)
		TE_Thief.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, te_start_poach)
		self.preference = preference

	def drafter_logic(self, eligible_players, opponent):

		if (self.preference == "RB"):
			if self.players.shape[1] >= self.rb_start_poach and self.drafted_flex == 0:
				if opponent.drafted_rbs == 0:
					if self.players.shape[1] in self.thief_sequence_start:
						return self.rb_steal_logic(eligible_players, opponent)
					elif self.drafted_rbs == 1:
						return self.rb_steal_logic(eligible_players, opponent)
			if self.players.shape[1] >= self.te_start_poach and self.drafted_flex == 0:	
				if opponent.drafted_tes == 0:
					if self.players.shape[1] in self.thief_sequence_start:
						return self.te_steal_logic(eligible_players, opponent)
					elif self.drafted_tes == 1:
						return self.te_steal_logic(eligible_players, opponent)
			return QB_Logical_Drafter.drafter_logic(self, eligible_players, opponent)
		elif (self.preference == "TE"):
			if self.players.shape[1] >= self.te_start_poach and self.drafted_flex == 0:
				if opponent.drafted_tes == 0:
					if self.players.shape[1] in self.thief_sequence_start:
						return self.te_steal_logic(eligible_players, opponent)
					elif self.drafted_tes == 1:
						return self.te_steal_logic(eligible_players, opponent)
			if self.players.shape[1] >= self.rb_start_poach and self.drafted_flex == 0:
				if opponent.drafted_rbs == 0:
					if self.players.shape[1] in self.thief_sequence_start:
						return self.rb_steal_logic(eligible_players, opponent)
					elif self.drafted_rbs == 1:
						return self.rb_steal_logic(eligible_players, opponent)
			return QB_Logical_Drafter.drafter_logic(self, eligible_players, opponent)	
		else:
			raise Exception("Invalid Preference")

class Largest_Gap(QB_Logical_Drafter):

	def __init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num):
		QB_Logical_Drafter.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num)

	def drafter_logic(self, eligible_players, opponent):
		rbs = eligible_players.loc[eligible_players['position'] == 'RB']
		tes = eligible_players.loc[eligible_players['position'] == 'TE']
		wrs = eligible_players.loc[eligible_players['position'] == 'WR']
		qbs = eligible_players.loc[eligible_players['position'] == 'QB']

		if (self.drafted_qbs == self.max_qb or opponent.drafted_qbs == self.max_qb):
			qb_diff = 0
		else:
			qb_diff = self.position_diff(eligible_players, 'QB', 1)

		if (self.drafted_rbs == self.max_rb and self.drafted_flex == self.max_flex) or ((opponent.drafted_rbs == self.max_rb and opponent.drafted_flex == self.max_flex) or (self.drafted_rbs == self.max_rb and opponent.drafted_rbs == self.max_rb)):
			rb_diff = 0
		else:
			rb_diff = self.position_diff(eligible_players, 'RB', 1)

		if (self.drafted_tes == self.max_te and self.drafted_flex == self.max_flex) or ((opponent.drafted_tes == self.max_te and opponent.drafted_flex == self.max_flex) or (self.drafted_tes == self.max_te and opponent.drafted_tes == self.max_te)):
			te_diff = 0
		else:
			te_diff = self.position_diff(eligible_players, 'TE', 1)

		if (self.drafted_wrs == self.max_wr and self.drafted_flex == self.max_flex) or ((opponent.drafted_wrs == self.max_wr and opponent.drafted_flex == self.max_flex) or (self.drafted_wrs == self.max_wr and opponent.drafted_wrs == self.max_wr)):
			wr_diff = 0
		else:
			wr_diff = self.position_diff(eligible_players, 'WR', 1)

		if (qb_diff == 0 and rb_diff == 0) and (te_diff == 0 and wr_diff == 0):
			return QB_Logical_Drafter.drafter_logic(self, eligible_players, opponent)
		elif all(qb_diff > x for x in [rb_diff, te_diff, wr_diff]):
			max_index = qbs['projected_points'].idxmax()
			max_player = qbs.loc[max_index]
		elif all(rb_diff > x for x in [qb_diff, te_diff, wr_diff]):
			max_index = rbs['projected_points'].idxmax()
			max_player = rbs.loc[max_index]
		elif all(te_diff > x for x in [rb_diff, qb_diff, wr_diff]):
			max_index = tes['projected_points'].idxmax()
			max_player = tes.loc[max_index]
		else:
			max_index = wrs['projected_points'].idxmax()
			max_player = wrs.loc[max_index]			

		return max_player	

	def position_diff(self, eligible_players, position, depth):

		position_players = eligible_players.loc[eligible_players['position'] == position]

		print(depth)
		max_points = position_players['projected_points'].nlargest(depth).iloc[-1]
		second_max = position_players['projected_points'].nlargest(depth+1).iloc[-1]

		return (max_points - second_max)

# class Thief_Gap(General_Thief, Largest_Gap):

# 	def __init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, te_start_poach, rb_start_poach, preference):
# 		General_Thief.__init__(self, max_qb, max_wr, max_rb, max_te, max_flex, draft_num, te_start_poach, rb_start_poach, preference)

# 	def drafter_logic(self, eligible_players, opponent):
# 		big_gap_player = Largest_Gap.drafter_logic(self, eligible_players, opponent)
# 		biggest_gap_difference = self.position_diff(eligible_players, big_gap_player['position'], 1)

# 		rb_thief_difference = self.position_diff(eligible_players, 'RB', 2)
# 		te_thief_difference = self.position_diff(eligible_players, 'TE', 2)


# 		if (biggest_gap_difference > x for x in [rb_thief_difference, te_thief_difference]):
# 			return big_gap_player
# 		elif (rb_thief_difference > x for x in [biggest_gap_difference, te_thief_difference]):
# 			return RB_Thief.drafter_logic(self, eligible_players, opponent)
# 		else:
# 			return TE_Thief.drafter_logic(self, eligible_players, opponent)


#drafter_one = Drafter(1, 2, 1, 1, 1, 1)
#drafter_two = Drafter(1, 2, 1, 1, 1, 2)
#drafter_one = RB_Thief(1, 2, 1, 1, 1, 1, 0)
#drafter_two = RB_Thief(1, 2, 1, 1, 1, 2, 0)
drafter_one = RB_Thief(1, 2, 1, 1, 1, 1, 0)
drafter_two = Largest_Gap(1, 2, 1, 1, 1, 2)

draft_order = [1,2,2,1,1,2,2,1,1,2,2,1]
contest_players = pd.read_csv(sys.argv[1])

new_draft = Draft(draft_order, contest_players, drafter_one, drafter_two)
new_draft.run_rounds()


