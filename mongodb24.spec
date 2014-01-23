%{!?scl_name_base:%global scl_name_base mongodb}
%{!?scl_name_version:%global scl_name_version 24}
# needed, because we can't use Requires: %{?scl_v8_%{scl_name_base}}
%global scl_v8 v8314

%{!?scl:%global scl %{scl_name_base}%{scl_name_version}}
%scl_package %scl

Summary: Package that installs %scl
Name: %scl_name
Version: 1
Release: 12%{?dist}
License: GPLv2+
Group: Applications/File
Source0:  macros.mongodb24
Source1:  mongodb24-javapackages-provides-wrapper
Source2:  mongodb24-javapackages-requires-wrapper
%if 0%{?rhel} < 7
Requires: scl-utils >= 20120927-8.el6_5
%else
Requires: scl-utils
%endif
Requires: %{scl_v8}
Requires: %{scl_prefix}mongodb-server
BuildRequires: scl-utils-build

%description
This is the main package for %scl Software Collection, which installs
necessary packages to use MongoDB 2.4 server. Software Collections allow
to install more versions of the same package by using alternative
directory structure.
Install this package if you want to use MongoDB 2.4 server on your system

%package runtime
Summary: Package that handles %scl Software Collection.
Group: Applications/File
Requires: scl-utils
Requires: %{scl_v8}
Requires(post): policycoreutils-python, libselinux-utils

%description runtime
Package shipping essential scripts to work with %scl Software Collection.

%package build
Summary: Package shipping basic build configuration
# Require xmvn config/java config at build time
Requires:   %{name}-runtime = %{version}
Group: Applications/File

%description build
Package shipping essential configuration macros to build
%scl Software Collection.

%package scldevel
Summary: Package shipping development files for %scl.
Group: Applications/File

%description scldevel
Development files for %scl (useful e.g. for hierarchical collection
building with transitive dependencies).

%prep
%setup -c -T
# java.conf
cat <<EOF >java.conf
# Java configuration file for %{scl} software collection.
JAVA_LIBDIR=%{_javadir}
JNI_LIBDIR=%{_jnidir}
JVM_ROOT=%{_jvmdir}
EOF
# XMvn config
cat <<EOF >configuration.xml
<!-- XMvn configuration file for %{scl} software collection -->
<configuration>
  <resolverSettings>
    <prefixes>
      <prefix>/opt/rh/%{scl}/root</prefix>
    </prefixes>
  </resolverSettings>
  <installerSettings>
    <metadataDir>opt/rh/%{scl}/root/usr/share/maven-fragments</metadataDir>
  </installerSettings>
  <repositories>
    <repository>
      <id>%{scl}-resolve</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-resolve</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>resolve-system</id>
      <type>compound</type>
      <properties>
        <prefix>/</prefix>
      </properties>
      <configuration>
        <repositories>
          <repository>%{scl}-resolve</repository>
          <repository>base-resolve</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-install</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install-raw-pom</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-raw-pom</repository>
        </repositories>
      </configuration>
    </repository>
    <repository>
      <id>install-effective-pom</id>
      <type>compound</type>
      <properties>
        <prefix>opt/rh/%{scl}/root</prefix>
        <namespace>%{scl}</namespace>
      </properties>
      <configuration>
        <repositories>
          <repository>base-effective-pom</repository>
        </repositories>
      </configuration>
    </repository>
  </repositories>
</configuration>
EOF

%install
mkdir -p %{buildroot}%{_scl_scripts}/root
# During the build of this package, we don't know which architecture it is
# going to be used on, so if we build on 64-bit system and use it on 32-bit,
# the %{_libdir} would stay expanded to '.../lib64'. This way we determine
# architecture everytime the 'scl enable ...' is run and set the
# LD_LIBRARY_PATH accordingly
cat >> %{buildroot}%{_scl_scripts}/enable << EOF
export PATH=%{_bindir}${PATH:+:\${PATH}}
export LIBRARY_PATH=%{_libdir}\${LIBRARY_PATH:+:\${LIBRARY_PATH}}
export LD_LIBRARY_PATH=%{_libdir}\${LD_LIBRARY_PATH:+:\${LD_LIBRARY_PATH}}
export MANPATH=%{_mandir}:\${MANPATH}
export PKG_CONFIG_PATH=%{_libdir}/pkgconfig\${PKG_CONFIG_PATH:+:\${PKG_CONFIG_PATH}}
export CPATH=%{_includedir}\${CPATH:+:\${CPATH}}
# Needed by Java Packages Tools to locate java.conf
export JAVACONFDIRS="%{_sysconfdir}/java:\${JAVACONFDIRS:-/etc/java}"
# Required by XMvn to locate its configuration file(s)
export XDG_CONFIG_DIRS="%{_sysconfdir}/xdg:\${XDG_CONFIG_DIRS:-/etc/xdg}"
# Not really needed by anything for now, but kept for consistency with
# XDG_CONFIG_DIRS.
export XDG_DATA_DIRS="%{_datadir}:\${XDG_DATA_DIRS:-/usr/local/share:/usr/share}"
. scl_source enable %{scl_v8}
EOF
cat >> %{buildroot}%{_scl_scripts}/service-environment << EOF
# Services are started in a fresh environment without any influence of user's
# environment (like environment variable values). As a consequence,
# information of all enabled collections will be lost during service start up.
# If user needs to run a service under any software collection enabled, this
# collection has to be written into %{scl}_SCLS_ENABLED variable in
# /opt/rh/sclname/service-environment.
$(printf '%%s' '%{scl}' | tr '[:lower:][:space:]' '[:upper:]_')_SCLS_ENABLED='%{scl}'
EOF

install -d -m 755 %{buildroot}%{_sysconfdir}/java
install -p -m 644 java.conf %{buildroot}%{_sysconfdir}/java/

install -d -m 755 %{buildroot}%{_sysconfdir}/xdg/xmvn
install -p -m 644 configuration.xml %{buildroot}%{_sysconfdir}/xdg/xmvn/

# install magic for java mvn provides/requires generators
install -Dpm0644 %{SOURCE0} %{buildroot}%{_root_sysconfdir}/rpm/macros.%{name}
install -Dpm0755 %{SOURCE1} %{buildroot}%{_rpmconfigdir}/%{name}-javapackages-provides-wrapper
install -Dpm0755 %{SOURCE2} %{buildroot}%{_rpmconfigdir}/%{name}-javapackages-requires-wrapper

%scl_install

# scldevel garbage
cat >> %{buildroot}%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel << EOF
%%scl_%{scl_name_base} %{scl}
%%scl_prefix_%{scl_name_base} %{scl_prefix}
%%scl_v8_%{scl_name_base} %{scl_v8}
EOF

%post runtime
# Simple copy of context from system root to DSC root.
# In case new version needs some additional rules or context definition,
# it needs to be solved.
semanage fcontext -a -e /var/log/mongodb /var/log/%{scl_prefix}mongodb >/dev/null 2>&1 || :
semanage fcontext -a -e /etc/rc.d/init.d/mongod /etc/rc.d/init.d/%{scl_prefix}mongod >/dev/null 2>&1 || :
semanage fcontext -a -e / %{_scl_root} >/dev/null 2>&1 || :
selinuxenabled && load_policy >/dev/null 2>&1 || :
restorecon -R %{_scl_root} >/dev/null 2>&1 || :
restorecon -R /var/log/%{scl_prefix}mongodb >/dev/null 2>&1 || :
restorecon /etc/rc.d/init.d/%{scl_prefix}mongod >/dev/null 2>&1 || :

%files

%files runtime
%scl_files
%config(noreplace) %{_scl_scripts}/service-environment
%config(noreplace) %{_sysconfdir}/java/java.conf
%config(noreplace) %{_sysconfdir}/xdg/xmvn/configuration.xml

%files build
%{_root_sysconfdir}/rpm/macros.%{scl}-config
%{_root_sysconfdir}/rpm/macros.%{name}
%{_rpmconfigdir}/%{name}*

%files scldevel
%{_root_sysconfdir}/rpm/macros.%{scl_name_base}-scldevel

%changelog
* Thu Jan 23 2014 Jan Pacner <jpacner@redhat.com> - 1-12
- Related: #1055555 (add -scldevel subpackage for shipped build-requires files);
  fix typo

* Mon Jan 20 2014 Jan Pacner <jpacner@redhat.com>
- Resolves: #1055555 (add -scldevel subpackage for shipped build-requires
  garbage)

* Fri Jan 17 2014 Jan Pacner <jpacner@redhat.com> - 1-10
- Resolves: RHBZ#1054644 (mongodb24-runtime needs to depend on newer scl-utils)

* Mon Dec 23 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-9
- Fix osgi() Requires/Provides generation.
- Resolves: RHBZ#1046029
- Fix javadoc requires/provides generation
- Resolves: RHBZ#1046032

* Wed Nov 27 2013 Honza Horak <hhorak@redhat.com> - 1-8
- Added dependency on v8314-runtime

* Tue Nov 26 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-7
- Revert temporary fix for thermostat1-thermostat build.

* Tue Nov 26 2013 Severin Gehwolf <sgehwolf@redhat.com> - 1-6
- Temporarily unbreak the thermostat1-thermostat build.

* Tue Nov 26 2013 Jan Pacner <jpacner@redhat.com> - 1-5
- rename system-wide v8 macro

* Thu Nov 21 2013 Jan Pacner <jpacner@redhat.com> - 1-4
- fix {scl}_SCLS_ENABLED variable
- add dependency on external v8 SCL

* Wed Nov 13 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-3
- Add java mvn provides and requires generator wrapper.

* Thu Nov 07 2013 Severin Gehwolf <sgehwolf@redhat.com> 1-2
- Add java/xmvn config to runtime subpackage.
- Require runtime in build package so as to have java/xmvn
  configs available.

* Mon Aug 12 2013 Honza Horak <hhorak@redhat.com> 1-1
- initial packaging

