# SPDX-License-Identifier: BSD-2-Clause
"""
Deployment regression tests

This can be a template for using waf to run the RSB.
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

from __future__ import print_function

import errno
import itertools
import os
import os.path
import shutil

#
# Provide a set of builds and the RTEMS version
#
import builds

from waflib import Context, Build, Errors, Logs, Scripting, Task, TaskGen, Utils

out = 'out'


class set_builder_task(Task.Task):
    always_run = True
    semaphore = Task.TaskSemaphore(1)

    def __str__(self):
        return self.name

    def uid(self):
        return Utils.h_list(self.name)

    def run(self):
        r = 0
        out = None
        err = None
        try:
            self.generator.bld.cmd_and_log(self.rsb_cmd,
                                           cwd=self.base,
                                           quiet=Context.BOTH)
        except Errors.WafError as e:
            out = e.stdout
            err = e.stderr
            r = 1
        if not self.good:
            if r == 0:
                r = 1
            else:
                r = 0
        if r != 0:
            self.generator.bld.to_log(err)
            self.generator.bld.to_log('rsb cmd: ' + self.rsb_cmd + os.linesep)
        return r


class set_builder_task_run(set_builder_task):
    '''run the build, run after dry-run tasks so they checked first'''
    ext_in = ['dry-run']


class set_builder_task_dry_run(set_builder_task):
    '''build is a dry run'''
    ext_out = ['dry-run']


@TaskGen.taskgen_method
@TaskGen.feature('*')
def set_builder_generator(self):
    if getattr(self, 'dry_run', None):
        task_type = 'set_builder_task_dry_run'
    else:
        task_type = 'set_builder_task_run'
    tsk = self.create_task(task_type)
    tsk.name = getattr(self, 'name', None)
    tsk.base = getattr(self, 'base', None)
    tsk.config = getattr(self, 'config', None)
    tsk.good = getattr(self, 'good', None)
    tsk.rsb_cmd = getattr(self, 'rsb_cmd', None)


class shower(Build.BuildContext):
    '''show the builds for a version of RTEMS'''
    cmd = 'show'
    fun = 'show'


class dry_runner(Build.BuildContext):
    '''runs the build sets with --dry-run'''
    cmd = 'dry-run'
    fun = 'dry_run'


def set_builder_build(bld, build, dry_run=False, show=False):
    name = os.path.basename(build['buildset'])
    logs = bld.path.get_bld()
    log = logs.make_node(name)
    cmd = [bld.env.RSB_SET_BUILDER, '--prefix=' + bld.env.PREFIX]
    if bld.env.NO_INSTALL:
        cmd += ['--no-install']
    cmd += ['--bset-tar-file']
    if build['dry-run'] or dry_run:
        cmd += ['--dry-run']
    cmd += [
        '--trace', '--log=' + str(log.path_from(bld.path)) + '.txt',
        build['buildset']
    ]
    if show:
        print(build['buildset'] + ':', ' '.join(cmd))
    else:
        config = 'config/' + build['buildset'] + '.bset'
        buildset = bld.path.find_resource(config)
        if buildset is None:
            bld.fatal('buildset not found: ' + build['buildset'])
        bld(name=build['buildset'],
            base=bld.path,
            good=build['good'],
            dry_run=build['dry-run'] or dry_run,
            rsb_cmd=' '.join(cmd),
            always=True)


def find_buildsets(version):
    path = os.path.join('config', str(version))
    discovered = []
    for root, dirs, files in os.walk(path):
        base = root[len('config') + 1:]
        for f in files:
            r, e = os.path.splitext(f)
            if e == '.bset':
                discovered += [os.path.join(base, r)]
    bs_default = [bs['buildset'] for bs in builds.configs[version]]
    bs = builds.configs[version] + [{
        'buildset': b,
        'good': True,
        'dry-run': False
    } for b in discovered if b not in bs_default]
    return sorted(bs, key=lambda bs: bs['buildset'])


def options(opt):
    opt.add_option('--rsb',
                   default=None,
                   dest='rsb_path',
                   help='Path to the RTEMS Source Builder (RSB)')
    opt.add_option('--rtems-version',
                   default=builds.rtems_version_default,
                   dest='rtems_version',
                   help='Version of RTEMS')
    opt.add_option('--prefix',
                   default='/opt/rtems/deploy',
                   dest='prefix',
                   help='RSB prefix path to install the packages too')
    opt.add_option('--install',
                   action='store_true',
                   default=False,
                   dest='install',
                   help='RSB Install mode')


def configure(conf):
    if conf.options.rsb_path is None:
        conf.fatal('RSB path not provided as configure option')
    if not os.path.exists(conf.options.rsb_path):
        conf.fatal('RSB path not found: ' + conf.options.rsb_path)
    try:
        rtems_version = int(conf.options.rtems_version)
    except:
        conf.fatal('invalid RTEMS version: ' + conf.options.rtems_version)
    if rtems_version not in builds.configs:
        conf.fatal('unsupported RTEMS version: ' + conf.options.rtems_version)
    conf.msg('RTEMS Version', rtems_version, 'GREEN')
    rsb_path = os.path.abspath(conf.options.rsb_path)
    rsb_set_builder = os.path.join(rsb_path, 'source-builder',
                                   'sb-set-builder')
    if not os.path.exists(rsb_set_builder):
        conf.fatal('RSB path not the valid: ' + rsb_path)
    conf.msg('RSB', rsb_path, 'GREEN')
    conf.msg('RSB Prefix', conf.options.prefix, 'GREEN')
    if conf.options.install:
        install = 'install'
    else:
        install = 'no-install'
    conf.msg('RSB Install mode', install, 'GREEN')
    conf.env.RSB_PATH = rsb_path
    conf.env.RSB_SET_BUILDER = rsb_set_builder
    conf.env.RTEMS_VERSION = rtems_version
    conf.env.PREFIX = conf.options.prefix
    conf.env.NO_INSTALL = not conf.options.install


def build(bld):
    dry_runs = [
        build for build in find_buildsets(bld.env.RTEMS_VERSION)
        if build['dry-run']
    ]
    tars = [
        build for build in find_buildsets(bld.env.RTEMS_VERSION)
        if not build['dry-run']
    ]
    for build in dry_runs:
        set_builder_build(bld, build)
    for build in tars:
        set_builder_build(bld, build)
    bld.clean_files = \
        itertools.chain(bld.bldnode.ant_glob('**',
          excl='.lock* config.log c4che/* config.h',
          quiet=True, generator=True),
                        bld.path.ant_glob('tar/**', quiet=True, generator=True))


def distclean(ctx):
    '''removes build folders and data'''

    def remove_and_log(k, fun):
        try:
            fun(k)
        except EnvironmentError as e:
            if e.errno != errno.ENOENT:
                Logs.warn('Could not remove %r', k)

    Scripting.distclean(ctx)
    for d in ['build', 'tar']:
        remove_and_log(d, shutil.rmtree)
    for f in os.listdir('.'):
        r, e = os.path.splitext(f)
        if e == '.txt':
            remove_and_log(f, os.remove)


def show(bld):
    for build in find_buildsets(bld.env.RTEMS_VERSION):
        set_builder_build(bld, build, show=True)


def dry_run(bld):
    for build in find_buildsets(bld.env.RTEMS_VERSION):
        set_builder_build(bld, build, dry_run=True)
