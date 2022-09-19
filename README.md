# RTEMS RSB Deployment Tests

This project provides buildset configuration scripts to test the
RSB. It provides:

1. Regression tests for the RSB

2. Examples of buildset configuration files for deployment

3. Waf build script as a template that can be used to create
   deplayment workflows for teams and organisations.


## RTEMS Source Builder

The RTEMS Source Builder or RSB is a package that builds tools, board
support packages (BSP) and third party libraries for RTEMS. The RSB is
a tool that can be embedded into custom workflows to provide a base
for deployment of tools, BSPs and libraries for users, teams and
organisations.

Deplopyment of tools, BSPs and libraries provides a stable common base
for all uses in project. Stable and controlled delivery can be
achieved when combined with a host's package management system.


## Requirements

- Please follow the RTEMS User Guide's Quick Start and Host section to
  get a properly configured host that can build RTEMS tools.

- A copy of the RSB in source. It can be a released tar file or a
  cloned git repo.


## Instructions

The default configuration does not install the built output and to
create a tar file. This is the RSB deployment mode. You can optionally
configure a prefix if you wish to install the built output or use the
build set tar file created by the builds.

### Help

The `waf` build system provides help:

```
./waf --help
```

**Configuration**:

To run a test build you must first run `configure`. Valid configure options are:

1. The `--rsb` option provides the path to the RSB to use when
   running the build set commands.

2. The optional `--prefx` option lets you set an install path for the
   build if the install mode is `install`.

3. The `--install` option enable the install mode. By default the
   builds do not install any output. Use this option with the `--prefix` option
   if you want to use the tools directly.

3. The `--rtems-version` options lets you specify the version of the
   RSB to test.

**Build**:

1. The `list` command will list the build targets.

2. The build `--targets` options lets you specific a build set
   configuration to run. This helps target or select a specific build
   set from the group of builds provided.

### Build All

Configure the build with the RSB you wish to use. Please sure the RSB
is the right version for the version configured:

```
./waf configure --rsb=../rtems-source-builder
```

Build:

```
./waf
```

### Dry Run

A dry-run is useful to check the RSB configurations are usable. Using
the Build All configuration:

```
./waf dry-run
```

### Show

Show the RSB commands for the build sets:

```
./waf show
```

### Prefix

The configure `--prefix` option lets you specify a deployment prefix
for your team or organisation:

```
./waf configure --rsb=../rtems-source-builder --prefix=/opt/project
```

All built sets built will use this prefix and the tar files create in
the build will use this path. Run the builds:

```
./waf
```

Use the `--targets=` option to select a specific build.Installing

### Installing

To install the output provide a prefix to a writable location on your disk:

```
./waf configure --rsb=../rtems-source-builder --prefix=/opt/project --install
```

Each build set will install to the prefix path. Run the builds:

```
./waf
```

Use the `--targets=` option to select a specific build.
