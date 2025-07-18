# SPDX-License-Identifier: BSD-2-Clause
'''
 Packaging Support
'''

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

import os

import pkg.configs

packager = None
if os.name == 'posix':
    system = os.uname()[0]
    if system == 'FreeBSD':
        import pkg.freebsd as packager
    elif system == 'Linux':
        import pkg.linux as packager


def init(ctx):
    pkg.configs.init(ctx)
    if packager is not None:
        packager.init(ctx)


def options(opt):
    if packager is not None:
        pkg.configs.options(opt)
        packager.options(opt)


def configure(conf):
    pkg.configs.configure(conf)
    conf.env.PACKAGER = False
    if packager is not None:
        packager.configure(conf)
    if conf.env.PACKAGER:
        p = 'yes'
    else:
        p = 'no'
    conf.msg('Packaging', p)


def build(bld, build, bset, dry_run):
    if packager is not None:
        packager.build(bld, build, bset, dry_run)
