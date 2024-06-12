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
import re
import shutil
import sys

#
# Provide a set of builds with special settings
#
import pkg

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
    ext_out = ['tarfile']


class set_builder_task_dry_run(set_builder_task):
    '''build is a dry run'''
    ext_out = ['dry-run']


@TaskGen.taskgen_method
@TaskGen.feature('setbuilder')
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


@TaskGen.feature('setbuilder')
class shower(Build.BuildContext):
    '''show the builds for a version of RTEMS'''
    cmd = 'show'
    fun = 'show'


@TaskGen.feature('setbuilder')
class dry_runner(Build.BuildContext):
    '''runs the build sets with --dry-run'''
    cmd = 'dry-run'
    fun = 'dry_run'


@TaskGen.feature('html')
class docs_builder(Build.BuildContext):
    '''build the documentation as html'''
    cmd = 'docs'
    fun = 'docs'


def set_builder_build(bld, build, dry_run=False, show=False):
    bset = pkg.configs.buildset(bld, build, dry_run)
    run_cmd = [bset['cmd']] + bset['run-opts']
    if show:
        print(build['buildset'] + ':', ' '.join(run_cmd))
    else:
        bld(name=build['buildset'],
            description='Build tar file',
            features='setbuilder',
            target=bset['tar'],
            base=bld.path,
            good=build['good'],
            dry_run=bset['dry-run'],
            rsb_cmd=' '.join(run_cmd),
            always=True)


def init(ctx):
    pkg.init(ctx)


def options(opt):
    opt.add_option('--rsb',
                   default=None,
                   dest='rsb_path',
                   help='Path to the RTEMS Source Builder (RSB)')
    opt.add_option('--rsb-options',
                   default=None,
                   dest='rsb_options',
                   help='Options to pass directly to the RTEMS Source Builder (RSB)')
    opt.add_option('--prefix',
                   default='/opt/rtems/deploy',
                   dest='prefix',
                   help='RSB prefix path to install the packages too (default: %default)')
    opt.add_option('--install',
                   action='store_true',
                   default=False,
                   dest='install',
                   help='RSB Install mode')
    pkg.options(opt)
    pkg.configs.options(opt)


def configure(conf):
    if conf.options.rsb_path is None:
        conf.fatal('RSB path not provided as configure option')
    if not os.path.exists(conf.options.rsb_path):
        conf.fatal('RSB path not found: ' + conf.options.rsb_path)
    rsb_path = os.path.abspath(conf.options.rsb_path)
    rsb_set_builder = os.path.join(rsb_path, 'source-builder',
                                   'sb-set-builder')
    if not os.path.exists(rsb_set_builder):
        conf.fatal('RSB path not the valid: ' + rsb_path)
    conf.msg('RSB', rsb_path, color='GREEN')
    # Get the version details from the RSB
    sys_path = sys.path
    try:
        rsb = None
        try:
            sys.path = [os.path.join(rsb_path, 'source-builder')] + sys.path
            import sb.version as rsb
        except:
            sys.path = [os.path.join(rsb_path, 'source-builder', 'sb')] + sys.path
            import version as rsb
        if rsb is None:
            conf.fatal('cannot import RSB version')
        rsb.set_top(rsb_path)
        rsb_version = rsb.version()
        rsb_revision = rsb.revision()
        rsb_released = rsb.released()
    except:
        raise
        conf.fatal('cannot get the RSB version information')
    finally:
        sys.path = sys_path
    conf.msg('RSB Version', rsb_version, color='GREEN')
    if 'modified' in rsb_revision:
        col = 'YELLOW'
    else:
        col = 'GREEN'
    conf.msg('RSB Revision', rsb_revision, color=col)
    if rsb_released:
        conf.msg('RSB Released', 'yes', color='GREEN')
    else:
        conf.msg('RSB Released', 'no', color='YELLOW')
    conf.msg('RSB Prefix', conf.options.prefix, color='GREEN')
    if conf.options.install:
        install = 'install'
    else:
        install = 'no-install'
    conf.msg('RSB Install mode', install, color='GREEN')
    if conf.options.rsb_options is not None:
        conf.msg('RSB Options', conf.options.rsb_options, color='GREEN')
        rsb_options = conf.options.rsb_options.split()
    else:
        rsb_options = []
    conf.find_program('pandoc', var='PANDOC', manditory=False)
    conf.env.RSB_PATH = rsb_path
    conf.env.RSB_OPTIONS = rsb_options
    conf.env.RSB_SET_BUILDER = rsb_set_builder
    conf.env.RSB_VERSION = rsb_version
    conf.env.RSB_REVISION = rsb_revision
    conf.env.RSB_RELEASED = rsb_released
    conf.env.PREFIX = conf.options.prefix
    conf.env.NO_INSTALL = not conf.options.install
    pkg.configure(conf)


def build(bld):
    if bld.cmd == 'install':
        print('Nothing to install')
        return
    builds = pkg.configs.find_buildsets(bld)
    dry_runs = [build for build in builds if build['dry-run']]
    tars = [build for build in builds if not build['dry-run']]
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
    for build in pkg.configs.find_buildsets(bld):
        set_builder_build(bld, build, show=True)


def dry_run(bld):
    for build in pkg.configs.find_buildsets(bld):
        set_builder_build(bld, build, dry_run=True)


def docs(bld):
    if not bld.env.PANDOC:
        bld.fatal('no pandoc found during configure')
    bld(name='css',
        features='subst',
        source='doc/rtems.css',
        target='rtems.css',
        is_copy=True)
    title = 'RTEMS Deployment'
    pandoc_std_opts = [
        '-f markdown_phpextra+grid_tables+multiline_tables+simple_tables+auto_identifiers',
        '--section-divs', '--toc',
        '-M title="%s"' % (title), '-t html', '--include-in-header=rtems.css'
    ]
    bld(name='html',
        source='README.md',
        target='README.html',
        rule=bld.env.PANDOC[0] + ' ${SRC} ' + ' '.join(pandoc_std_opts) +
        ' > ${TGT}',
        use='css')
