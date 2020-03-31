# Overview

This charm provides the nimsoft-robot agent for collecting information for CA
UIM (Unified Infrastructure Managment). The charm was based on nimsoft-robot
version 7.96 but should work with any version. (Unverified.)

# Usage

    juju deploy cs:~vhart/nimsoft-robot --resource \
      nimsoft-robot-package=/path/to/nimsoft-robot.deb

This charm supports juju resources to provide the deb package file.
This allows us to use `--resource` in the deploy command or use
`juju attach` to supply the required resource after deployment:

    juju attach nimsoft-robot nimsoft-robot-package=/path/to/nimsoft-robot.deb

You can also specify this in your bundle.yaml in the resources section:

    nimsoft-robot:
      charm: cs:~vhart/nimsoft-robot
      resources:
        nimsoft-robot-package: /path/to/nimsoft-robot.deb

The deb file should be obtainable from CA (Broadcom) via their CA-UIM (or DX
IM) installation package. Additionally, you may be able to find it in the
Archive section of [nimsoft-archive][Nimsoft Support].

# Configuration

The configuration options will be listed on the charm store, however If you're
making assumptions or opinionated decisions in the charm (like setting a default
administrator password), you should detail that here so the user knows how to
change it immediately, etc.

# Contact Information

Though this will be listed in the charm store itself don't assume a user will
know that, so include that information here:

<!-- ## Upstream Project Name

  - Upstream website
  - Upstream bug tracker
  - Mailing list or contact information -->


[nimsoft-archive]: http://support.nimsoft.com/Default.aspx?center=felles/archive
