# SPDX-License-Identifier: BSD-2-Clause
"""
Linux Packaging Support

Currently only RPM is supported. Happy to have more added
"""

#
# Copyright 2022 Chris Johns (chris@contemporary.software)
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
# 1. Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
#

from email.utils import format_datetime
import datetime
import os.path
import os
import platform

import pkg.configs

from waflib import Build, TaskGen


@TaskGen.feature('rpmspec')
class rpmspecer(Build.BuildContext):
    '''generate RPM spec files'''
    cmd = 'rpmspec'
    fun = 'rpmspec'


@TaskGen.feature('deb')
class deber(Build.BuildContext):
    '''generate Debian control files'''
    cmd = 'deb'
    fun = 'deb'


def _esc_name(s):
    return s.replace('_', '-')


def _esc_label(s):
    return s.replace('-', '_')


arch_map = {
    'rpmspec': {
        'x86_64': 'x86_64',
        'aarch64': 'aarch64',
    },
    'deb': {
        'x86_64': 'amd64',
        'aarch64': 'arm64',
    }
}


def rpm_get_config(ctx):
    if ctx.env.RPM_CONFIG:
        config = pkg.configs.get_config_parser()
        try:
            config.read(ctx.env.RPM_CONFIG)
        except pkg.configs.get_config_error() as ce:
            ctx.fatal('rpm config parse error: ' + str(ce))
    else:
        config = None
    return config


def rpm_config_parser(bld, build):
    config = rpm_get_config(bld)
    no_config = '#  No user configuration, see ./waf --help and --rpm-config'
    if config is None:
        return no_config
    if not config.has_section(build['buildset']):
        return no_config
    try:
        items = config.items(build['buildset'])
    except pkg.configs.get_config_error() as ce:
        bld.fatal('rpm config parse error: ' + str(ce))
    user_config = []
    if bld.env.RPM_CONFIG_VALUES:
        for cv in bld.env.RPM_CONFIG_VALUES:
            ci = cv.split('=', 1)
            if len(ci) != 2:
                bld.fatal('invalid RPM config value: ' + cv)
            user_config += ['%%define %s %s' % (ci[0], ci[1])]
    for ci in items:
        user_config += ['%%define %s %s' % (ci[0], ci[1])]
    return os.linesep.join(user_config)


def rpm_configure(conf):
    try:
        conf.find_program('rpmbuild', var='RPMBUILD', mandatory=False)
        conf.env.PACKAGER = True
    except:
        pass
    if conf.options.rpm_config is not None:
        if not conf.env.PACKAGER:
            conf.fatal('RPM config option is invalid without rpmbuild')
        if not os.path.isfile(conf.options.rpm_config):
            conf.fatal('RPM config does not exist or not a file: ' +
                       conf.options.rpm_config)
        conf.msg('RPM config', conf.options.rpm_config)
        conf.env.RPM_CONFIG = conf.options.rpm_config
        rpm_get_config(conf)
        if conf.options.rpm_config_value:
            conf.env.RPM_CONFIG_VALUES = conf.options.rpm_config_value
            conf.msg('RPM config values', len(conf.options.rpm_config_value))
    else:
        if conf.options.rpm_config_value:
            conf.fatal('RPM configuration value and no INI file')


def deb_get_config(ctx):
    if ctx.env.DEB_CONFIG:
        config = pkg.configs.get_config_parser()
        try:
            config.read(ctx.env.DEB_CONFIG)
        except pkg.configs.get_config_error() as ce:
            ctx.fatal('deb config parse error: ' + str(ce))
    else:
        config = None
    return config


def deb_config_parser(bld, build):
    config = deb_get_config(bld)
    no_config = ''
    if config is None:
        return no_config
    if not config.has_section(build['buildset']):
        return no_config
    try:
        items = config.items(build['buildset'])
    except pkg.configs.get_config_error() as ce:
        bld.fatal('deb config parse error: ' + str(ce))
    user_config = []
    if bld.env.DEB_CONFIG_VALUES:
        for cv in bld.env.DEB_CONFIG_VALUES:
            ci = cv.split('=', 1)
            if len(ci) != 2:
                bld.fatal('invalid DEB config value: ' + cv)
            user_config += ['%define %s %s' % (ci[0], ci[1])]
    for ci in items:
        user_config += ['%define %s %s' % (ci[0], ci[1])]
    return os.linesep.join(user_config)


def deb_configure(conf):
    try:
        conf.find_program('dpkg-deb', var='DPKG_DEB', mandatory=False)
        # fakeroot is commonly used for local package building
        conf.find_program('fakeroot', var='FAKEROOT', mandatory=False)
        conf.find_program('dh', var='DEBHELPER', mandatory=False)
        conf.env.PACKAGER = True
    except:
        pass
    if conf.options.deb_config is not None:
        if not conf.env.PACKAGER:
            conf.fatal('DEB config option is invalid without dpkg-deb')
        if not os.path.isfile(conf.options.deb_config):
            conf.fatal('DEB config does not exist or not a file: ' +
                       conf.options.deb_config)
        conf.msg('DEB config', conf.options.deb_config)
        conf.env.DEB_CONFIG = conf.options.deb_config
        deb_get_config(conf)
        if conf.options.deb_config_value:
            conf.env.DEB_CONFIG_VALUES = conf.options.deb_config_value
            conf.msg('DEB config values', len(conf.options.deb_config_value))
    else:
        if conf.options.deb_config_value:
            conf.fatal('DEB configuration value and no INI file')

    if 'SOURCE_DATE_EPOCH' in os.environ:
        now = datetime.datetime.fromtimestamp(
            int(os.environ['SOURCE_DATE_EPOCH']), datetime.timezone.utc)
    else:
        now = datetime.datetime.now(datetime.timezone.utc)
    conf.env.DEB_DATE = format_datetime(now)


def rpm_build(bld, build):
    user_rpm_config = rpm_config_parser(bld, build)
    bset = pkg.configs.buildset(bld, build, dry_run=False)
    rpm_name = 'rpmspec/' + bset['name']
    spec_file = _esc_name(build['buildset'])
    spec = bld.path.get_bld().find_or_declare(spec_file + '.spec')
    buildroot = bld.path.get_bld().find_or_declare('buildroot')
    buildroot_BUILD = buildroot.find_or_declare('BUILD')
    buildroot_BUILDROOT = buildroot.find_or_declare('BUILDROOT')
    buildroot_RPMS = buildroot.find_or_declare('RPMS')
    buildroot_SRPMS = buildroot.find_or_declare('SRPMS')
    buildroot.mkdir()
    buildroot_BUILD.mkdir()
    buildroot_BUILDROOT.mkdir()
    buildroot_RPMS.mkdir()
    buildroot_SRPMS.mkdir()
    if bld.env.RSB_RELEASED:
        rel = 'released'
    else:
        rel = 'not-released'
    bld(name=rpm_name,
        features='subst',
        description='Generate RPM spec file',
        target=spec,
        source='pkg/rpm.spec.in',
        RSB_BUILDROOT=buildroot,
        RSB_PKG_NAME=bset['name'],
        RSB_HOST_ARCH=arch_map["rpmspec"][platform.machine()],
        PREFIX=bld.env.PREFIX,
        RSB_VERSION=bld.env.RSB_VERSION,
        RSB_REVISION=_esc_label(bld.env.RSB_REVISION),
        RSB_RELEASED=rel,
        TARFILE=bset['tar'],
        RSB_SET_BUILDER=bset['cmd'],
        RSB_SET_BUILDER_ARGS=' '.join(bset['pkg-opts']),
        RSB_WORK_PATH=bld.path,
        USER_RPM_CONFIG=user_rpm_config)


def deb_build(bld, build):
    user_deb_config = deb_config_parser(bld, build)
    bset = pkg.configs.buildset(bld, build, dry_run=False)

    board_path = _esc_name(build['buildset'])
    deb_dir = board_path + '.debian/debian'

    buildroot = bld.path.get_bld().find_or_declare('deb_buildroot')
    buildroot.mkdir()

    if bld.env.RSB_RELEASED:
        rel = 'released'
    else:
        rel = 'not-released'

    # Consolidate all common substitution variables
    subst_vars = {
        'RSB_BUILDROOT': buildroot.abspath(),
        'RSB_PKG_NAME': bset['name'],
        'RSB_HOST_ARCH': arch_map["deb"][platform.machine()],
        'PREFIX': bld.env.PREFIX,
        'RSB_VERSION': bld.env.RSB_VERSION,
        'RSB_REVISION': _esc_label(bld.env.RSB_REVISION),
        'RSB_RELEASED': rel,
        'TARFILE': bset['tar'],
        'RSB_SET_BUILDER': bset['cmd'],
        'RSB_SET_BUILDER_ARGS': ' '.join(bset['pkg-opts']),
        'RSB_WORK_PATH': bld.path.abspath(),
        'USER_DEB_CONFIG': user_deb_config,
        'DEB_DATE': bld.env.DEB_DATE
    }

    bld(name='deb_control_' + bset['name'],
        features='subst',
        description='Generate Debian control file',
        target=bld.path.get_bld().find_or_declare(deb_dir + '/control'),
        source='pkg/debian.control.in',
        **subst_vars)

    bld(name='deb_rules_' + bset['name'],
        features='subst',
        description='Generate Debian rules file',
        target=bld.path.get_bld().find_or_declare(deb_dir + '/rules'),
        source='pkg/debian.rules.in',
        chmod=0o755,
        **subst_vars)

    bld(name='deb_changelog_' + bset['name'],
        features='subst',
        description='Generate Debian changelog file',
        target=bld.path.get_bld().find_or_declare(deb_dir + '/changelog'),
        source='pkg/debian.changelog.in',
        **subst_vars)

    bld(name='deb_compat_' + bset['name'],
        features='subst',
        description='Generate Debian compat file',
        target=bld.path.get_bld().find_or_declare(deb_dir + '/compat'),
        source='pkg/debian.compat.in',
        **subst_vars)


def deb(bld):
    for build in pkg.configs.find_buildsets(bld):
        deb_build(bld, build)


def rpmspec(bld):
    for build in pkg.configs.find_buildsets(bld):
        rpm_build(bld, build)


def init(ctx):
    pkg.configs.add_wscript_fun(ctx, 'rpmspec', rpmspec)
    pkg.configs.add_wscript_fun(ctx, 'deb', deb)


def options(opt):
    opt.add_option('--rpm-config',
                   default=None,
                   dest='rpm_config',
                   help='RPM configuration INI file')
    opt.add_option('--rpm-config-value',
                   action='append',
                   type=str,
                   default=None,
                   dest='rpm_config_value',
                   help='Set RPM configuration value (key=value)')
    opt.add_option('--deb-config',
                   default=None,
                   dest='deb_config',
                   help='DEB configuration INI file')
    opt.add_option('--deb-config-value',
                   action='append',
                   type=str,
                   default=None,
                   dest='deb_config_value',
                   help='Set DEB configuration value (key=value)')


def configure(conf):
    rpm_configure(conf)
    deb_configure(conf)


def build(bld, build, bset, dry_run):
    pass
