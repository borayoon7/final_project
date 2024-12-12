# -*- coding: utf-8 -*-
"""model.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1lyLVMlzBxfzALET3mki0e8d8xB6N8SPR
"""

import torch
import torch.nn as nn
import torch.nn.functional as F


class Parallel(nn.Module):
    """Convolution block with 3x3 and 5x5 dilated convolutions in parallel."""
    def __init__(self, in_channels, out_channels, dilation=2):
        super(Parallel, self).__init__()
        # 3x3 Convolutions
        self.conv3x3_1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn3x3_1 = nn.BatchNorm2d(out_channels)
        self.conv3x3_2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.bn3x3_2 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()

        # 5x5 Dilated Convolutions
        self.conv5x5_1 = nn.Conv2d(in_channels, out_channels, kernel_size=5, padding='same', dilation=dilation)
        self.bn5x5_1 = nn.BatchNorm2d(out_channels)
        self.conv5x5_2 = nn.Conv2d(out_channels, out_channels, kernel_size=5, padding='same', dilation=dilation)
        self.bn5x5_2 = nn.BatchNorm2d(out_channels)

    def forward(self, x):
        # Parallel convolutions
        conv3x3 = self.relu(self.bn3x3_1(self.conv3x3_1(x)))
        conv3x3 = self.bn3x3_2(self.conv3x3_2(conv3x3))

        conv5x5 = self.relu(self.bn5x5_1(self.conv5x5_1(x)))
        conv5x5 = self.bn5x5_2(self.conv5x5_2(conv5x5))
        # conv3x3 = self.relu(self.conv3x3_1(x))
        # conv3x3 = self.bn3x3_2(self.conv3x3_2(conv3x3))
        # # conv3x3 = self.conv3x3_2(conv3x3)

        # conv5x5 = self.relu(self.conv5x5_1(x))
        # conv5x5 = self.conv5x5_2(conv5x5)

        # Add the two outputs
        return conv3x3 + conv5x5
    

class AttentionBlock(nn.Module):
    """Attention block with global average pooling and convolution layers."""
    def __init__(self, in_channels, out_channels):
        super(AttentionBlock, self).__init__()
        self.gap = nn.AdaptiveAvgPool2d(1)  # Global Average Pooling
        self.conv1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.conv2 = nn.Conv2d(out_channels, out_channels, kernel_size=3, padding=1)
        self.relu = nn.ReLU()
        self.sigmoid = nn.Sigmoid()

    def forward(self, x, skip_connection):
        # Attention mechanism
        attention = self.gap(x)
        attention = self.relu(self.conv1(attention))
        attention = self.sigmoid(self.conv2(attention))

        # Multiply attention weights with the skip connection
        return x * attention + skip_connection


class boReEsNet(nn.Module):
    """boReEsNet model."""
    def __init__(self, input_channels, num_filters, num_classes=2):
        super(boReEsNet, self).__init__()
        # Initial convolution
        self.relu = nn.ReLU()
        self.conv0 = nn.Conv2d(input_channels, num_filters, kernel_size=3, padding=1)
        self.bn0 = nn.BatchNorm2d(num_filters) 

        # Blocks 1 to 4
        self.block1 = Parallel(num_filters, num_filters)
        self.attention1 = AttentionBlock(num_filters, num_filters)

        self.block2 = Parallel(num_filters, num_filters)
        self.attention2 = AttentionBlock(num_filters, num_filters)

        self.block3 = Parallel(num_filters, num_filters)
        self.attention3 = AttentionBlock(num_filters, num_filters)

        self.block4 = Parallel(num_filters, num_filters)
        self.attention4 = AttentionBlock(num_filters, num_filters)
        
        self.block5 = nn.Conv2d(num_filters, num_filters, kernel_size=3, padding=1)
        self.bn5 = nn.BatchNorm2d(num_filters) 

        # Final convolutions and regression
        self.conv5 = nn.ConvTranspose2d(num_filters, num_filters, kernel_size=11,stride=[3,7], padding=(4, 2))
        self.bn6 = nn.BatchNorm2d(num_filters)
        self.conv6 = nn.Conv2d(num_filters, num_classes, kernel_size=3, padding=1)

    def forward(self, x):
        # print(x.shape) # 24x2x2
        # Block 0
        # x0 = self.conv0(x)
        x0 = self.relu(self.bn0(self.conv0(x)))

        # Block 1
        x1 = self.block1(x0)
        x1 = self.attention1(x1, x0)

        # Block 2
        x2 = self.block2(x1)
        x2 = self.attention2(x2, x1)

        # Block 3
        x3 = self.block3(x2)
        x3 = self.attention3(x3, x2)

        # Block 4
        x4 = self.block4(x3)
        x4 = self.attention4(x4, x3)

        # Block 5
        x5 = self.relu(self.bn5(self.block5(x4)))
        # x5 = self.block5(x4)
        
        # transposed
        x6 = self.relu(self.bn6(self.conv5(x0 + x5)))
        # x6 = self.conv5(x0+x5)
        # print(x5.shape) # torch.Size([64, 24, 2, 2]) 72
        #   마지막 conv
        out = self.conv6(x6) #torch.Size([64, 8, 10, 10])
        return out
        

    
## ReEsBlock
class ReEsblock(nn.Module):
    def __init__(self, in_channels, out_channels):
        super(ReEsblock, self).__init__()
        self.conv3x3_1 = nn.Conv2d(in_channels, out_channels, kernel_size=3, padding=1)
        self.bn1 = nn.BatchNorm2d(out_channels)
        self.relu = nn.ReLU()
        
    def forward(self, x):
        conv3x3 = self.relu(self.bn1(self.conv3x3_1(x)))  # BN 적용
        conv3x3 = self.bn1(self.conv3x3_1(conv3x3)) 
        # conv3x3 = self.relu(self.conv3x3_1(x))
        # conv3x3 = self.conv3x3_1(conv3x3)
        return conv3x3
        
class ReEsNet(nn.Module):
    def __init__(self, input_channels, num_filters, num_classes=2):
        super(ReEsNet, self).__init__()
        self.relu = nn.ReLU()
        self.conv0 = nn.Conv2d(input_channels, num_filters, kernel_size=3, padding=1)
        self.bn0 = nn.BatchNorm2d(num_filters)
        
        # Blocks 1 to 4
        self.block1 = ReEsblock(num_filters, num_filters)
        self.block2 = ReEsblock(num_filters, num_filters)
        self.block3 = ReEsblock(num_filters, num_filters)
        self.block4 = ReEsblock(num_filters, num_filters)
        # conv
        self.block5 = nn.Conv2d(num_filters, num_filters, kernel_size=3, padding=1)
        self.bn5 = nn.BatchNorm2d(num_filters)
        # Final convolutions and regression
        self.conv5 = nn.ConvTranspose2d(num_filters, num_filters, kernel_size=11,stride=[3,7], padding=(4, 2))
        self.bn6 = nn.BatchNorm2d(num_filters) 
        self.conv6 = nn.Conv2d(num_filters, num_classes, kernel_size=3, padding=1)

    def forward(self, x):
        x0 = self.relu(self.bn0(self.conv0(x)))
        # x0 = self.conv0(x)
        # Block 1
        x1 = self.block1(x0)
        # Block 2
        x2 = self.block2(x1)
        # Block 3
        x3 = self.block3(x2)
        # Block 4
        x4 = self.block4(x3)
        
        x5 = self.relu(self.bn5(self.block5(x4)))
        x6 = self.relu(self.bn6(self.conv5(x0 + x5)))
        
        # x5 = self.block5(x4)
        # # 
        # x6 = self.conv5(x0+x5)
        # print(x5.shape) # torch.Size([64, 24, 2, 2]) 72

        # Block 6
        out = self.conv6(x6) #torch.Size([64, 8, 10, 10])
        return out