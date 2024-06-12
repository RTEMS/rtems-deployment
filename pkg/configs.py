# SPDX-License-Identifier: BSD-2-Clause
"""
RSB Deployment Configurations
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

import re
import os
import sys

from waflib import Context

path = 'config'


def init(ctx):
    pass


def options(opt):
    opt.add_option('--builds',
                   default=None,
                   dest='builds',
                   help='Regex filter of buildset to build')


def configure(conf):
    if conf.options.builds is not None:
        try:
            bf = re.compile(conf.options.builds)
            build_filter = conf.options.builds
            bf = 'yes'
        except:
            conf.fatal('Builds filter regex invalid')
    else:
        build_filter = None
        bf = 'no'
    conf.env.BUILD_FILTER = build_filter
    conf.msg('Buildset filter', bf, color='GREEN')


def get_config_parser():
    try:
        import configparser
        config = configparser.ConfigParser(strict=False, interpolation=None)
    except:
        # python2
        import ConfigParser as configparser
        config = configparser.ConfigParser(raw=True)
    return config


def get_config_error():
    try:
        import configparser
    except:
        # python2
        import ConfigParser as configparser
    return configparser.Error


def config_path(config):
    return os.path.join(path, config + '.bset')


def config_dir(config):
    return os.path.dirname(config_path(config))


def add_wscript_fun(ctx, fun_name, fun_func):
    node = ctx.path.find_node(Context.WSCRIPT_FILE)
    if node:
        wscript_module = Context.load_module(node.abspath())
        setattr(wscript_module, fun_name, fun_func)


def configs_ini_load(bld, inis, configs):

    def parse_types(bld, value):
        vs = value.lower().strip().split(' ')
        if len(vs) == 1:
            if vs[0] == 'true':
                return True
            if vs[0] == 'false':
                return False
            return None
        if vs[0] == 'version':
            if len(vs) != 3:
                return None
            try:
                rev = int(bld.env.RSB_VERSION)
            except:
                bld.fatal('cannot convert RSB version to a number: ' +
                          bld.env.RSB_VERSION)
            try:
                val = int(vs[2])
            except:
                return None
            if vs[1] == '==':
                return rev == val
            if vs[1] == '!=':
                return rev != val
            if vs[1] == '>':
                return rev > val
            if vs[1] == '<':
                return rev < val
            if vs[1] == '>=':
                return rev >= val
            if vs[1] == '<=':
                return rev <= val
            return None
        return None

    for ini in inis:
        config = get_config_parser()
        try:
            config.read(ini)
        except pkg.configs.get_config_error() as ce:
            bld.fatal('configs ini parse error: ' + str(ce))
        ini_dir = os.path.dirname(os.path.abspath(ini))
        for d in config.defaults():
            i = (d, config.defaults()[d])
            val = parse_types(bld, i[1])
            if val is None:
                bld.fatal('invalid configs item in ' + ini + ': defaults: ' +
                          i[0] + ' = ' + i[1])
            for c in configs:
                if ini_dir == os.path.abspath(config_dir(c['buildset'])):
                    c[d] = val
        for section in config.sections():
            for c in configs:
                if section == os.path.basename(c['buildset']):
                    try:
                        items = config.items(section)
                    except pkg.configs.get_config_error() as ce:
                        bld.fatal('configs ini parse error: ' + str(ce))
                    for i in items:
                        val = parse_types(bld, i[1])
                        if val is None:
                            bld.fatal('invalid configs item in ' + ini + ': ' +
                                      section + ': ' + i[0] + ' = ' + i[1])
                        c[i[0]] = val


def find_buildsets(bld):
    discovered = []
    inis = []
    for root, dirs, files in os.walk(path):
        base = root[len('config') + 1:]
        for f in files:
            r, e = os.path.splitext(f)
            if e == '.bset':
                discovered += [os.path.join(base, r)]
            elif f == 'configs.ini':
                inis += [os.path.join(root, f)]
    bs = [{
        'buildset': b,
        'enabled': True,
        'good': True,
        'dry-run': False
    } for b in discovered]
    if len(bld.env.BUILD_FILTER) > 0:
        bf = re.compile(bld.env.BUILD_FILTER)
        bs = [b for b in bs if bf.match(b['buildset'])]
    configs_ini_load(bld, inis, bs)
    return sorted([b for b in bs if b['enabled']],
                  key=lambda bs: bs['buildset'])


def buildset(bld, build, dry_run):
    name = os.path.basename(build['buildset'])
    log = bld.path.get_bld().find_or_declare(build['buildset'] + '.txt')
    config = config_path(build['buildset'])
    bset = bld.path.find_resource(config)
    if buildset is None:
        bld.fatal('buildset not found: ' + build['buildset'])
    tardir = bld.path.make_node('tar')
    tar = tardir.make_node(os.path.basename(build['buildset']) + '.tar.bz2')
    cmd = bld.env.RSB_SET_BUILDER
    opts = [
        '--prefix=' + bld.env.PREFIX, '--bset-tar-file', '--trace',
        '--log=' + str(log.path_from(bld.path))
    ]
    opts += bld.env.RSB_OPTIONS
    opts_extra = []
    if bld.env.NO_INSTALL:
        opts_extra += ['--no-install']
    if build['dry-run'] or dry_run:
        opts_extra += ['--dry-run']
    run_opts = opts + opts_extra + [build['buildset']]
    pkg_opts = opts + ['--no-install', build['buildset']]
    return {
        'name': name,
        'config': config,
        'buildset': bset,
        'log': log,
        'tardir': tardir,
        'tar': tar,
        'dry-run': build['dry-run'] or dry_run,
        'cmd': cmd,
        'opts': opts,
        'opts-extra': opts_extra,
        'run-opts': run_opts,
        'pkg-opts': pkg_opts
    }
