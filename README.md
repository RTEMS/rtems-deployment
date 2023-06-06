# RTEMS Deployment

Deployment is the process a team or organization uses to provide
configuration controlled tools and libraries that are used to build
RTEMS applications. An RTEMS application can be viewed as a vertical
software stack and deployment of RTEMS is a way to manage this
complexity across a team.

Deployment using this tool is based on building vertical stacks using
the RSB. The project provides buildset configurations that contain
the buildsets a team or organization needs to build configuration
managed RTEMS applications.

A deployment of RTEMS can be based on a tar file or a package for a
supported operating system, for example RPM. This repo is organized to
integrate with Constant Integration (CI) workflows by providing a
common interface to the management of specific configurations across
different operating systems and deployment options.

The output of this project normally forms part of a wider deployment
model a team or organization uses. An example is containers on
Linux. A container can contain the RPM built by this tool and the
container can be used as a base for application development. For
example the Gemini project uses GitLab CI workflows to automatically
build Docker containers that have the RPM output from this tool
installed.

The deployment project provides:

1. Buildset configurations for users, organization and commonly used
   builds.

2. Host operating system specific packaging if supported.

3. Regression tests build configurations for the RSB.

4. Examples of buildset configuration files for deployment.

5. Waf based build scripts that are used to create custom deployment
   workflows for teams and organizations.

The repo is open and anyone can add a buildset configuration so please
ask.

The repo uses waf but you do not need to learn or understand waf to
use it.

## Deployable Packages

Deployment is based on the system level requirements a project or
organization has.

### Single Package

The single package deployment model has a top level buildset
configuration file that builds a single output package containing all
the packages a projects needs.

An organization can have more than one single package, for example
different versions of RTEMS. If more than one package is to be
installed use the prefix to make sure there are not conflicts.

A single package is easier to configuration manage because the output
package contains all the pieces in the vertical software
stack. Installing the output package installs all the vertical stack
layers at the same time.

### Multiple Packages

Multiple packages means each part in a vertical stack is built
separately and managed externally. Correct management requires extra
tools or logic to make sure all the pieces are built vertically
against the lower layers. Packaging and installation needs to account
for the dependencies between the packages.

Packaging systems provide support for multiple packages and can be
used if supported. Multiple packages support a common install path
because the common pieces need to be handled when packaging.

Supporting multiple packages is more complex because each layer built
needs to be packaged and installed so it can be used to build higher
layers. Packaging needs to understand the common pieces in each
package and those need to be packaged in common packages other
packages depend on. This can become complex if the vertical stack is
not fully defined.

Multiple packages is not supported by this repo.

## Host Support

You can build a deployment package for the host packaging formats
listed in the section. The package built is a deployment snapshot of
the tools, libraries and headers files. The package should not be
viewed the same as packages your host provides. There is no sharing of
common files between packages this tool builds. You should consider
the deployment as the super set of what your team or organization
needs.

A host packaging system provides you with the ability to query what is
installed as well being able to verify what is installed against what
was built.

### RPM

An RPM package can be built. This has been tested on Rocky
distributions. The `configure` option provdes support to customise the
RPM information to capture site specific details.

## RTEMS Source Builder

The RTEMS Source Builder or RSB is a package that builds tools, board
support packages (BSP) and third party libraries for RTEMS. The RSB is
a tool that can be embedded into custom workflows to support
deployment.

The RSB provides a stable interface across releases of RTEMS. Using it
to deploy RTEMS packages lets a deployment workflow work across
different releases of RTEMS.

## Requirements

- Please follow the RTEMS User Guide's Quick Start and Host section to
  get a properly configured host that can build RTEMS tools.

- A copy of the RSB in source. It can be a released tar file or a
  cloned git repo. You provide the path to the source tree.

## Instructions

The default configuration does not install the built output. A  and to
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

2. The optional `--prefix` option lets you set an install path for the
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
for your team or organization:

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

### RPM

Generate RPM spec files using:

```
./waf rpmspec
```

Build the RPM using the RPM build tool:

```
rpmbuild -bb out/gemini/gemini-powerpc-net-legacy-bsps.spec
```

You can use `configure` to provide an RPM configuration INI file to
override specific fields in the RPM spec file. The INI format is:

```
[DEFAULT]

[<configuration>]
<key> = <value>
```

where:

`<configuration>` is a configuration being built

`<key>` is a key. The keys are:

- `rpm_name` : The name of the RPM

- `rpm_version` : Site specific version of the RPM

- `rpm_summary` : The RPM Summary

- `rpm_description` : The RPM description

An example for Gemini the INI called `gemini.ini` is:

```
[DEFAULT]

[gemini/gemini-powerpc-legacy-bsps]
rpm_name = rtems-gemini-powerpc-legacy
rpm_version = %{rsb_version}.%{rsb_revision}
rpm_revision = %{gemini_version}%{?dist}

[gemini/gemini-powerpc-net-legacy-bsps]
rpm_name = rtems-gemini-powerpc-net-legacy
rpm_version = %{rsb_version}.%{rsb_revision}
rpm_revision = %{gemini_version}%{?dist}
```

RPM configuration values can also be supplied on the `configure`
command line as options. For example the following command line can be
used with the `gemini.ini` configuration:

```
--rpm-config-value=gemini_version=123456
```

A site configuration INI file and the `configure` command line options
provides a simple way to integrate site information needed to
deployment configuration control and auditing into a CI process.
