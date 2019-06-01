import numpy as np
import pommerman.utility as utility
import queue
from collections import Counter
import pommerman.constants as constants
BFS_EPISODES = 4


class BFSNode:
    def __init__(self, env, my_position, taken_action, steps):
        self.env = env
        self.my_position = my_position
        self.taken_action = taken_action
        self.steps = steps

    def dist_from_start(self):
        stop_num = Counter(self.taken_action)[constants.Action.Stop]
        return self.steps - stop_num + 1

    def first_action(self):
        return self.taken_action[1]


def CanGo(bfs_node, action, enemies):
    position_x, position_y = utility.get_next_position(bfs_node.my_position, action)
    if not utility.is_valid_direction(bfs_node.env._board, (position_x, position_y), action):
        return False
    if not utility.position_is_passable(bfs_node.env._board, (position_x, position_y), enemies):
        return False
    can_go = True
    bombs = bfs_node.env._bombs
    for bomb in bombs:
        bomb_x, bomb_y = bomb.position
        safe_from_bomb = False
        if bomb.life > bomb.blast_strength + 2: continue
        if (bomb_x == position_x and abs(bomb_y - position_y) <= bomb.blast_strength):
            for pix_y in range(min(bomb_y, position_y), max(bomb_y, position_y)):
                if utility.position_is_wall(bfs_node.env._board, (position_x, pix_y)):
                    safe_from_bomb = True
                    break                     
        elif (bomb_y == position_y and abs(bomb_x - position_x) <= bomb.blast_strength):
            for pix_x in range(min(bomb_x, position_x), max(bomb_x, position_x)):
                if utility.position_is_wall(bfs_node.env._board, (pix_x, position_y)):
                    safe_from_bomb = True
                    break
        else:
            continue
        if not safe_from_bomb:
            can_go = False
    return can_go
            

def BFS_when_unsafe(my_position, env, enemies, trained_num=0):
    q = queue.Queue()
    q.put(BFSNode(env, my_position, [constants.Action.Stop], 0))
    ret = []
    while not q.empty():
        temp_node = q.get()
        if temp_node.steps >= BFS_EPISODES:
            ret.append(temp_node)
            continue
        for row, col in [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)]:
            new_position = (temp_node.my_position[0] + row, temp_node.my_position[1] + col)
            if row == 0 and col == 0:
                action = constants.Action.Stop
            else:
                action = utility.get_direction(temp_node.my_position, new_position)
            if CanGo(temp_node, action, enemies):
                q.put(BFSNode(temp_node.env, new_position, temp_node.taken_action+[action], temp_node.steps+1))     
    
    ret.sort(key=lambda x: x.dist_from_start())
    return ret
