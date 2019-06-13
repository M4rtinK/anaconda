Summary: Content for the Anaconda built-in help system
Name: anaconda-user-help
URL: https://access.redhat.com/documentation/en-US/Red_Hat_Enterprise_Linux/7/Installation_Guide
Version: 7.1.1
Release: 1%{?dist}

# This is a Red Hat maintained package which is specific to
# our distribution.
#
# The source is thus available only from within this SRPM.
Source0: %{name}-%{version}.tar.gz

%define debug_package %{nil}
%define anacondaver 19.31.108

License: CC-BY-SA
Group: System Environment/Base
BuildRequires: python2-devel
BuildRequires: python-lxml

Requires: anaconda-gui >= %{anacondaver}

%description
This package provides content for the Anaconda built-in help system.

#%prep
#%setup -q

%build
cd install-guide
python prepare_anaconda_help_content.py

%install
mkdir -p %{buildroot}/usr/share/anaconda/help
cp anaconda_help_content/* %{buildroot}/usr/share/anaconda/help

%files
/usr/share/anaconda/help/*

%changelog
* Thu Nov 20 2014 Martin Kolman <mkolman@redhat.com> - 7.1.1-1
- Initial release (mkolman)
  Resolves: rhbz#1234567
