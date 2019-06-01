import copy
import pommerman
import sys
# import utility

from pommerman import agents
import numpy as np 
from pommerman.agents.my_agent import MyAgent
from Encode import EncodingState

EPISODE = 50
ACTIONS = [0, 1, 2, 3, 4, 5]

sys.setrecursionlimit(2000)
# You just need to complete this function


def main():
    """Simple function to bootstrap a game"""
    # Print all possible environments in the Pommerman registry
    print(pommerman.REGISTRY)

    # Create a set of agents (exactly four)
    agent_list = [
        agents.SimpleAgent(),
        agents.SimpleAgent(),
        agents.SimpleAgent(),
    ]
    train_agent_number = 0
    agent_list.insert(train_agent_number, agents.BaseAgent())
    
    # Make the "Free-For-All" environment using the agent list
    env = pommerman.make('PommeFFACompetition-v0', agent_list)
    env.set_training_agent(train_agent_number)
    my_agent = MyAgent()

    lose_cnt = 0
    # Run the episodes just like OpenAI Gym
    for i_episode in range(EPISODE):
        state = env.reset()
        done = False
        step_cnt = 1
        while not done:
            step_cnt += 1
            if (step_cnt >= 500): break
            # fresh env
            env.render()
            # for simple agents making decisions
            actions = env.act(state)
            
            agent_action = 0
            # RL make decision based on present state
            agent_action = my_agent.act(state[train_agent_number], ACTIONS)
            
            actions.insert(train_agent_number, agent_action)

            # get next state
            state, reward, done, info = env.step(actions)

            # learn from states
            agent_reward = reward[train_agent_number]
            if done:
                if agent_reward == -1:
                    lose_cnt += 1
                    print("lose")
                else:
                    print("win")
    env.close()
    print("win rate: ", 1 - lose_cnt / float(EPISODE))


if __name__ == '__main__':
    main()