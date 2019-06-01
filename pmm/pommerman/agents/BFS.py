import numpy as np
from .. import utility
import queue
from collections import Counter
from .. import constants
BFS_EPISODES = 4

class BFSNode:
    def __init__(self, env, my_position, taken_action, steps):
        # action 应为 constants 中的值
        self.env = env
        self.my_position = my_position
        self.taken_action = taken_action
        self.steps = steps

    def dist_from_start(self):
        stop_num = Counter(self.taken_action)[constants.Action.Stop]
        return steps - stop_num + 1

    def first_action(self):
        return self.taken_action[1]

    def can_go(self):
        position_x, position_y = self.my_position
        if not utility.position_on_board(self.env._board, self.my_position):
            return False
        if not utility.position_is_passage(self.env._board, self.my_position):
            return False
        can_go = True
        bombs = self.env._bombs
        for bomb in bombs:
            bomb_x, bomb_y = bomb.position
            safe_from_bomb = False
            if (bomb_x == position_x and abs(bomb_y - position_y) <= bomb.blast_strength):
                for pix_y in range(bomb_y, position_y):
                    if utility.position_is_wall(self.env._board, (position_x, pix_y)):
                        safe_from_bomb = True
                        break                     
            elif (bomb_y == position_y and abs(bomb_x - position_x) <= bomb.blast_strength):
                for pix_x in range(bomb_x, position_x):
                    if utility.position_is_wall(self.env._board, (pix_x, position_y)):
                        safe_from_bomb = True
                        break
            if not safe_from_bomb:
                can_go = False
        return can_go
                

def BFS_when_unsafe(my_position, env, trained_num=0):
    board = np.array(env._board)
    visted = set()
    q = queue.Queue()
    q.put(BFSNode(env, my_position, [constants.Action.Stop], 0))
    ret = []
    while not q.empty():
        temp_node = q.get()
        temp_env = temp_node.env
        visted.add(temp_node.my_position)
        if not temp_node.can_go():
            continue
        if temp_node.steps == BFS_EPISODES:
            ret.append(temp_node)
            continue
        for row, col in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            assume_actions = [
                constants.Action.Stop, constants.Action.Stop,
                constants.Action.Stop
            ]
            new_position = (temp_node.my_position[0] + row, temp_node.my_position[1] + col)
            if new_position in visted:
                continue
            action = utility.get_direction(temp_node.my_position, new_position)
            actions = assume_actions.insert(trained_num, action)
            temp_env.step(actions)
            q.put(BFSNode(temp_env, new_position, temp_node.taken_action.append(action), temp_node.steps+1))     
    
    ret.sort(key=lambda x: x.dist_from_start())
    return ret[0].first_action()
