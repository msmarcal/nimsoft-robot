import os

from subprocess import check_call

from charms.layer import status
from charms.reactive import when, when_not, set_flag

from charmhelpers.core import hookenv
from charmhelpers.core.hookenv import resource_get
from charmhelpers.core.hookenv import config, unit_private_ip, charm_dir
from charmhelpers.core.host import file_hash, service
from charmhelpers.core.templating import render
from charmhelpers.core.host import rsync

NIMBUS_ROBOT_CONFIG = '/opt/nms-robot-vars.cfg'


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
                           'The nimsoft_robot_resource resource is missing.')
        return

    # Handle null resource publication, we check if filesize < 1mb
    filesize = os.stat(nimsoft_robot_resource).st_size
    if filesize < 1000000:
        hookenv.status_set('blocked',
                           'Incomplete nimsoft_robot_resource resource.')
        return

    hookenv.status_set('maintenance', 'Installing nimsoft_robot resource.')

    cmd = ['dpkg', '-i', nimsoft_robot_resource]
    hookenv.log(cmd)
    check_call(cmd)

    set_flag('nimsoft-robot.installed')


@when('config.changed')
@when('nimsoft-robot.installed')
def render_nimsoft_robot_config():
    """Create the nimbus.conf config file.

    Renders the appropriate template for the Nimbus Robot
    """
    # The v5 template is compatible with all versions < 6
    cfg_original_hash = file_hash(NIMBUS_ROBOT_CONFIG)
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
        'hostname': os.uname()[1]
    }
    render('nms-robot-vars.cfg', NIMBUS_ROBOT_CONFIG, context=context)
    cfg_new_hash = file_hash(NIMBUS_ROBOT_CONFIG)

    rsync(charm_dir() + '/files/request_linux_prod.cfg',
          '/opt/nimsoft/request.cfg')

    if cfg_original_hash != cfg_new_hash:
        # run RobotConfigurer.sh script
        cmd = ['/opt/nimsoft/install/RobotConfigurer.sh']
        hookenv.log(cmd)
        check_call(cmd)
        service('restart', 'nimbus')
        status.active('nimbus ready.')
