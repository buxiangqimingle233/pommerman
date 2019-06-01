import numpy as np


CODING_SIZE = 6

# coding bits
IN_DANGER = 0
ONE_STEP = 1
TWO_STEP = 2
THR_STEP = 3
AVL_CHOICE = 4
NEAR_ENEMY = 5
# NEAR_FLAME = 6
BOMB = 3


class EncodingState:
    def __init__(self, states, env, trained_num):
        self.states = np.array(env._board)
        self.my_agent = env._agents[trained_num]._character   
        self.enemy = [env._agents[i]._character for i in range(0, 4) if i != trained_num]
        self.bombs = env._bombs
        self.flames = env._flames
        self.coding = [0 for i in range(CODING_SIZE)]
        self.InDanger()
        self.Steps()
        self.NearEnemy()
        self.AvailableChoice()

    def CalDistance(self, itemA, itemB):
        # naive strategy
        return abs(itemA[0]-itemB[0]) + abs(itemA[1]-itemB[1])
    
    def InDanger(self):
        my_location = self.my_agent.position
        for bomb in self.bombs:
            if bomb.life == 1:
                if (bomb.position[0] == my_location[0] and bomb.position[1] == my_location[1]):
                    self.coding[IN_DANGER] = 5
                elif (bomb.position[0] == my_location[0]):
                    if (bomb.position[1] < my_location[1]): 
                        self.coding[IN_DANGER] = 1  # up
                    elif (bomb.position[1] >= my_location[1]):
                        self.coding[IN_DANGER] = 2  # down
                elif (bomb.position[1] == my_location[1]):
                    if (bomb.position[0] < my_location[0]): 
                        self.coding[IN_DANGER] = 3  # left
                    elif (bomb.position[0] >= my_location[0]):
                        self.coding[IN_DANGER] = 4  # right=

    def Steps(self):
        my_location = self.my_agent.position
        min_time_1, min_time_2, min_time_3 = 100, 100, 100
        for bomb in self.bombs:
            if self.CalDistance(bomb.position, my_location) <= 1:
                min_time_1 = min(min_time_1, bomb.life)
            if self.CalDistance(bomb.position, my_location) <= 2:
                min_time_2 = min(min_time_2, bomb.life)
            if self.CalDistance(bomb.position, my_location) <= 3:
                min_time_3 = min(min_time_3, bomb.life)
        if (min_time_1 <= 1):
            self.coding[ONE_STEP] = 1
        if (min_time_2 <= 2):
            self.coding[TWO_STEP] = 1
        if (min_time_3 <= 3):
            self.coding[THR_STEP] = 1

    def NearEnemy(self):
        my_location = self.my_agent.position
        for i in range(-1, 1):
            for j in range(-1, 1):
                if (i == 0 and j == 0): continue
                moved_x, moved_y = my_location[0]+i, my_location[1] + j
                if (self.states[moved_x][moved_y] >= 10):
                    self.coding[NEAR_ENEMY] = 1
                    return

    def AvailableChoice(self):
        my_location = self.my_agent.position
        move_set = [(0,1), (0,-1), (1,0), (-1,0)]
        cnt = 0
        for move in move_set:
            moved_x, moved_y = my_location[0]+move[0], my_location[1]+move[1]
            if (self.states[moved_x][moved_y] == 0):
                cnt += 1
        self.coding[AVL_CHOICE] = cnt        
