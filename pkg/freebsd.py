# SPDX-License-Identifier: BSD-2-Clause
"""
FreeBSD Packaging Support

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


@TaskGen.feature('port')
class porter(Build.BuildContext):
    '''generate port files'''
    cmd = 'ports'
    fun = 'ports'


def _esc_name(s):
    return s.replace('_', '-')


def _esc_label(s):
    return s.replace('-', '_')


def ports_configure(conf):
    pass


def ports_build(bld, build):
    bset = pkg.configs.buildset(bld, build, dry_run=False)
    pkg_name = 'pkg/' + bset['name']
    pkg_file_name = _esc_name(build['buildset'])
    pkg_file = bld.path.get_bld().find_or_declare(spec_file + '.spec')
    if bld.env.RSB_RELEASED:
        rel = 'released'
    else:
        rel = 'not-released'


def ports(bld):
    for build in pkg.configs.find_buildsets(bld):
        ports_build(bld, build)


def init(ctx):
    pkg.configs.add_wscript_fun(ctx, 'ports', ports)


def options(opt):
    pass


def configure(conf):
    ports_configure(conf)


def build(bld, build, bset, dry_run):
    pass
