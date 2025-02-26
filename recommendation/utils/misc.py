import os
import cv2
import random
import numpy as np
from collections import OrderedDict

import torch


def set_random_seed(seed):
    np.random.seed(seed)
    random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


class AverageMeter(object):
    """Computes and stores the average and current value"""

    def __init__(self):
        self.val = None
        self.avg = None
        self.sum = None
        self.count = None
        self.reset()

    def reset(self):
        self.val = 0
        self.avg = 0
        self.sum = 0
        self.count = 0

    def update(self, val, n=1):
        self.val = val
        self.sum += val * n
        self.count += n
        self.avg = self.sum / self.count



def save_network_checkpoint(ckpt_dir, assess_net):
    os.makedirs(ckpt_dir, exist_ok=True)
    dict_network = assess_net.state_dict()
    new_state_dict = OrderedDict()
    for k, v in dict_network.items():
        name = k[7:] if 'module' in k else k  # remove `module.`
        new_state_dict[name] = v.clone().detach().to('cpu')
    torch.save(dict_network, os.path.join(ckpt_dir, 'assess_net.pt'))



def load_network_checkpoint(ckpt_path, encoder=None, device='cpu', strict=True):
    flag_encoder = False
    state_dict_encoder = torch.load(
        ckpt_path) if os.path.exists(ckpt_path) else None

    if state_dict_encoder is not None:
        new_state_dict_encoder = OrderedDict()
        for k, v in state_dict_encoder.items():
            if device == 'cpu' and 'module' in k:
                name = k[7:]  # remove `module.`
            elif device == 'gpu' and 'module' not in k:
                name = 'module.' + k
            else:
                name = k
            new_state_dict_encoder[name] = v
        encoder.load_state_dict(new_state_dict_encoder, strict=strict)
        flag_encoder = True
    return flag_encoder


def save_agent_checkpoint(net, ckpt_dir, epoch=None, weight_name='agent.pt'):
    agent_ckpt_path = os.path.join(ckpt_dir, weight_name if epoch is None else f'agent_epoch_{epoch}.pt')

    os.makedirs(ckpt_dir, exist_ok=True)

    state_dict = net.state_dict()

    new_state_dict = OrderedDict()
    for k, v in state_dict.items():
        name = k[7:] if 'module' in k else k  # remove `module.`
        new_state_dict[name] = v.clone().detach().to('cpu')

    torch.save(state_dict, agent_ckpt_path)



def load_agent_checkpoint(agent, ckpt_dir, device='cpu', strict=False, weight_name='agent.pt'):
    if agent is None:
        return
    agent_ckpt_path = os.path.join(ckpt_dir, weight_name)
    print(agent_ckpt_path)
    if not os.path.exists(agent_ckpt_path):
        print(f"no model found in {agent_ckpt_path}")
        return
    else:
        print(f"load agent model from {agent_ckpt_path}")

    try:
        state_dict = torch.load(agent_ckpt_path)
        new_state_dict = OrderedDict()
        for k, v in state_dict.items():
            if 'module' in k:  # remove 'module' first
                k = k[7:]
            if 'base' in k and 'encoder' not in k:  # from video_match ckpt
                k = 'encoder.' + k
            if str(device) == 'cuda':
                k = 'module.' + k
            new_state_dict[k] = v
        agent.policy_net.load_state_dict(new_state_dict, strict=strict)
        flag = 1
    except:
        print(f"catch some EXCEPTION when trying to load {agent_ckpt_path}")
        flag = -1
    return flag





def save_seg_preds(probs, new_masks_meta, save_result_dir):

    sequence = new_masks_meta["sequence"]
    n_interaction = new_masks_meta["n_interaction"]
    scribble_iter = new_masks_meta["scribble_iter"]
    save_dir_res_probs = os.path.join(save_result_dir, 'interaction-{}'.format(n_interaction),
                                      'scribble-{}'.format(scribble_iter), sequence, 'probs')
    os.makedirs(save_dir_res_probs, exist_ok=True)

    # Save the concatted result, attention to the index i
    for i in range(int(probs.shape[0])):
        # 1 x (O+1) x H x W
        n_objects = probs[i:i+1].shape[1] - 1
        for n in range(1, n_objects + 1):
            save_dir_res_probs_subpath = os.path.join(save_dir_res_probs, f'{n}')
            os.makedirs(save_dir_res_probs_subpath, exist_ok=True)
            cv2.imwrite(os.path.join(save_dir_res_probs_subpath, f'{i}'.zfill(5) + '.png'), probs[i, n] * 255)
