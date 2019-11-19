import os
import shutil

from shlex import split
from subprocess import check_call
from subprocess import check_output
from charms.apt import get_package_version

from charms import apt
from charms.reactive import when, when_not, set_flag
from charms.reactive import hook
from charms.reactive.helpers import data_changed
from charms.reactive.relations import endpoint_from_flag
from charms.reactive.flags import is_flag_set
from charms.reactive.flags import clear_flag
from charms.reactive.flags import set_flag

from charmhelpers.core import hookenv
from charmhelpers.core import unitdata
from charmhelpers.core.host import chdir
from charmhelpers.core.hookenv import resource_get
from charmhelpers.core.hookenv import status_set

NIMBUS_ROBOT_CONFIG = '/etc/nimbus.conf'


@when_not('nimsoft-robot.installed')
def install_nimsoft_robot():
    '''Install the nimsoft robot software that is used for LMA.'''
    nimsoft_robot_resource = None
    try:
        # Try to get the resource from Juju.
        nimsoft_robot_resource = resource_get('nimsoft-robot-package')
    except Exception as e:
        message = 'An error occurred fetching the nimsoft-robot-package resource.'
        hookenv.log(message)
        hookenv.log(e)
        hookenv.status_set('blocked', message)
        return

    if not nimsoft_robot_resource:
        hookenv.status_set('blocked', 'The nimsoft_robot_resource resource is missing.')
        return

    # Handle null resource publication, we check if filesize < 1mb
    filesize = os.stat(nimsoft_robot_resource).st_size
    if filesize < 1000000:
        hookenv.status_set('blocked', 'Incomplete nimsoft_robot_resource resource.')
        return

    hookenv.status_set('maintenance', 'Installing nimsoft_robot resource.')

    cmd = ['dpkg', '-i', nimsoft_robot_resource]
    hookenv.log(cmd)
    check_call(cmd)

    set_state('nimsoft-robot.installed')
    cur_ver = get_package_version(nimsoft_robot, full_version=True)
    # Do your setup here.
    #
    # If your charm has other dependencies before it can install,
    # add those as @when() clauses above., or as additional @when()
    # decorated handlers below
    #
    # See the following for information about reactive charms:
    #
    #  * https://jujucharms.com/docs/devel/developer-getting-started
    #  * https://github.com/juju-solutions/layer-basic#overview
    #
    set_flag('nimsoft-robot.installed')


@when('nimsoft-robot.render')
@when('nimsoft-robot.installed')
def render_nimsoft_robot_config():
    """Create the nimbus.conf config file.

    Renders the appropriate template for the Nimbus Robot 
    """
    # The v5 template is compatible with all versions < 6
    cfg_original_hash = file_hash(NIMBUS_ROBOT_CONFIG)
    connections = render_without_context(
        'nuimbus.conf',
        NIMBUS_ROBOT_CONFIG
        )
    cfg_new_hash = file_hash(NIMBUS_ROBOT_CONFIG)

    if connections:
        if cfg_original_hash != cfg_new_hash:
            service('restart', 'nimbus')
        status.active('nimbus ready.')
    else:
        # Stop the service when not connected to any log handlers.
        # NB: beat base layer will handle setting a waiting status
        service('stop', 'nimbus')
