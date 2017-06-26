# Only x86_64 and i686 are Tier 1 platforms at this time.
# https://forge.rust-lang.org/platform-support.html
%define rust_arches x86_64 i686 armv7hl aarch64 ppc64 ppc64le s390x

# Only the specified arches will use bootstrap binaries.
#define bootstrap_arches %%{rust_arches}

%define cargo_version %{version}
%define cargo_bootstrap 0.18.0

Summary:	Rust's package manager and build tool
Name:		cargo
Version:	0.19.0
Release:	0.1
License:	ASL 2.0 or MIT
Source0:	https://github.com/rust-lang/cargo/archive/%{cargo_version}/%{name}-%{cargo_version}.tar.gz
# submodule, bundled for local installation only, not distributed
%define rust_installer 4f994850808a572e2cc8d43f968893c8e942e9bf
Source1:	https://github.com/rust-lang/rust-installer/archive/%{rust_installer}/rust-installer-%{rust_installer}.tar.gz

# Use vendored crate dependencies so we can build offline.
# Created using https://github.com/alexcrichton/cargo-vendor/ 0.1.7
# It's so big because some of the -sys crates include the C library source they
# want to link to.  With our -devel buildreqs in place, they'll be used instead.
# FIXME: These should all eventually be packaged on their own!
Source100:	%{name}-%{version}-vendor.tar.xz

URL:		https://crates.io/
%ifarch %{bootstrap_arches}
%define bootstrap_root cargo-%{cargo_bootstrap}-%{rust_triple}
%define local_cargo %{_builddir}/%{bootstrap_root}/cargo/bin/cargo
%else
BuildRequires:	%{name} >= 0.13.0
%define local_cargo %{_bindir}/%{name}
%endif

BuildRequires:	cmake
BuildRequires:	gcc
BuildRequires:	rust
# Indirect dependencies for vendored -sys crates above
BuildRequires:	curl-devel
BuildRequires:	libgit2-devel >= 0.24
BuildRequires:	libssh2-devel
BuildRequires:	openssl-devel
BuildRequires:	pkgconfig
BuildRequires:	zlib-devel
Requires:	rust
ExclusiveArch:	%{rust_arches}

%define rust_triple %{_target_cpu}-unknown-linux-gnu

%description
Cargo is a tool that allows Rust projects to declare their various
dependencies and ensure that you'll always get a repeatable build.

%prep
%ifarch %{bootstrap_arches}
%setup -q -n %{bootstrap_root} -T -b %{bootstrap_source}
test -f '%{local_cargo}'
%endif

# vendored crates
%setup -q -n %{name}-%{version}-vendor -T -b 100

# cargo sources
%setup -q -n %{name}-%{cargo_version}

# rust-installer
%setup -q -n %{name}-%{cargo_version} -T -D -a 1
rmdir src/rust-installer
mv rust-installer-%{rust_installer} src/rust-installer

# define the offline registry
%define cargo_home $PWD/.cargo
mkdir -p %{cargo_home}
cat >.cargo/config <<EOF
[source.crates-io]
registry = 'https://github.com/rust-lang/crates.io-index'
replace-with = 'vendored-sources'

[source.vendored-sources]
directory = '$PWD/../%{name}-%{version}-vendor'
EOF

# This should eventually migrate to distro policy
# Enable optimization, debuginfo, and link hardening.
%define rustflags -Copt-level=3 -Cdebuginfo=2 -Clink-arg=-Wl,-z,relro,-z,now

%build
# convince libgit2-sys to use the distro libgit2
export LIBGIT2_SYS_USE_PKG_CONFIG=1

# use our offline registry and custom rustc flags
export CARGO_HOME="%{cargo_home}"
export RUSTFLAGS="%{rustflags}"

%configure \
	--disable-option-checking \
	--build=%{rust_triple} --host=%{rust_triple} --target=%{rust_triple} \
	--rustc=%{_bindir}/rustc --rustdoc=%{_bindir}/rustdoc \
	--cargo=%{local_cargo} \
	--release-channel=stable \
	--disable-cross-tests

%{__make}

%install
rm -rf $RPM_BUILD_ROOT
export CARGO_HOME="%{cargo_home}"
export RUSTFLAGS="%{rustflags}"

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

# Remove installer artifacts (manifests, uninstall scripts, etc.)
rm -rv $RPM_BUILD_ROOT%{_prefix}/lib/

# Fix the etc/ location
mv -v $RPM_BUILD_ROOT%{_prefix}/%{_sysconfdir} $RPM_BUILD_ROOT%{_sysconfdir}

# Remove unwanted documentation files (we already package them)
rm -rf $RPM_BUILD_ROOT%{_docdir}/%{name}/

# Create the path for crate-devel packages
install -d $RPM_BUILD_ROOT%{_datadir}/cargo/registry

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc LICENSE-APACHE LICENSE-MIT LICENSE-THIRD-PARTY
%doc README.md
%attr(755,root,root) %{_bindir}/cargo
%{_mandir}/man1/cargo*.1*
%{_sysconfdir}/bash_completion.d/cargo
%{zsh_compdir}/_cargo
%dir %{_datadir}/cargo
%dir %{_datadir}/cargo/registry
