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

import os.path

import pkg.configs

from waflib import Build, TaskGen


@TaskGen.feature('rpmspec')
class rpmspecer(Build.BuildContext):
    '''generate RPM spec files'''
    cmd = 'rpmspec'
    fun = 'rpmspec'


def _esc_name(s):
    return s.replace('_', '-')


def _esc_label(s):
    return s.replace('-', '_')


def rpm_configure(conf):
    try:
        conf.find_program('rpmbuild', var='RPMBUILD', manditory=False)
        conf.env.PACKAGER = True
    except:
        pass


def rpm_build(bld, build):
    bset = pkg.configs.buildset(bld, build, dry_run=False)
    rpm_name = 'rpmspec/' + bset['name']
    spec_file = _esc_name(build['buildset'])
    spec = bld.path.get_bld().find_or_declare(spec_file + '.spec')
    buildroot = bld.path.get_bld().find_or_declare('buildroot')
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
        PREFIX=bld.env.PREFIX,
        RSB_VERSION=bld.env.RSB_VERSION,
        RSB_REVISION=_esc_label(bld.env.RSB_REVISION),
        RSB_RELEASED=rel,
        TARFILE=bset['tar'],
        RSB_SET_BUILDER=bset['cmd'],
        RSB_SET_BUILDER_ARGS=' '.join(bset['pkg-opts']),
        RSB_WORK_PATH=bld.path)


def rpmspec(bld):
    for build in pkg.configs.find_buildsets(bld):
        rpm_build(bld, build)


def init(ctx):
    pkg.configs.add_wscript_fun(ctx, 'rpmspec', rpmspec)


def options(opt):
    pass


def configure(conf):
    rpm_configure(conf)


def build(bld, build, bset, dry_run):
    pass
