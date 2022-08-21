"""
from XD_XD's 5th place solution for SpaceNet-4 challenge
https://github.com/SpaceNetChallenge/SpaceNet_Off_Nadir_Solutions/blob/master/XD_XD/main.py
"""

import torch
import torch.nn as nn
from torchvision.models import vgg16


class conv_relu(nn.Module):
    def __init__(self, in_, out):
        super().__init__()
        self.conv = nn.Conv2d(in_, out, 3, padding=1)
        self.activation = nn.ReLU(inplace=True)

    def forward(self, x):
        x = self.conv(x)
        x = self.activation(x)
        return x


class decoder_block(nn.Module):
    def __init__(self, in_channels, middle_channels, out_channels):
        super(decoder_block, self).__init__()
        self.in_channels = in_channels
        self.block = nn.Sequential(
            #nn.Upsample(scale_factor=2, mode='bilinear'),
            nn.Upsample(scale_factor=2),
            conv_relu(in_channels, middle_channels),
            conv_relu(middle_channels, out_channels),
        )

    def forward(self, x):
        return self.block(x)


class unet_vgg16(nn.Module):
    def __init__(self, num_filters=32, pretrained=False):
        super().__init__()
        self.encoder = vgg16(pretrained=pretrained).features
        self.pool = nn.MaxPool2d(2, 2)

        self.relu = nn.ReLU(inplace=True)
        self.conv1 = nn.Sequential(
            self.encoder[0], self.relu, self.encoder[2], self.relu)
        self.conv2 = nn.Sequential(
            self.encoder[5], self.relu, self.encoder[7], self.relu)
        self.conv3 = nn.Sequential(
            self.encoder[10], self.relu, self.encoder[12], self.relu,
            self.encoder[14], self.relu)
        self.conv4 = nn.Sequential(
            self.encoder[17], self.relu, self.encoder[19], self.relu,
            self.encoder[21], self.relu)
        self.conv5 = nn.Sequential(
            self.encoder[24], self.relu, self.encoder[26], self.relu,
            self.encoder[28], self.relu)

        self.center = decoder_block(512, num_filters * 8 * 2, num_filters * 8)
        self.dec5 = decoder_block(
            512 + num_filters * 8, num_filters * 8 * 2, num_filters * 8)
        self.dec4 = decoder_block(
            512 + num_filters * 8, num_filters * 8 * 2, num_filters * 8)
        self.dec3 = decoder_block(
            256 + num_filters * 8, num_filters * 4 * 2, num_filters * 2)
        self.dec2 = decoder_block(
            128 + num_filters * 2, num_filters * 2 * 2, num_filters)
        self.dec1 = conv_relu(64 + num_filters, num_filters)
        self.final = nn.Conv2d(num_filters, 1, kernel_size=1)

    def forward(self, x):
        conv1 = self.conv1(x)
        conv2 = self.conv2(self.pool(conv1))
        conv3 = self.conv3(self.pool(conv2))
        conv4 = self.conv4(self.pool(conv3))
        conv5 = self.conv5(self.pool(conv4))
        center = self.center(self.pool(conv5))
        dec5 = self.dec5(torch.cat([center, conv5], 1))
        dec4 = self.dec4(torch.cat([dec5, conv4], 1))
        dec3 = self.dec3(torch.cat([dec4, conv3], 1))
        dec2 = self.dec2(torch.cat([dec3, conv2], 1))
        dec1 = self.dec1(torch.cat([dec2, conv1], 1))
        x_out = self.final(dec1)
        return x_out
