'''
Q-learning based agent. 
All decisions are made in here
'''

Q_TABLE_FILE_PATH = "QTable.csv"

import numpy as np
import pandas as pd


class QLAgent:
    def __init__(self, actions, learning_rage=0.05,
                reward_decay=0.9, e_greedy=0.9):
        self.actions = actions  # list
        self.lr = learning_rage
        self.rd = reward_decay
        self.eps = e_greedy
        self.q_table = pd.DataFrame(columns=self.actions, dtype=np.float64)
        # self.q_table = pd.read_csv(Q_TABLE_FILE_PATH, index_col = 0, header=0)
        # change_name = {str(i): i for i in actions}
        # self.q_table.rename(columns=change_name, inplace=True)

    def CheckStateExist(self, state):
        if state not in self.q_table.index:
            self.q_table = self.q_table.append(
                pd.Series(
                    [0]*len(self.actions),
                    index=self.q_table.columns,
                    name=state,
                )
            )
    
    def ChooseAction(self, state, env, trained_num):
        # check whether the state exists
        self.CheckStateExist(state)
        if np.random.uniform() < self.eps:
            # rewards of actions in present state
            state_rewards = self.q_table.loc[state, :]
            action = np.random.choice(state_rewards[state_rewards == np.max(state_rewards)].index)
        else:
            # random
            action = np.random.choice(self.actions)
        move_set = [(0, 0), (0, -1), (-1, 0), (0, 1), (1, 0), (0, 0)]
        board = np.array(env._board)
       
       
        # 别往火上撞
        my_position = env._agents[trained_num]._character.position
        while True:
            moved_x, moved_y = move_set[action][0]+my_position[0], move_set[action][1]+my_position[1]
            if (moved_x >= 0 and moved_x < 11 and moved_y >= 0 and moved_y < 11):
                if (board[moved_x][moved_y] != 4):
                    break
                else:
                    action = np.random.choice(self.actions)
            else:
                break
        
        # 能别放炸弹就别放了8
        if (action == 5 and np.random.uniform() < 0.8): action = 0
        return action
    
    def Learn(self, state, action, rewards, state_):
        self.CheckStateExist(state_)
        q_predict = self.q_table.loc[state, action]
        if state_ != 'terminal':
            q_target = rewards + self.rd * self.q_table.loc[state_, :].max()
        else:
            q_target = rewards
        self.q_table.loc[state, action] += self.lr * (q_target - q_predict)
