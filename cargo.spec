#
# Conditional build:
%bcond_with	bootstrap	# bootstrap using precompiled binaries
%bcond_without	tests		# build without tests

%define		cargo_version	%{version}
%define		cargo_bootstrap	0.18.0

Summary:	Rust's package manager and build tool
Summary(pl.UTF-8):	Zarządca pakietów i narzędzie do budowania
Name:		cargo
Version:	0.26.0
Release:	1
License:	Apache v2.0 or MIT
Group:		Development/Tools
Source0:	https://github.com/rust-lang/cargo/archive/%{cargo_version}/%{name}-%{cargo_version}.tar.gz
# Source0-md5:	9929f01186583c5c9f01b587356a7c92
Source2:	https://static.rust-lang.org/dist/%{name}-%{cargo_bootstrap}-x86_64-unknown-linux-gnu.tar.gz
# Source2-md5:	d2cbab6378c1f60b483efa0f076a8f81
Source3:	https://static.rust-lang.org/dist/%{name}-%{cargo_bootstrap}-i686-unknown-linux-gnu.tar.gz
# Source3-md5:	1ad24c241a2f5e3c4bf83855766fab35
# Use vendored crate dependencies so we can build offline.
# Created using https://github.com/alexcrichton/cargo-vendor/ 0.1.13
# It's so big because some of the -sys crates include the C library source they
# want to link to.  With our -devel buildreqs in place, they'll be used instead.
# FIXME: These should all eventually be packaged on their own!
# PLD: using sources vendored by Fedora
Source4:	https://src.fedoraproject.org/repo/pkgs/cargo/%{name}-%{version}-vendor.tar.xz/sha512/6ed2a1644c9b18fc24ddad5350d41b6c36cd5b62de4cf0b748a57b589f4f0ac12f91461989158d58d0892bf6fc2c1626cf574e7e2b9da4b0e35f72dfd88f9048/%{name}-%{version}-vendor.tar.xz
# Source4-md5:	bf5dd065f46ece6a0d30dbd3216508a0
Patch0:		x32.patch
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
ExclusiveArch:	%{x8664} %{ix86} x32
BuildRoot:	%{tmpdir}/%{name}-%{version}-root-%(id -u -n)

%ifarch x32
%define		rust_triple	x86_64-unknown-linux-gnux32
%else
%define		rust_triple	%{_target_cpu}-unknown-linux-gnu
%endif

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

%description -l pl.UTF-8
Cargo to narzędzie pozwalające projektom w języku Rust deklarować ich
zależności i zapewniające powtarzalność procesu budowania.

%package -n bash-completion-cargo
Summary:	Bash completion for cargo command
Summary(pl.UTF-8):	Bashowe dopełnianie parametrów polecenia cargo
Group:		Applications/Shells
Requires:	%{name} = %{version}-%{release}
Requires:	bash-completion

%description -n bash-completion-cargo
Bash completion for cargo command.

%description -n bash-completion-cargo -l pl.UTF-8
Bashowe dopełnianie parametrów polecenia cargo.

%package -n zsh-completion-cargo
Summary:	Zsh completion for cargo command
Summary(pl.UTF-8):	Dopełnianie parametrów polecenia cargo w powłoce Zsh
Group:		Applications/Shells
Requires:	%{name} = %{version}-%{release}
Requires:	bash-completion

%description -n zsh-completion-cargo
Zsh completion for cargo command.

%description -n zsh-completion-cargo -l pl.UTF-8
Dopełnianie parametrów polecenia cargo w powłoce Zsh.

%prep
%setup -q -n %{name}-%{cargo_version} -a4
%ifarch x32
%patch0 -p1
%endif

%if %{with bootstrap}
%ifarch %{x8664}
tar xf %{SOURCE2}
%endif
%ifarch %{ix86}
tar xf %{SOURCE3}
%endif
test -f '%{local_cargo}'
%endif

# use our offline registry
export CARGO_HOME="`pwd`/.cargo"

mkdir -p "$CARGO_HOME"
cat >.cargo/config <<EOF
[source.crates-io]
registry = 'https://github.com/rust-lang/crates.io-index'
replace-with = 'vendored-sources'

[source.vendored-sources]
directory = '$PWD/vendor'
EOF

%build
# use our offline registry and custom rustc flags
export CARGO_HOME="`pwd`/.cargo"
export RUSTFLAGS="%{rustflags}"

# convince libgit2-sys to use the distro libgit2
export LIBGIT2_SYS_USE_PKG_CONFIG=1

%{local_cargo} build --release

%install
rm -rf $RPM_BUILD_ROOT
export CARGO_HOME="`pwd`/.cargo"
export RUSTFLAGS="%{rustflags}"

%{local_cargo} install --root $RPM_BUILD_ROOT%{_prefix}
rm $RPM_BUILD_ROOT%{_prefix}/.crates.toml

install -d $RPM_BUILD_ROOT%{_mandir}/man1
install -p src%{_sysconfdir}/man/cargo*.1 $RPM_BUILD_ROOT%{_mandir}/man1

install -p src%{_sysconfdir}/cargo.bashcomp.sh \
  -D $RPM_BUILD_ROOT%{_sysconfdir}/bash_completion.d/cargo

install -p src%{_sysconfdir}/_cargo \
  -D $RPM_BUILD_ROOT%{zsh_compdir}/_cargo

# Create the path for crate-devel packages
install -d $RPM_BUILD_ROOT%{_datadir}/cargo/registry

%clean
rm -rf $RPM_BUILD_ROOT

%files
%defattr(644,root,root,755)
%doc LICENSE-APACHE LICENSE-MIT LICENSE-THIRD-PARTY README.md
%attr(755,root,root) %{_bindir}/cargo
%{_mandir}/man1/cargo*.1*
%dir %{_datadir}/cargo
%dir %{_datadir}/cargo/registry

%files -n bash-completion-cargo
%defattr(644,root,root,755)
%{_sysconfdir}/bash_completion.d/cargo

%files -n zsh-completion-cargo
%defattr(644,root,root,755)
%{zsh_compdir}/_cargo
