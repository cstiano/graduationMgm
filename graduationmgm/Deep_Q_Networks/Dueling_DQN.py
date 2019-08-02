from collections import deque  # Ordered collection with ends

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torch.optim as optim

from graduationmgm.lib.DDQN_train import DuelingTrain


class DuelingDQN(nn.Module):
    def __init__(self, input_shape, num_outputs):
        super(DuelingDQN, self).__init__()

        self.input_shape = input_shape
        self.num_actions = num_outputs

        self.conv1 = nn.Conv1d(
            self.input_shape[0], 32, kernel_size=3, bias=False)
        self.conv2 = nn.Conv1d(32, 64, kernel_size=3, bias=False)
        self.conv3 = nn.Conv1d(64, 64, kernel_size=3, bias=False)

        self.adv1 = nn.Linear(self.feature_size(), 512)
        self.adv2 = nn.Linear(512, self.num_actions)

        self.val1 = nn.Linear(self.feature_size(), 512)
        self.val2 = nn.Linear(512, 1)

    def forward(self, x):
        x = F.relu(self.conv1(x))
        x = F.relu(self.conv2(x))
        x = F.relu(self.conv3(x))
        x = x.view(x.size(0), -1)
        adv = F.relu(self.adv1(x))
        adv = self.adv2(adv)

        val = F.relu(self.val1(x))
        val = self.val2(val)

        return val + adv - adv.mean()

    def feature_size(self):
        x = self.conv1(torch.zeros(1, *self.input_shape))
        x = self.conv2(x)
        x = self.conv3(x)
        return x.view(1, -1).size(1)


class Model(DuelingTrain):
    def __init__(self, static_policy=False, env=None, config=None):
        self.stacked_frames = deque(
            [np.zeros(env.observation_space.shape, dtype=np.int)
             for i in range(16)], maxlen=16)
        super(Model, self).__init__(static_policy, env, config)
        self.num_feats = (*self.env.observation_space.shape,
                          len(self.stacked_frames))

    def declare_networks(self):
        self.model = DuelingDQN(
            (*self.env.observation_space.shape,
             len(self.stacked_frames)), self.env.action_space.n)
        self.target_model = DuelingDQN(
            (*self.env.observation_space.shape,
             len(self.stacked_frames)), self.env.action_space.n)

    def stack_frames(self, frame, is_new_episode):
        if is_new_episode:
            # Clear our stacked_frams
            self.stacked_frames = deque([np.zeros(
                frame.shape,
                dtype=np.int) for i in range(16)], maxlen=16)

            # Because we're in a new episode, copy the same frame 4x
            for _ in range(16):
                self.stacked_frames.append(frame)

            # Stack the frames
            stacked_state = np.stack(self.stacked_frames, axis=1)

        else:
            # Append frame to deque, automatically removes the oldest frame
            self.stacked_frames.append(frame)

            # Build the stacked state (first dimension specifies different
            # frames)
            stacked_state = np.stack(self.stacked_frames, axis=1)

        return stacked_state