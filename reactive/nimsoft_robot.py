#
# Copyright 2020 Canonical Ltd
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#  http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import os
from subprocess import check_call

from charms.reactive import when, when_not, set_flag
from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import resource_get
from charmhelpers.core.hookenv import config, unit_private_ip, charm_dir
from charmhelpers.core.host import file_hash, service
from charmhelpers.core.templating import render
from charmhelpers.core.host import rsync
from charmhelpers.contrib.openstack import context

ROBOT_CONFIG = 'robot.cfg'
ROBOT_CONFIG_PATH = ('/opt/nimsoft/robot/{}'.format(ROBOT_CONFIG))
NIMBUS_AA_PROFILE = 'opt.nimsoft.bin.nimbus'
NIMBUS_AA_PROFILE_PATH = ('/etc/apparmor.d/{}'.format(NIMBUS_AA_PROFILE))


class NimbusAppArmorContext(context.AppArmorContext):
    """"Apparmor context for nimbus binary"""
    def __init__(self):
        super(NimbusAppArmorContext, self).__init__()
        self.aa_profile = NIMBUS_AA_PROFILE

    def __call__(self):
        super(NimbusAppArmorContext, self).__call__()
        if not self.ctxt:
            return self.ctxt
        self._ctxt.update({'aa_profile': self.aa_profile})
        return self.ctxt


@when_not('nimsoft-robot.installed')
def install_nimsoft_robot():
    '''Install the nimsoft robot software that is used for LMA.'''
    nimsoft_robot_resource = None
    try:
        # Try to get the resource from Juju.
        nimsoft_robot_resource = resource_get('nimsoft-robot-package')
    except Exception as e:
        message = \
            'An error occurred fetching the nimsoft-robot-package resource.'
        hookenv.log(message)
        hookenv.log(e)
        hookenv.status_set('blocked', message)
        return

    if not nimsoft_robot_resource:
        hookenv.status_set('blocked',
                           'The nimsoft-robot-package resource is missing.')
        return

    # Handle null resource publication, we check if filesize < 1mb
    filesize = os.stat(nimsoft_robot_resource).st_size
    if filesize < 1000000:
        hookenv.status_set('blocked',
                           'Incomplete nimsoft-robot-package resource.')
        return

    hookenv.status_set('maintenance',
                       'Installing nimsoft-robot-package resource.')

    cmd = ['dpkg', '-i', nimsoft_robot_resource]
    hookenv.log(cmd)
    check_call(cmd)

    set_flag('nimsoft-robot.installed')


@when('config.changed')
@when('nimsoft-robot.installed')
def render_nimsoft_robot_config():
    """Create the robot.conf config file.

    Renders the appropriate template for the Nimbus Robot
    """
    # The v5 template is compatible with all versions < 6
    cfg_original_hash = file_hash(ROBOT_CONFIG)
    context = {
        'hub': config("hub"),
        'domain': config("domain"),
        'hubip': config("hubip"),
        'hub_robot_name': config("hub-robot-name"),
        'secondary_domain': config("secondary-domain"),
        'secondary_hubip': config("secondary-hubip"),
        'secondary_hub': config("secondary-hub"),
        'secondary_hub_robot_name': config("secondary-hub-robot-name"),
        'private_address': unit_private_ip(),
        'hostname': os.uname()[1],
        'aa_profile_mode': config("aa-profile-mode")
    }

    render('robot.cfg', ROBOT_CONFIG_PATH, context=context)
    cfg_new_hash = file_hash(ROBOT_CONFIG)

    rsync(charm_dir() + '/files/request_linux_prod.cfg',
          '/opt/nimsoft/request.cfg')

    # Install the nimbus service
    rsync(charm_dir() + '/files/nimbus.service',
          '/lib/systemd/system/nimbus.service')

    render(NIMBUS_AA_PROFILE, NIMBUS_AA_PROFILE_PATH, context=context)

    NimbusAppArmorContext().setup_aa_profile()

    if cfg_original_hash != cfg_new_hash:
        service('restart', 'nimbus')

    hookenv.status_set('active', 'ready')
