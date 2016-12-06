'''ESPCN Model'''
from __future__ import absolute_import
from __future__ import division
from __future__ import print_function
from __future__ import unicode_literals

import tensorflow as tf
import numpy as np


class SuperResolution(object):
    def __init__(self, config):
        self.variables = {}

        self.factor = config.factor
        self.height = config.height
        self.width = config.width
        self.filters = config.filters
        self.kernel_sizes = config.kernel_sizes
        self.strides = config.strides

        self._build()

    def _build(self):
        self._create_variables()
        self._create_inference()
        self._create_loss()
        self._create_train()
        self._create_metric()

    def _create_variables(self):
        with tf.variable_scope('variables'):
            self.input = tf.placeholder(
                tf.float32, [None, self.height, self.width, 3], 'input'
            )
            self.output = tf.placeholder(
                tf.float32, [None, self.height * self.factor, self.width * self.factor, 3], 'output'
            )

    def _create_inference(self):
        x0 = self.input

        for idx, (stride, filter_n, kernel) in enumerate(zip(self.strides, self.filters, self.kernel_sizes)):
            layer = tf.contrib.layers.convolution(
                x0,
                filter_n,
                kernel,
                stride=stride,
                 # not sure about padding, it seems in paper they're okay with
                 # spatial dimensions reduction
                 # XXX: consider using 'VALID' instead
                padding='SAME',
                activation_fn=tf.nn.tanh
            )
            self.variables['layer' + str(idx)] = layer
            x0 = layer

        # implementing subpixel (deconv/upsampling) layer
        # i've checked with paper formula and it seems like just reshape
        # XXX: check this again: it just can't be that simple
        subpixel = tf.reshape(x0, [
            -1,
            self.height * self.factor,
            self.height * self.factor,
            3])
        self.predicted = subpixel


    def _create_loss(self):
        self.loss = (
            tf.reduce_sum(tf.squared_difference(self.predicted, self.output)) *
            1.0 / (3 * self.width * self.height * self.factor ** 2)
        )

    def _create_train(self):
        self.train_op = tf.train.AdamOptimizer().minimize(self.loss)

    def _create_metric(self):
        maxf = 255.0
        self.psnr = 20.0 * tf.log(maxf / tf.sqrt(self.loss)) / np.log(10)