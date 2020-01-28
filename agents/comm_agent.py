import datetime
import gc
import itertools
import logging
import os
import pickle
import socket

import hfo
import numpy as np

from agents.base_agent import Agent
from graduationmgm.lib.hfo_env import HFOEnv
from graduationmgm.lib.utils import AsyncWrite, OUNoise

logger = logging.getLogger('Agent')


class DDPGAgent(Agent):

    memory_save_thread = None

    def __init__(self, model, per, team='base', port=6000):
        self.config_env(team, port)
        self.config_hyper(per)
        self.config_model(model)
        self.goals = 0

    def config_env(self, team, port):
        BLOCK = hfo.CATCH
        self.actions = [hfo.MOVE, hfo.GO_TO_BALL, BLOCK]
        self.rewards = [0, 0, 0]
        self.hfo_env = HFOEnv(self.actions, self.rewards,
                              strict=True, continuous=True, team=team, port=port)
        self.test = False
        self.gen_mem = True
        self.unum = self.hfo_env.getUnum()

    def load_model(self, model):
        self.ddpg = model(env=self.hfo_env, config=self.config,
                          static_policy=self.test)
        self.model_paths = (f'./saved_agents/DDPG/actor_{self.unum}.dump',
                            f'./saved_agents/DDPG/critic_{self.unum}.dump')
        self.optim_paths = (f'./saved_agents/DDPG/actor_optim_{self.unum}.dump',
                            f'./saved_agents/DDPG/critic_optim_{self.unum}.dump')
        if os.path.isfile(self.model_paths[0]) \
                and os.path.isfile(self.optim_paths[0]):
            self.ddpg.load_w(path_models=self.model_paths,
                             path_optims=self.optim_paths)
            print("Model Loaded")

    def load_memory(self):
        self.mem_path = f'./saved_agents/DDPG/exp_replay_agent_{self.unum}_ddpg.dump'
        if os.path.isfile(self.mem_path) and not self.test:
            self.ddpg.load_replay(mem_path=self.mem_path)
            self.gen_mem_end(0)
            print("Memory Loaded")

    def save_model(self, episode=0, bye=False):
        saved = False
        if (episode % 100 == 0 and episode > 0) or bye:
            self.ddpg.save_w(path_models=self.model_paths,
                             path_optims=self.optim_paths)
            print("Model Saved")
            saved = True
        return saved

    def save_mem(self, episode=0, bye=False):
        saved = False
        if episode % 5 == 0 and self.memory_save_thread is not None:
            self.memory_save_thread.join()
            self.memory_save_thread = None
        if (episode % 1000 == 0 and episode > 2 and not self.test) or bye:
            # self.ddpg.save_replay(mem_path=self.mem_path)
            # print('Memory saved')
            self.memory_save_thread = AsyncWrite(
                self.ddpg.memory, self.mem_path, 'Memory saved')
            self.memory_save_thread.start()
            saved = True
        return saved

    def save_loss(self, episode=0, bye=False):
        losses = (self.ddpg.critic_loss, self.ddpg.actor_loss)
        if (episode % 100 == 0 and episode > 0 and not self.test) or bye:
            with open(f'./saved_agents/{self.ddpg.__name__}/{self.ddpg.__name__}.loss', 'wb') as lf:
                pickle.dump(losses, lf)
                lf.close()

    def save_rewards(self, episode=0, bye=False):
        if (episode % 100 == 0 and episode > 0 and not self.test) or bye:
            with open(f'./saved_agents/{self.ddpg.__name__}/{self.ddpg.__name__}.reward', 'wb') as lf:
                pickle.dump(self.currun_rewards, lf)
                lf.close()

    def set_comm(self, messages=list(), recmsg=-1):
        HOST = '127.0.0.1'  # The server's hostname or IP address
        PORT = 65432 + self.unum  # The port used by the server

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((HOST, PORT))
            for msg in messages:
                msg = pickle.dumps(msg)
                s.sendall(msg)
            if recmsg > 0:
                recv = s.recv(recmsg)
                return pickle.loads(recv)

    def get_action(self, state, done):
        action = set_comm(messages=[state, done], recmsg=12)
        return action

    def train(self, state, action, reward, next_state, done):
        set_comm(messages=[state, action, reward, next_state, done])

    def run(self):
        self.frame_idx = 1
        self.goals = 0
        for episode in itertools.count():
            status = hfo.IN_GAME
            done = True
            episode_rewards = 0
            step = 0
            while status == hfo.IN_GAME:
                # Every time when game resets starts a zero frame
                if done:
                    state = self.hfo_env.get_state()
                    interceptable = state_ori[-1]
                action = self.get_action(state, done)

                # Calculates results from environment
                next_state, reward, done, status = self.hfo_env.step(
                    action)

                self.train(state, action, reward, next_state, done)
                episode_rewards += reward

                if done:
                    next_state = np.zeros(state.shape)
                    next_frame = np.zeros(frame.shape)
                    if episode % 100 == 0 and episode > 10 and self.goals > 0:
                        print(self.goals)
                        self.goals = 0
                else:
                    next_frame = self.ddpg.stack_frames(next_state, done)

                if status == hfo.GOAL:
                    self.goals += 1
                self.ddpg.append_to_replay(
                    frame, action, reward, next_frame, int(done))
                if not self.gen_mem and not self.test:
                    self.ddpg.update()
                frame = next_frame
                state = next_state
                if done:
                    break
                self.frame_idx += 1
            if not self.gen_mem or self.test:
                self.save_modelmem(episode)
            gc.collect()
            self.bye(status)