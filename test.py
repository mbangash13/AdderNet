# 2020.01.10-Changed for testing AdderNets
#            Huawei Technologies Co., Ltd. <foss@huawei.com>

import argparse
import os
import torch
import torch.backends.cudnn as cudnn
import torchvision.transforms as transforms
import torchvision.datasets as datasets

parser = argparse.ArgumentParser(description='PyTorch MNIST and ImageNet Testing for AdderNet')
parser.add_argument('--dataset', type=str, default='mnist', choices=['mnist', 'cifar10', 'ImageNet'],
                    help='Dataset to use: mnist, cifar10, or ImageNet')
parser.add_argument('-j', '--workers', default=4, type=int, metavar='N',
                    help='Number of data loading workers (default: 4)')
parser.add_argument('-b', '--batch-size', default=256, type=int,
                    metavar='N',
                    help='Mini-batch size (default: 256)')
parser.add_argument('--data_dir', type=str, help='Path to dataset', default="./data/")
parser.add_argument('--model_dir', type=str, help='Path to saved model', default="models/addernet.pth")
args, unparsed = parser.parse_known_args()
best_acc1 = 0
args, unparsed = parser.parse_known_args()

def main():

    # create model
    if args.dataset == 'mnist':
        import resnet20
        model = resnet20.resnet20()
    elif args.dataset == 'ImageNet':
        import resnet50
        model = resnet50.resnet50()


    model = torch.load(args.model_dir)
  
    model = torch.nn.DataParallel(model).cuda()
    
    cudnn.benchmark = True

    # Data loading code
    
    if args.dataset == 'mnist':
       val_loader = torch.utils.data.DataLoader(
        datasets.MNIST(args.data_dir, train=False,download=True, transform=transforms.Compose([
            transforms.Resize((32, 32)),
            transforms.ToTensor(),
            transforms.Normalize((0.1307,), (0.3081,))
        ])),
        batch_size=args.batch_size, shuffle=False,
        num_workers=args.workers, pin_memory=True
    )
    elif args.dataset == 'ImageNet':
        val_loader = torch.utils.data.DataLoader(
            datasets.ImageFolder(args.data_dir, transforms.Compose([
                transforms.Resize(256),
                transforms.CenterCrop(224),
                transforms.ToTensor(),
                transforms.Normalize(mean=[0.485, 0.456, 0.406],
                                         std=[0.229, 0.224, 0.225])
            ])),
            batch_size=args.batch_size, shuffle=False,
            num_workers=args.workers, pin_memory=True)

    acc1 = validate(val_loader, model)


def validate(val_loader, model):
    top1 = AverageMeter()
    top5 = AverageMeter()

    model.eval()

    with torch.no_grad():
        for i, (input, target) in enumerate(val_loader):
            input = input.cuda(non_blocking=True)
            target = target.cuda(non_blocking=True)

            # compute output
            output = model(input)

            # measure accuracy and record loss
            acc1, acc5 = accuracy(output, target, topk=(1, 5))
            top1.update(acc1[0], input.size(0))
            top5.update(acc5[0], input.size(0))

            print(' * Acc@1 {top1.avg:.3f} Acc@5 {top5.avg:.3f}'
                  .format(top1=top1, top5=top5))

    return top1.avg


class AverageMeter(object):
    """Computes and stores the average and current value"""
    def __init__(self):
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



def accuracy(output, target, topk=(1,)):
    """Computes the accuracy over the k top predictions for the specified values of k"""
    with torch.no_grad():
        maxk = max(topk)
        batch_size = target.size(0)

        _, pred = output.topk(maxk, 1, True, True)
        pred = pred.t()
        correct = pred.eq(target.view(1, -1).expand_as(pred))

        res = []
        for k in topk:
            correct_k = correct[:k].reshape(-1).float().sum(0, keepdim=True)
            res.append(correct_k.mul_(100.0 / batch_size))
        return res


if __name__ == '__main__':
    main()
