import pommerman
from pommerman import agents


def main():
    print(pommerman.REGISTRY)

    # Create a set of agents (exactly four)
    agent_list = [
        agents.PlayerAgent(agent_control="arrows"),
        agents.SimpleAgent(),
        agents.SimpleAgent(),
        agents.SimpleAgent()
    ]

    # Play with AI with agent list bellow
    # agent_list = [
    # agents.SimpleAgent(),
    # agents.PlayerAgent(agent_control="arrows"), # Arrows = Move, Space = Bomb
    # agents.SimpleAgent(),
    # agents.PlayerAgent(agent_control="wasd"), # W,A,S,D = Move, E = Bomb
    # ]

    # Make the "Free-For-All" environment using the agent list
    env = pommerman.make('PommeFFACompetition-v0', agent_list)

    # Run the episodes just like OpenAI Gym
    for i_episode in range(3):
        state = env.reset()
        done = False
        while not done:
            env.render()
            actions = env.act(state)
            state, reward, done, info = env.step(actions)
        print('Episode {} finished'.format(i_episode))
    env.close()


if __name__ == '__main__':
    main()