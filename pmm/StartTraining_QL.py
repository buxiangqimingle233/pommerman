import pommerman
from pommerman import agents
import numpy as np 
from QL import QLAgent
from Encode import EncodingState

EPISODE = 100
ACTIONS = [0, 1, 2, 3, 4, 5]

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
    my_agent = QLAgent(ACTIONS)

    # Run the episodes just like OpenAI Gym
    lose_cnt = 0
    for i_episode in range(EPISODE):
        state = env.reset()
        done = False
        step_count = 0
        while not done:
            step_count += 1
            # fresh env
            env.render()
            encoded_state = EncodingState(state, env, train_agent_number)

            # for simple agents making decisions
            actions = env.act(state)
            
            # RL make decision based on present state
            agent_action = my_agent.ChooseAction(str(encoded_state.coding), env, train_agent_number)

            actions.insert(train_agent_number, agent_action)

            # get next state
            state_, reward, done, info = env.step(actions)

            # learn from states
            agent_reward = reward[0]
            encoded_state_ = EncodingState(state_, env, train_agent_number)
            if done:
                print(reward)
                my_agent.Learn(str(encoded_state.coding), agent_action, agent_reward, 'terminal')
            else:
                my_agent.Learn(str(encoded_state.coding), agent_action, agent_reward, str(encoded_state_.coding))
            if done and agent_reward == -1:
                lose_cnt += 1
            # print("#####################")
            # print("coding:", encoded_state.coding, encoded_state_.coding)
            # print("actions:", actions)
            # print("rewards:", reward)
            # print("#####################")       
        # print('Episode {} finished'.format(i_episode))
    env.close()
    print("lose rate: ", lose_cnt / float(EPISODE))
    my_agent.q_table.to_csv('QTable.csv')


if __name__ == '__main__':
    main()