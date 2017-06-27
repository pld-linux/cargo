#
# Conditional build:
%bcond_with	bootstrap
%bcond_without	tests		# build without tests

%define cargo_version %{version}
%define cargo_bootstrap 0.18.0

Summary:	Rust's package manager and build tool
Name:		cargo
Version:	0.19.0
Release:	0.1
License:	ASL 2.0 or MIT
Group:		Development/Libraries
Source0:	https://github.com/rust-lang/cargo/archive/%{cargo_version}/%{name}-%{cargo_version}.tar.gz
# Source0-md5:	e46e9f565df765b63f641c0d933297d7
# submodule, bundled for local installation only, not distributed
%define rust_installer 4f994850808a572e2cc8d43f968893c8e942e9bf
Source1:	https://github.com/rust-lang/rust-installer/archive/%{rust_installer}/rust-installer-%{rust_installer}.tar.gz
# Source1-md5:	a222edd3ab08779f527aafe862207027
Source2:	https://static.rust-lang.org/dist/cargo-%{cargo_bootstrap}-x86_64-unknown-linux-gnu.tar.gz
# Source2-md5:	d2cbab6378c1f60b483efa0f076a8f81
Source3:	https://static.rust-lang.org/dist/cargo-%{cargo_bootstrap}-i686-unknown-linux-gnu.tar.gz
# Source3-md5:	1ad24c241a2f5e3c4bf83855766fab35
# Use vendored crate dependencies so we can build offline.
# Created using https://github.com/alexcrichton/cargo-vendor/ 0.1.7
# It's so big because some of the -sys crates include the C library source they
# want to link to.  With our -devel buildreqs in place, they'll be used instead.
# FIXME: These should all eventually be packaged on their own!
Source4:	%{name}-%{version}-vendor.tar.xz
# Source4-md5:	c8025d6ba2aa668c0bafc468ec354630
Patch0:		use-system-libgit2.patch
URL:		https://crates.io/
%{!?with_bootstrap:BuildRequires:	%{name} >= 0.13.0}
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
ExclusiveArch:	%{x8664} %{ix86}

%define rust_triple %{_target_cpu}-unknown-linux-gnu

%if %{with bootstrap}
%define		bootstrap_root	cargo-%{cargo_bootstrap}-%{rust_triple}
%define		local_cargo	%{_builddir}/%{name}-%{version}/%{bootstrap_root}/cargo/bin/cargo
%else
%define		local_cargo	%{_bindir}/%{name}
%endif

# This should eventually migrate to distro policy
# Enable optimization, debuginfo, and link hardening.
%define		rustflags	-Copt-level=3 -Cdebuginfo=2 -Clink-arg=-Wl,-z,relro,-z,now

%description
Cargo is a tool that allows Rust projects to declare their various
dependencies and ensure that you'll always get a repeatable build.

%prep
%setup -q -n %{name}-%{cargo_version} -a1 -a4
%if %{with bootstrap}
%ifarch %{x8664}
tar xf %{SOURCE2}
%endif
%ifarch %{ix86}
tar xf %{SOURCE3}
%endif
test -f '%{local_cargo}'
%endif
%patch0 -p1

rmdir src/rust-installer
mv rust-installer-%{rust_installer} src/rust-installer

# use our offline registry and custom rustc flags
export CARGO_HOME="`pwd`/.cargo"
export RUSTFLAGS="%{rustflags}"

mkdir -p "$CARGO_HOME"
cat >.cargo/config <<EOF
[source.crates-io]
registry = 'https://github.com/rust-lang/crates.io-index'
replace-with = 'vendored-sources'

[source.vendored-sources]
directory = '$PWD/vendor'
EOF

%build
# convince libgit2-sys to use the distro libgit2
export LIBGIT2_SYS_USE_PKG_CONFIG=1

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
export CARGO_HOME="`pwd`/.cargo"
export RUSTFLAGS="%{rustflags}"

%{__make} install \
	DESTDIR=$RPM_BUILD_ROOT

# Remove installer artifacts (manifests, uninstall scripts, etc.)
rm -rv $RPM_BUILD_ROOT%{_prefix}/lib/

# Fix the etc/ location
mv -v $RPM_BUILD_ROOT%{_prefix}/%{_sysconfdir} $RPM_BUILD_ROOT%{_sysconfdir}

# Remove unwanted documentation files (we already package them)
rm -r $RPM_BUILD_ROOT%{_docdir}/%{name}/

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
