import sys


# charms.layer.status only exists in the built charm; mock it out before
# the beats_base imports since those depend on c.l.s.*.
from unittest.mock import Mock

layer_mock = Mock()
sys.modules['charms.layer'] = layer_mock
sys.modules['charms.layer.status'] = layer_mock

import reactive.nimsoft_robot as handlers
import charms_openstack.test_utils as test_utils


class TestRegisteredHooks(test_utils.TestRegisteredHooks):

    def test_hooks(self):
        # test that the hooks actually registered the relation expressions that
        # are meaningful for this interface: this is to handle regressions.
        # The keys are the function names that the hook attaches to.
        hook_set = {
            'when': {
                'render_nimsoft_robot_config': (
                    'nimsoft-robot.installed', 'config.changed')
            },
            'when_not': {
                'install_nimsoft_robot': (
                    'nimsoft-robot.installed', ),
            }
        }
        # test that the hooks were registered via the
        # reactive.barbican_handlers
        self.registered_hooks_test_helper(handlers, hook_set, [])
