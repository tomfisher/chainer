import unittest

import mock

from chainer import testing
from chainer.training import extensions
from chainer.training import util


@testing.parameterize(
    {'base_lr': 2.0, 'gamma': 0.1, 'step_value': [1, 3, 5],
     'expect': [2.0, 0.2, 0.2, 0.02, 0.02, 0.002]},
    {'base_lr': -2.0, 'gamma': 0.1, 'step_value': [1, 3, 5],
     'expect': [-2.0, -0.2, -0.2, -0.02, -0.02, -0.002]},
    {'base_lr': 2.0, 'gamma': 2, 'step_value': [1, 3, 5],
     'expect': [2.0, 4.0, 4.0, 8.0, 8.0, 16.0]},
    {'base_lr': -2.0, 'gamma': 2, 'step_value': [1, 3, 5],
     'expect': [-2.0, -4.0, -4.0, -8.0, -8.0, -16.0]},
)
class TestMutistep(unittest.TestCase):

    def setUp(self):
        self.optimizer = mock.MagicMock()
        self.extension = extensions.Multistep(
            'x', self.base_lr, self.gamma, self.step_value, self.optimizer)

        self.interval = 1
        self.expect = [e for e in self.expect for _ in range(self.interval)]
        self.trigger = util.get_trigger((self.interval, 'iteration'))

        self.trainer = testing.get_trainer_with_mock_updater(self.trigger)
        self.trainer.updater.get_optimizer.return_value = self.optimizer

    def _run_trainer(self, extension, expect, optimizer=None):
        if optimizer is None:
            optimizer = self.optimizer
        extension.initialize(self.trainer)
        actual = []
        for _ in expect:
            self.trainer.updater.update()
            actual.append(optimizer.x)
            if self.trigger(self.trainer):
                extension(self.trainer)

        self.assertEqual(actual, expect)

    def test_basic(self):
        self.optimizer.x = 0
        extension = extensions.multistep.Multistep(
            'x', self.base_lr, self.gamma, self.step_value, self.optimizer)
        self._run_trainer(extension, self.expect)

    def test_without_init(self):
        self.optimizer.x = self.base_lr
        extension = extensions.multistep.Multistep(
            'x', self.base_lr, self.gamma, self.step_value, self.optimizer)
        self._run_trainer(extension, self.expect)

    def test_with_optimizer(self):
        optimizer = mock.Mock()
        optimizer.x = 0
        extension = extensions.multistep.Multistep(
            'x', self.base_lr, self.gamma, self.step_value, optimizer)

        self._run_trainer(extension, self.expect, optimizer)


testing.run_module(__name__, __file__)