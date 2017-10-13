from __future__ import print_function
import argparse
import torch
import torch.optim as optim
from gcommand_loader import GCommandLoader
import numpy as np
from model import LeNet, VGG
from train import train, test
import os

# Training settings
parser = argparse.ArgumentParser(description='PyTorch MNIST Example')
parser.add_argument('--train_path', default='gcommands/train', help='path to the train data folder')
parser.add_argument('--test_path', default='gcommands/test', help='path to the test data folder')
parser.add_argument('--valid_path', default='gcommands/valid', help='path to the valid data folder')
parser.add_argument('--batch_size', type=int, default=100, metavar='N', help='training and valid batch size')
parser.add_argument('--test_batch_size', type=int, default=100, metavar='N', help='batch size for testing')
parser.add_argument('--arc', default='VGG11', help='network architecture: LeNet, VGG11, VGG13, VGG16, VGG19')
parser.add_argument('--epochs', type=int, default=10, metavar='N', help='number of epochs to train')
parser.add_argument('--lr', type=float, default=0.001, metavar='LR', help='learning rate')
parser.add_argument('--momentum', type=float, default=0.9, metavar='M', help='SGD momentum, for SGD only')
parser.add_argument('--optimizer', default='adam', help='optimization method: sgd | adam')
parser.add_argument('--cuda', default=False, help='enable CUDA')
parser.add_argument('--seed', type=int, default=1234, metavar='S', help='random seed')
parser.add_argument('--log-interval', type=int, default=10, metavar='N', help='how many batches to wait before logging training status')
parser.add_argument('--patience', type=int, default=5, metavar='N', help='how many epochs of no loss improvement should we wait before stop training')
args = parser.parse_args()

args.cuda = args.cuda and torch.cuda.is_available()
torch.manual_seed(args.seed)
if args.cuda:
    torch.cuda.manual_seed(args.seed)

# loading data
train_dataset = GCommandLoader(args.train_path)
train_loader = torch.utils.data.DataLoader(
        train_dataset, batch_size=args.batch_size, shuffle=True,
        num_workers=20, pin_memory=args.cuda, sampler=None)

valid_dataset = GCommandLoader(args.valid_path)
valid_loader = torch.utils.data.DataLoader(
        valid_dataset, batch_size=args.batch_size, shuffle=None,
        num_workers=20, pin_memory=args.cuda, sampler=None)

test_dataset = GCommandLoader(args.test_path)
test_loader = torch.utils.data.DataLoader(
        test_dataset, batch_size=args.test_batch_size, shuffle=None,
        num_workers=20, pin_memory=args.cuda, sampler=None)

# build model
if args.arc == 'LeNet':
    model = LeNet()
elif args.arc.startswith('VGG'):
    model = VGG(args.arc)
else:
    model = LeNet()

if args.cuda:
    print('Using CUDA with {0}'.format(torch.cuda.device_count()))
    torch.nn.DataParallel(model).cuda()

# define optimizer
if args.optimizer.lower() == 'adam':
    optimizer = optim.Adam(model.parameters(), lr=args.lr)
elif args.optimizer.lower() == 'sgd':
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)
else:
    optimizer = optim.SGD(model.parameters(), lr=args.lr, momentum=args.momentum)

best_valid_loss = np.inf
iteration = 0
epoch = 1

while (epoch < args.epochs + 1) and (iteration < args.patience):
    train(train_loader, model, optimizer, epoch, args.cuda, args.log_interval)
    valid_loss = test(test_loader, model, args.cuda)
    if valid_loss > best_valid_loss:
        iteration += 1
    else:
        state = {
            'net': model.module if args.cuda else model,
            'acc': valid_loss,
            'epoch': epoch,
        }
        if not os.path.isdir('checkpoint'):
            os.mkdir('checkpoint')
        torch.save(state, './checkpoint/ckpt.t7')

test(test_loader, model, args.cuda)