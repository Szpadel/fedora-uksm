# We have to override the new %%install behavior because, well... the kernel is special.
%global __spec_install_pre %{___build_pre}

# At the time of this writing (2019-03), RHEL8 packages use w2.xzdio
# compression for rpms (xz, level 2).
# Kernel has several large (hundreds of mbytes) rpms, they take ~5 mins
# to compress by single-threaded xz. Switch to threaded compression,
# and from level 2 to 3 to keep compressed sizes close to "w2" results.
#
# NB: if default compression in /usr/lib/rpm/redhat/macros ever changes,
# this one might need tweaking (e.g. if default changes to w3.xzdio,
# change below to w4T.xzdio):
#
# This is disabled on i686 as it triggers oom errors

%ifnarch i686
%define _binary_payload w3T.xzdio
%endif

Summary: The Linux kernel

# For a kernel released for public testing, released_kernel should be 1.
# For internal testing builds during development, it should be 0.
# For rawhide and/or a kernel built from an rc or git snapshot,
# released_kernel should be 0.
# For a stable, released kernel, released_kernel should be 1.
%global released_kernel 1

%if 0%{?fedora}
%define secure_boot_arch x86_64
%else
%define secure_boot_arch x86_64 aarch64 s390x ppc64le
%endif

# Signing for secure boot authentication
%ifarch %{secure_boot_arch}
%global signkernel 1
%else
%global signkernel 0
%endif

# Sign modules on all arches
%global signmodules 1

# Compress modules only for architectures that build modules
%ifarch noarch
%global zipmodules 0
%else
%global zipmodules 1
%endif

%if %{zipmodules}
%global zipsed -e 's/\.ko$/\.ko.xz/'
%endif

# define buildid .local

%if 0%{?fedora}
%define primary_target fedora
%else
%define primary_target rhel
%endif

# baserelease defines which build revision of this kernel version we're
# building.  We used to call this fedora_build, but the magical name
# baserelease is matched by the rpmdev-bumpspec tool, which you should use.
#
# We used to have some extra magic weirdness to bump this automatically,
# but now we don't.  Just use: rpmdev-bumpspec -c 'comment for changelog'
# When changing base_sublevel below or going from rc to a final kernel,
# reset this by hand to 1 (or to 0 and then use rpmdev-bumpspec).
# scripts/rebase.sh should be made to do that for you, actually.
#
# NOTE: baserelease must be > 0 or bad things will happen if you switch
#       to a released kernel (released version will be < rc version)
#
# For non-released -rc kernels, this will be appended after the rcX and
# gitX tags, so a 3 here would become part of release "0.rcX.gitX.3"
#
%global baserelease 201
%global fedora_build %{baserelease}

# base_sublevel is the kernel version we're starting with and patching
# on top of -- for example, 3.1-rc7-git1 starts with a 3.0 base,
# which yields a base_sublevel of 0.
%define base_sublevel 4

## If this is a released kernel ##
%if 0%{?released_kernel}

# Do we have a -stable update to apply?
%define stable_update 12
# Set rpm version accordingly
%if 0%{?stable_update}
%define stablerev %{stable_update}
%define stable_base %{stable_update}
%endif
%define rpmversion 5.%{base_sublevel}.%{stable_update}

## The not-released-kernel case ##
%else
# The next upstream release sublevel (base_sublevel+1)
%define upstream_sublevel %(echo $((%{base_sublevel} + 1)))
# The rc snapshot level
%global rcrev 0
# The git snapshot level
%define gitrev 0
# Set rpm version accordingly
%define rpmversion 5.%{upstream_sublevel}.0
%endif
# Nb: The above rcrev and gitrev values automagically define Patch00 and Patch01 below.

# What parts do we want to build?  We must build at least one kernel.
# These are the kernels that are built IF the architecture allows it.
# All should default to 1 (enabled) and be flipped to 0 (disabled)
# by later arch-specific checks.

# The following build options are enabled by default.
# Use either --without <opt> in your rpmbuild command or force values
# to 0 in here to disable them.
#
# standard kernel
%define with_up        %{?_without_up:        0} %{?!_without_up:        1}
# kernel PAE (only valid for ARM (lpae))
%define with_pae       %{?_without_pae:       0} %{?!_without_pae:       1}
# kernel-debug
%define with_debug     %{?_without_debug:     0} %{?!_without_debug:     1}
# kernel-doc
%define with_doc       %{?_without_doc:       0} %{?!_without_doc:       1}
# kernel-headers
%define with_headers   %{?_without_headers:   0} %{?!_without_headers:   1}
%define with_cross_headers   %{?_without_cross_headers:   0} %{?!_without_cross_headers:   1}
# kernel-debuginfo
%define with_debuginfo %{?_without_debuginfo: 0} %{?!_without_debuginfo: 1}
# Want to build a the vsdo directories installed
%define with_vdso_install %{?_without_vdso_install: 0} %{?!_without_vdso_install: 1}
# kernel-zfcpdump (s390 specific kernel for zfcpdump)
%define with_zfcpdump  %{?_without_zfcpdump:  0} %{?!_without_zfcpdump:  1}
# kernel-abi-whitelists
%define with_kernel_abi_whitelists %{?_without_kernel_abi_whitelists: 0} %{?!_without_kernel_abi_whitelists: 1}
# internal samples and selftests
%define with_selftests %{?_without_selftests: 0} %{?!_without_selftests: 1}
#
# Additional options for user-friendly one-off kernel building:
#
# Only build the base kernel (--with baseonly):
%define with_baseonly  %{?_with_baseonly:     1} %{?!_with_baseonly:     0}
# Only build the pae kernel (--with paeonly):
%define with_paeonly   %{?_with_paeonly:      1} %{?!_with_paeonly:      0}
# Only build the debug kernel (--with dbgonly):
%define with_dbgonly   %{?_with_dbgonly:      1} %{?!_with_dbgonly:      0}
# Control whether we perform a compat. check against published ABI.
%define with_kabichk   %{?_without_kabichk:   0} %{?!_without_kabichk:   1}
# Temporarily disable kabi checks until RC.
%define with_kabichk 0
# Control whether we perform a compat. check against DUP ABI.
%define with_kabidupchk %{?_with_kabidupchk:  1} %{?!_with_kabidupchk:   0}
#
# Control whether to run an extensive DWARF based kABI check.
# Note that this option needs to have baseline setup in SOURCE300.
%define with_kabidwchk %{?_without_kabidwchk: 0} %{?!_without_kabidwchk: 1}
%define with_kabidw_base %{?_with_kabidw_base: 1} %{?!_with_kabidw_base: 0}
#
# should we do C=1 builds with sparse
%define with_sparse    %{?_with_sparse:       1} %{?!_with_sparse:       0}
#
# Cross compile requested?
%define with_cross    %{?_with_cross:         1} %{?!_with_cross:        0}
#
# build a release kernel on rawhide
%define with_release   %{?_with_release:      1} %{?!_with_release:      0}

# verbose build, i.e. no silent rules and V=1
%define with_verbose %{?_with_verbose:        1} %{?!_with_verbose:      0}

#
# check for mismatched config options
%define with_configchecks %{?_without_configchecks:        0} %{?!_without_configchecks:        1}

#
# gcov support
%define with_gcov %{?_with_gcov: 1} %{?!_with_gcov: 0}

#
# ipa_clone support
%define with_ipaclones %{?_without_ipaclones: 0} %{?!_without_ipaclones: 1}

# Want to build a vanilla kernel build without any non-upstream patches?
%define with_vanilla %{?_with_vanilla: 1} %{?!_with_vanilla: 0}

# Set debugbuildsenabled to 1 for production (build separate debug kernels)
#  and 0 for rawhide (all kernels are debug kernels).
# See also 'make debug' and 'make release'.
%define debugbuildsenabled 1

%if 0%{?fedora}
# Kernel headers are being split out into a separate package
%define with_headers 0
%define with_cross_headers 0
# no selftests for now
%define with_selftests 0
# no ipa_clone for now
%define with_ipaclones 0
# no whitelist
%define with_kernel_abi_whitelists 0
# Fedora builds these separately
%define with_perf 0
%define with_tools 0
%define with_bpftool 0
%endif

%if %{with_verbose}
%define make_opts V=1
%else
%define make_opts -s
%endif

# pkg_release is what we'll fill in for the rpm Release: field
%if 0%{?released_kernel}

%define pkg_release %{fedora_build}%{?buildid}%{?dist}

%else

# non-released_kernel
%if 0%{?rcrev}
%define rctag .rc%rcrev
%else
%define rctag .rc0
%endif
%if 0%{?gitrev}
%define gittag .git%gitrev
%else
%define gittag .git0
%endif
%define pkg_release 0%{?rctag}%{?gittag}.%{fedora_build}%{?buildid}%{?dist}

%endif

# The kernel tarball/base version
%define kversion 5.%{base_sublevel}


# turn off debug kernel and kabichk for gcov builds
%if %{with_gcov}
%define with_debug 0
%define with_kabichk 0
%define with_kabidupchk 0
%define with_kabidwchk 0
%endif

# turn off kABI DWARF-based check if we're generating the base dataset
%if %{with_kabidw_base}
%define with_kabidwchk 0
%endif

# kpatch_kcflags are extra compiler flags applied to base kernel
# -fdump-ipa-clones is enabled only for base kernels on selected arches
%if %{with_ipaclones}
%ifarch x86_64 ppc64le
%define kpatch_kcflags -fdump-ipa-clones
%else
%define with_ipaclones 0
%endif
%endif

%define make_target bzImage
%define image_install_path boot

%define KVERREL %{version}-%{release}.%{_target_cpu}
%define KVERREL_RE %(echo %KVERREL | sed 's/+/[+]/g')
%define hdrarch %_target_cpu
%define asmarch %_target_cpu

%if 0%{!?nopatches:1}
%define nopatches 0
%endif

%if %{with_vanilla}
%define nopatches 1
%endif

%if %{nopatches}
%define variant -vanilla
%endif

%if !%{debugbuildsenabled}
%define with_debug 0
%endif

%if !%{with_debuginfo}
%define _enable_debug_packages 0
%endif
%define debuginfodir /usr/lib/debug
# Needed because we override almost everything involving build-ids
# and debuginfo generation. Currently we rely on the old alldebug setting.
%global _build_id_links alldebug

# kernel PAE is only built on ARMv7
%ifnarch armv7hl
%define with_pae 0
%endif

# if requested, only build base kernel
%if %{with_baseonly}
%define with_pae 0
%define with_debug 0
%endif

# if requested, only build pae kernel
%if %{with_paeonly}
%define with_up 0
%define with_debug 0
%endif

# if requested, only build debug kernel
%if %{with_dbgonly}
%if %{debugbuildsenabled}
%define with_up 0
%define with_pae 0
%endif
%define with_pae 0
%endif

# turn off kABI DUP check and DWARF-based check if kABI check is disabled
%if !%{with_kabichk}
%define with_kabidupchk 0
%define with_kabidwchk 0
%endif

%if %{with_vdso_install}
%define use_vdso 1
%endif


%ifnarch noarch
%define with_kernel_abi_whitelists 0
%endif

# Overrides for generic default options

# only package docs noarch
%ifnarch noarch
%define with_doc 0
%define doc_build_fail true
%endif

%if 0%{?fedora}
# don't do debug builds on anything but i686 and x86_64
%ifnarch i686 x86_64
%define with_debug 0
%endif
%endif

# don't build noarch kernels or headers (duh)
%ifarch noarch
%define with_up 0
%define with_headers 0
%define with_cross_headers 0
%define with_selftests 0
%define with_debug 0
%define all_arch_configs kernel-%{version}-*.config
%endif

# sparse blows up on ppc
%ifnarch ppc64le
%define with_sparse 0
%endif

# zfcpdump mechanism is s390 only
%ifnarch s390x
%define with_zfcpdump 0
%endif

%if 0%{?fedora}
# This is not for Fedora
%define with_zfcpdump 0
%endif

# Per-arch tweaks

%ifarch i686
%define asmarch x86
%define hdrarch i386
%define all_arch_configs kernel-%{version}-i?86*.config
%define kernel_image arch/x86/boot/bzImage
%endif

%ifarch x86_64
%define asmarch x86
%define all_arch_configs kernel-%{version}-x86_64*.config
%define kernel_image arch/x86/boot/bzImage
%endif

%ifarch ppc64le
%define asmarch powerpc
%define hdrarch powerpc
%define make_target vmlinux
%define kernel_image vmlinux
%define kernel_image_elf 1
%define all_arch_configs kernel-%{version}-ppc64le*.config
%define kcflags -O3
%endif

%ifarch s390x
%define asmarch s390
%define hdrarch s390
%define all_arch_configs kernel-%{version}-s390x.config
%define kernel_image arch/s390/boot/bzImage
%endif

%ifarch %{arm}
%define all_arch_configs kernel-%{version}-arm*.config
%define skip_nonpae_vdso 1
%define asmarch arm
%define hdrarch arm
%define make_target bzImage
%define kernel_image arch/arm/boot/zImage
# http://lists.infradead.org/pipermail/linux-arm-kernel/2012-March/091404.html
%define kernel_mflags KALLSYMS_EXTRA_PASS=1
# we only build headers/perf/tools on the base arm arches
# just like we used to only build them on i386 for x86
%ifnarch armv7hl
%define with_headers 0
%define with_cross_headers 0
%endif
# These currently don't compile on armv7
%define with_selftests 0
%endif

%ifarch aarch64
%define all_arch_configs kernel-%{version}-aarch64*.config
%define asmarch arm64
%define hdrarch arm64
%define make_target Image.gz
%define kernel_image arch/arm64/boot/Image.gz
%endif

# Should make listnewconfig fail if there's config options
# printed out?
%if %{nopatches}
%define with_configchecks 0
%endif

# To temporarily exclude an architecture from being built, add it to
# %%nobuildarches. Do _NOT_ use the ExclusiveArch: line, because if we
# don't build kernel-headers then the new build system will no longer let
# us use the previous build of that package -- it'll just be completely AWOL.
# Which is a BadThing(tm).

# We only build kernel-headers on the following...
%if 0%{?fedora}
%define nobuildarches i386
%else
%define nobuildarches i386 i686
%endif

%ifarch %nobuildarches
%define with_up 0
%define with_debug 0
%define with_debuginfo 0
%define with_selftests 0
%define with_pae 0
%define _enable_debug_packages 0
%endif

# Architectures we build tools/cpupower on
%if 0%{?fedora}
%define cpupowerarchs %{ix86} x86_64 ppc64le %{arm} aarch64
%else
%define cpupowerarchs i686 x86_64 ppc64le aarch64
%endif

%if %{use_vdso}

%if 0%{?skip_nonpae_vdso}
%define _use_vdso 0
%else
%define _use_vdso 1
%endif

%else
%define _use_vdso 0
%endif

#
# Packages that need to be installed before the kernel is, because the %%post
# scripts use them.
#
%define kernel_prereq  coreutils, systemd >= 203-2, /usr/bin/kernel-install
%define initrd_prereq  dracut >= 027


Name: kernel%{?variant}
License: GPLv2 and Redistributable, no modification permitted
URL: https://www.kernel.org/
Version: %{rpmversion}
Release: %{pkg_release}
# DO NOT CHANGE THE 'ExclusiveArch' LINE TO TEMPORARILY EXCLUDE AN ARCHITECTURE BUILD.
# SET %%nobuildarches (ABOVE) INSTEAD
%if 0%{?fedora}
ExclusiveArch: x86_64 s390x %{arm} aarch64 ppc64le
%else
ExclusiveArch: noarch i386 i686 x86_64 s390x %{arm} aarch64 ppc64le
%endif
ExclusiveOS: Linux
%ifnarch %{nobuildarches}
Requires: kernel-core-uname-r = %{KVERREL}%{?variant}
Requires: kernel-modules-uname-r = %{KVERREL}%{?variant}
%endif


#
# List the packages used during the kernel build
#
BuildRequires: kmod, patch, bash, tar, git-core
BuildRequires: bzip2, xz, findutils, gzip, m4, perl-interpreter, perl-Carp, perl-devel, perl-generators, make, diffutils, gawk
BuildRequires: gcc, binutils, redhat-rpm-config, hmaccalc, bison, flex
BuildRequires: net-tools, hostname, bc, elfutils-devel
%if 0%{?fedora}
BuildRequires: dwarves
%endif
# Used to mangle unversioned shebangs to be Python 3
BuildRequires: python3-devel
%if %{with_headers}
BuildRequires: rsync
%endif
%if %{with_doc}
BuildRequires: xmlto, asciidoc, python3-sphinx
%endif
%if %{with_sparse}
BuildRequires: sparse
%endif
%if %{with_selftests}
%if 0%{?fedora}
BuildRequires: clang llvm
%else
BuildRequires: llvm-toolset
%endif
%ifnarch %{arm}
BuildRequires: numactl-devel
%endif
BuildRequires: libcap-devel libcap-ng-devel rsync
%endif
BuildConflicts: rhbuildsys(DiskFree) < 500Mb
%if %{with_debuginfo}
BuildRequires: rpm-build, elfutils
BuildConflicts: rpm < 4.13.0.1-19
%if 0%{?fedora}
BuildConflicts: dwarves < 1.13
%endif
# Most of these should be enabled after more investigation
%undefine _include_minidebuginfo
%undefine _find_debuginfo_dwz_opts
%undefine _unique_build_ids
%undefine _unique_debug_names
%undefine _unique_debug_srcs
%undefine _debugsource_packages
%undefine _debuginfo_subpackages
%global _find_debuginfo_opts -r
%global _missing_build_ids_terminate_build 1
%global _no_recompute_build_ids 1
%endif
%if %{with_kabidwchk} || %{with_kabidw_base}
BuildRequires: kabi-dw
%endif

%if %{signkernel}%{signmodules}
BuildRequires: openssl openssl-devel
%if %{signkernel}
%ifarch x86_64 aarch64
BuildRequires: nss-tools
BuildRequires: pesign >= 0.10-4
%endif
%endif
%endif

%if %{with_cross}
BuildRequires: binutils-%{_build_arch}-linux-gnu, gcc-%{_build_arch}-linux-gnu
%define cross_opts CROSS_COMPILE=%{_build_arch}-linux-gnu-
%endif

Source0: https://www.kernel.org/pub/linux/kernel/v5.x/linux-%{kversion}.tar.xz

# Name of the packaged file containing signing key
%ifarch ppc64le
%define signing_key_filename kernel-signing-ppc.cer
%endif
%ifarch s390x
%define signing_key_filename kernel-signing-s390.cer
%endif

Source10: x509.genkey.rhel
Source11: x509.genkey.fedora
%if %{?released_kernel}

Source12: securebootca.cer
Source13: secureboot.cer

%define secureboot_ca %{SOURCE12}
%ifarch x86_64 aarch64
%define secureboot_key %{SOURCE13}
%define pesign_name redhatsecureboot301
%endif

%else # released_kernel

Source12: redhatsecurebootca2.cer
Source13: redhatsecureboot003.cer

%define secureboot_ca %{SOURCE12}
%define secureboot_key %{SOURCE13}
%define pesign_name redhatsecureboot003

%endif # released_kernel

Source15: mod-extra.list.rhel
Source16: mod-extra.list.fedora
Source17: mod-extra.sh
Source18: mod-sign.sh
Source19: mod-extra-blacklist.sh
Source79: parallel_xz.sh

Source80: filter-x86_64.sh.fedora
Source81: filter-armv7hl.sh.fedora
Source82: filter-i686.sh.fedora
Source83: filter-aarch64.sh.fedora
Source86: filter-ppc64le.sh.fedora
Source87: filter-s390x.sh.fedora
Source89: filter-modules.sh.fedora

Source90: filter-x86_64.sh.rhel
Source91: filter-armv7hl.sh.rhel
Source92: filter-i686.sh.rhel
Source93: filter-aarch64.sh.rhel
Source96: filter-ppc64le.sh.rhel
Source97: filter-s390x.sh.rhel
Source99: filter-modules.sh.rhel
%define modsign_cmd %{SOURCE18}

Source20: kernel-aarch64-rhel.config
Source21: kernel-aarch64-debug-rhel.config
Source30: kernel-ppc64le-rhel.config
Source31: kernel-ppc64le-debug-rhel.config
Source32: kernel-s390x-rhel.config
Source33: kernel-s390x-debug-rhel.config
Source34: kernel-s390x-zfcpdump-rhel.config
Source35: kernel-x86_64-rhel.config
Source36: kernel-x86_64-debug-rhel.config

Source37: kernel-aarch64-fedora.config
Source38: kernel-aarch64-debug-fedora.config
Source39: kernel-armv7hl-fedora.config
Source40: kernel-armv7hl-debug-fedora.config
Source41: kernel-armv7hl-lpae-fedora.config
Source42: kernel-armv7hl-lpae-debug-fedora.config
Source43: kernel-i686-fedora.config
Source44: kernel-i686-debug-fedora.config
Source45: kernel-ppc64le-fedora.config
Source46: kernel-ppc64le-debug-fedora.config
Source47: kernel-s390x-fedora.config
Source48: kernel-s390x-debug-fedora.config
Source49: kernel-x86_64-fedora.config
Source50: kernel-x86_64-debug-fedora.config



Source51: generate_all_configs.sh

Source52: process_configs.sh
Source53: generate_bls_conf.sh
Source56: update_scripts.sh

Source54: mod-internal.list
Source55: merge.pl

Source200: check-kabi

Source201: Module.kabi_aarch64
Source202: Module.kabi_ppc64le
Source203: Module.kabi_s390x
Source204: Module.kabi_x86_64

Source210: Module.kabi_dup_aarch64
Source211: Module.kabi_dup_ppc64le
Source212: Module.kabi_dup_s390x
Source213: Module.kabi_dup_x86_64

# Source300: kernel-abi-whitelists-%{rpmversion}-%{distro_build}.tar.bz2
# Source301: kernel-kabi-dw-%{rpmversion}-%{distro_build}.tar.bz2

# Sources for kernel-tools
Source2000: cpupower.service
Source2001: cpupower.config

## Patches needed for building this package

# Patch1: patch-%{rpmversion}-redhat.patch

# empty final patch to facilitate testing of kernel patches
# Patch999999: linux-kernel-test.patch

# This file is intentionally left empty in the stock kernel. Its a nicety
# added for those wanting to do custom rebuilds with altered config opts.
Source1000: kernel-local

# Here should be only the patches up to the upstream canonical Linus tree.

# For a stable release kernel
%if 0%{?stable_update}
%if 0%{?stable_base}
%define    stable_patch_00  patch-5.%{base_sublevel}.%{stable_base}.xz
Source5000: %{stable_patch_00}
%endif

# non-released_kernel case
# These are automagically defined by the rcrev and gitrev values set up
# near the top of this spec file.
%else
%if 0%{?rcrev}
Source5000: patch-5.%{upstream_sublevel}-rc%{rcrev}.xz
%if 0%{?gitrev}
Source5001: patch-5.%{upstream_sublevel}-rc%{rcrev}-git%{gitrev}.xz
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
Source5000: patch-5.%{base_sublevel}-git%{gitrev}.xz
%endif
%endif
%endif

## Patches needed for building this package

## compile fixes

%if !%{nopatches}

# Git trees.

# Standalone patches
# 100 - Generic long running patches

# 200 - x86 / secureboot

# bz 1497559 - Make kernel MODSIGN code not error on missing variables
Patch200: 0001-Make-get_cert_list-not-complain-about-cert-lists-tha.patch
Patch201: 0002-Add-efi_status_to_str-and-rework-efi_status_to_err.patch
Patch202: 0003-Make-get_cert_list-use-efi_status_to_str-to-print-er.patch

Patch204: efi-secureboot.patch

Patch205: lift-lockdown-sysrq.patch

# 300 - ARM patches
Patch300: arm64-Add-option-of-13-for-FORCE_MAX_ZONEORDER.patch

# RHBZ Bug 1576593 - work around while vendor investigates
Patch301: arm-make-highpte-not-expert.patch

# https://patchwork.kernel.org/patch/10351797/
Patch302: ACPI-scan-Fix-regression-related-to-X-Gene-UARTs.patch
# rhbz 1574718
Patch303: ACPI-irq-Workaround-firmware-issue-on-X-Gene-based-m400.patch

# http://www.spinics.net/lists/linux-tegra/msg26029.html
Patch304: usb-phy-tegra-Add-38.4MHz-clock-table-entry.patch
# http://patchwork.ozlabs.org/patch/587554/
Patch305: ARM-tegra-usb-no-reset.patch

# Tegra bits
Patch320: arm64-tegra-jetson-tx1-fixes.patch
# https://www.spinics.net/lists/linux-tegra/msg43110.html
Patch321: arm64-tegra-Jetson-TX2-Allow-bootloader-to-configure.patch
# https://patchwork.kernel.org/patch/11171225/
Patch322: mfd-max77620-Do-not-allocate-IRQs-upfront.patch
# https://patchwork.ozlabs.org/patch/1170631/
Patch323: gpio-max77620-Use-correct-unit-for-debounce-times.patch
# https://www.spinics.net/lists/linux-tegra/msg44216.html
Patch324: arm64-tegra186-enable-USB-on-Jetson-TX2.patch
# https://patchwork.kernel.org/patch/11224177/
Patch325: arm64-usb-host-xhci-tegra-set-MODULE_FIRMWARE-for-tegra186.patch

# 400 - IBM (ppc/s390x) patches

# 500 - Temp fixes/CVEs etc
Patch500: PATCH-v2-selinux-allow-labeling-before-policy-is-loaded.patch

# rhbz 1431375
Patch501: input-rmi4-remove-the-need-for-artifical-IRQ.patch

# gcc9 fixes
Patch502: 0001-Drop-that-for-now.patch

# https://bugzilla.redhat.com/show_bug.cgi?id=1701096
# Submitted upstream at https://lkml.org/lkml/2019/4/23/89
Patch503: KEYS-Make-use-of-platform-keyring-for-module-signature.patch

# it seems CONFIG_OPTIMIZE_INLINING has been forced now and is causing issues on ARMv7
# https://lore.kernel.org/patchwork/patch/1132459/
# https://lkml.org/lkml/2019/8/29/1772
Patch504: ARM-fix-__get_user_check-in-case-uaccess_-calls-are-not-inlined.patch

# CVE-2019-19043 rhbz 1774972 1774973
Patch512: net-next-v2-9-9-i40e-prevent-memory-leak-in-i40e_setup_macvlans.patch

# CVE-2019-19046 rhbz 1774988 1774989
Patch514: ipmi-Fix-memory-leak-in-__ipmi_bmc_register.patch

# CVE-2019-19064 rhbz 1775010 1775011
Patch515: spi-lpspi-fix-memory-leak-in-fsl_lpspi_probe.patch

# CVE-2019-19054 rhbz 1775063 1775117
Patch523: media-rc-prevent-memory-leak-in-cx23888_ir_probe.patch

# CVE-2019-14896 rhbz 1774875 1776143
# CVE-2019-14897 rhbz 1774879 1776146
Patch525: libertas-Fix-two-buffer-overflows-at-parsing-bss-descriptor.patch

# CVE-2019-18808 rhbz 1777418 1777421
Patch527: 0001-crypto-ccp-Release-all-allocated-memory-if-sha-type-.patch

# https://gitlab.freedesktop.org/drm/intel/issues/673
Patch531: drm-i915-gt-Detect-if-we-miss-WaIdleLiteRestore.patch

Patch900: 0001-Add-UKSM.patch
# END OF PATCH DEFINITIONS

%endif


%description
The kernel meta package

#
# This macro does requires, provides, conflicts, obsoletes for a kernel package.
#	%%kernel_reqprovconf <subpackage>
# It uses any kernel_<subpackage>_conflicts and kernel_<subpackage>_obsoletes
# macros defined above.
#
%define kernel_reqprovconf \
Provides: kernel = %{rpmversion}-%{pkg_release}\
Provides: kernel-%{_target_cpu} = %{rpmversion}-%{pkg_release}%{?1:+%{1}}\
Provides: kernel-drm-nouveau = 16\
Provides: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires(pre): %{kernel_prereq}\
Requires(pre): %{initrd_prereq}\
Requires(pre): linux-firmware >= 20150904-56.git6ebf5d57\
Requires(preun): systemd >= 200\
Conflicts: xfsprogs < 4.3.0-1\
Conflicts: xorg-x11-drv-vmmouse < 13.0.99\
%{expand:%%{?kernel%{?1:_%{1}}_conflicts:Conflicts: %%{kernel%{?1:_%{1}}_conflicts}}}\
%{expand:%%{?kernel%{?1:_%{1}}_obsoletes:Obsoletes: %%{kernel%{?1:_%{1}}_obsoletes}}}\
%{expand:%%{?kernel%{?1:_%{1}}_provides:Provides: %%{kernel%{?1:_%{1}}_provides}}}\
# We can't let RPM do the dependencies automatic because it'll then pick up\
# a correct but undesirable perl dependency from the module headers which\
# isn't required for the kernel proper to function\
AutoReq: no\
AutoProv: yes\
%{nil}


%package doc
Summary: Various documentation bits found in the kernel source
Group: Documentation
%description doc
This package contains documentation files from the kernel
source. Various bits of information about the Linux kernel and the
device drivers shipped with it are documented in these files.

You'll want to install this package if you need a reference to the
options that can be passed to Linux kernel modules at load time.


%package headers
Summary: Header files for the Linux kernel for use by glibc
Obsoletes: glibc-kernheaders < 3.0-46
Provides: glibc-kernheaders = 3.0-46
%if "0%{?variant}"
Obsoletes: kernel-headers < %{rpmversion}-%{pkg_release}
Provides: kernel-headers = %{rpmversion}-%{pkg_release}
%endif
%description headers
Kernel-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
glibc package.

%package cross-headers
Summary: Header files for the Linux kernel for use by cross-glibc
%description cross-headers
Kernel-cross-headers includes the C header files that specify the interface
between the Linux kernel and userspace libraries and programs.  The
header files define structures and constants that are needed for
building most standard programs and are also needed for rebuilding the
cross-glibc package.


%package debuginfo-common-%{_target_cpu}
Summary: Kernel source files used by %{name}-debuginfo packages
Provides: installonlypkg(kernel)
%description debuginfo-common-%{_target_cpu}
This package is required by %{name}-debuginfo subpackages.
It provides the kernel source files common to all builds.

%if %{with_selftests}
%package selftests-internal
Summary: Kernel samples and selftests
License: GPLv2
Requires: binutils, bpftool, iproute-tc, nmap-ncat
Requires: kernel-modules-internal = %{version}-%{release}
%description selftests-internal
Kernel sample programs and selftests.
%{nil}
# Note that this pattern only works right to match the .build-id
# symlinks because of the trailing nonmatching alternation and
# the leading .*, because of find-debuginfo.sh's buggy handling
# of matching the pattern against the symlinks file.
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*%%{_libexecdir}/(ksamples|kselftests)/.*|XXX' -o selftests-debuginfo.list}
%endif

%if %{with_gcov}
%package gcov
Summary: gcov graph and source files for coverage data collection.
%description gcov
kernel-gcov includes the gcov graph and source files for gcov coverage collection.
%endif

%package -n kernel-abi-whitelists
Summary: The Red Hat Enterprise Linux kernel ABI symbol whitelists
AutoReqProv: no
%description -n kernel-abi-whitelists
The kABI package contains information pertaining to the Red Hat Enterprise
Linux kernel ABI, including lists of kernel symbols that are needed by
external Linux kernel modules, and a yum plugin to aid enforcement.

%if %{with_kabidw_base}
%package kabidw-base
Summary: The baseline dataset for kABI verification using DWARF data
Group: System Environment/Kernel
AutoReqProv: no
%description kabidw-base
The kabidw-base package contains data describing the current ABI of the Red Hat
Enterprise Linux kernel, suitable for the kabi-dw tool.
%endif

#
# This macro creates a kernel-<subpackage>-debuginfo package.
#	%%kernel_debuginfo_package <subpackage>
#
# Explanation of the find_debuginfo_opts: We build multiple kernels (debug
# pae etc.) so the regex filters those kernels appropriately. We also
# have to package several binaries as part of kernel-devel but getting
# unique build-ids is tricky for these userspace binaries. We don't really
# care about debugging those so we just filter those out and remove it.
%define kernel_debuginfo_package() \
%package %{?1:%{1}-}debuginfo\
Summary: Debug information for package %{name}%{?1:-%{1}}\
Requires: %{name}-debuginfo-common-%{_target_cpu} = %{version}-%{release}\
Provides: %{name}%{?1:-%{1}}-debuginfo-%{_target_cpu} = %{version}-%{release}\
Provides: installonlypkg(kernel)\
AutoReqProv: no\
%description %{?1:%{1}-}debuginfo\
This package provides debug information for package %{name}%{?1:-%{1}}.\
This is required to use SystemTap with %{name}%{?1:-%{1}}-%{KVERREL}.\
%{expand:%%global _find_debuginfo_opts %{?_find_debuginfo_opts} -p '.*\/usr\/src\/kernels/.*|XXX' -o ignored-debuginfo.list -p '/.*/%%{KVERREL_RE}%{?1:[+]%{1}}/.*|/.*%%{KVERREL_RE}%{?1:\+%{1}}(\.debug)?' -o debuginfo%{?1}.list}\


%{nil}

#
# This macro creates a kernel-<subpackage>-devel package.
#	%%kernel_devel_package <subpackage> <pretty-name>
#
%define kernel_devel_package() \
%package %{?1:%{1}-}devel\
Summary: Development package for building kernel modules to match the %{?2:%{2} }kernel\
Provides: kernel%{?1:-%{1}}-devel-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-devel-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-devel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Provides: installonlypkg(kernel)\
AutoReqProv: no\
Requires(pre): findutils\
Requires: findutils\
Requires: perl-interpreter\
%description %{?1:%{1}-}devel\
This package provides kernel headers and makefiles sufficient to build modules\
against the %{?2:%{2} }kernel package.\
%{nil}

#
# kernel-<variant>-ipaclones-internal package
#
%define kernel_ipaclones_package() \
%package %{?1:%{1}-}ipaclones-internal\
Summary: *.ipa-clones files generated by -fdump-ipa-clones for kernel%{?1:-%{1}}\
Group: System Environment/Kernel\
AutoReqProv: no\
%description %{?1:%{1}-}ipaclones-internal\
This package provides *.ipa-clones files.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-internal package.
#	%%kernel_modules_internal_package <subpackage> <pretty-name>
#
%define kernel_modules_internal_package() \
%package %{?1:%{1}-}modules-internal\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Group: System Environment/Kernel\
Provides: kernel%{?1:-%{1}}-modules-internal-%{_target_cpu} = %{version}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-internal-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel%{?1:-%{1}}-modules-internal = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-internal-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-internal\
This package provides kernel modules for the %{?2:%{2} }kernel package for Red Hat internal usage.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules-extra package.
#	%%kernel_modules_extra_package <subpackage> <pretty-name>
#
%define kernel_modules_extra_package() \
%package %{?1:%{1}-}modules-extra\
Summary: Extra kernel modules to match the %{?2:%{2} }kernel\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}\
Provides: kernel%{?1:-%{1}}-modules-extra-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel%{?1:-%{1}}-modules-extra = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-extra-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules-extra\
This package provides less commonly used kernel modules for the %{?2:%{2} }kernel package.\
%{nil}

#
# This macro creates a kernel-<subpackage>-modules package.
#	%%kernel_modules_package <subpackage> <pretty-name>
#
%define kernel_modules_package() \
%package %{?1:%{1}-}modules\
Summary: kernel modules to match the %{?2:%{2}-}core kernel\
Provides: kernel%{?1:-%{1}}-modules-%{_target_cpu} = %{version}-%{release}\
Provides: kernel-modules-%{_target_cpu} = %{version}-%{release}%{?1:+%{1}}\
Provides: kernel-modules = %{version}-%{release}%{?1:+%{1}}\
Provides: installonlypkg(kernel-module)\
Provides: kernel%{?1:-%{1}}-modules-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Requires: kernel-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
AutoReq: no\
AutoProv: yes\
%description %{?1:%{1}-}modules\
This package provides commonly used kernel modules for the %{?2:%{2}-}core kernel package.\
%{nil}

#
# this macro creates a kernel-<subpackage> meta package.
#	%%kernel_meta_package <subpackage>
#
%define kernel_meta_package() \
%package %{1}\
summary: kernel meta-package for the %{1} kernel\
Requires: kernel-%{1}-core-uname-r = %{KVERREL}%{?variant}+%{1}\
Requires: kernel-%{1}-modules-uname-r = %{KVERREL}%{?variant}+%{1}\
Provides: installonlypkg(kernel)\
%description %{1}\
The meta-package for the %{1} kernel\
%{nil}

#
# This macro creates a kernel-<subpackage> and its -devel and -debuginfo too.
#	%%define variant_summary The Linux kernel compiled for <configuration>
#	%%kernel_variant_package [-n <pretty-name>] <subpackage>
#
%define kernel_variant_package(n:) \
%package %{?1:%{1}-}core\
Summary: %{variant_summary}\
Provides: kernel-%{?1:%{1}-}core-uname-r = %{KVERREL}%{?variant}%{?1:+%{1}}\
Provides: installonlypkg(kernel)\
%ifarch ppc64le\
Obsoletes: kernel-bootwrapper\
%endif\
%{expand:%%kernel_reqprovconf}\
%if %{?1:1} %{!?1:0} \
%{expand:%%kernel_meta_package %{?1:%{1}}}\
%endif\
%{expand:%%kernel_devel_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_extra_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_modules_internal_package %{?1:%{1}} %{!?{-n}:%{1}}%{?{-n}:%{-n*}}}\
%{expand:%%kernel_debuginfo_package %{?1:%{1}}}\
%{nil}

# Now, each variant package.

%if %{with_pae}
%define variant_summary The Linux kernel compiled for Cortex-A15
%kernel_variant_package lpae
%description lpae-core
This package includes a version of the Linux kernel with support for
Cortex-A15 devices with LPAE and HW virtualisation support
%endif

%if %{with_zfcpdump}
%define variant_summary The Linux kernel compiled for zfcpdump usage
%kernel_variant_package zfcpdump
%description zfcpdump-core
The kernel package contains the Linux kernel (vmlinuz) for use by the
zfcpdump infrastructure.
%endif

%define variant_summary The Linux kernel compiled with extra debugging enabled
%kernel_variant_package debug
%description debug-core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system:  memory allocation, process allocation, device
input and output, etc.

This variant of the kernel has numerous debugging options enabled.
It should only be installed when trying to gather additional information
on kernel bugs, as some of these options impact performance noticably.

# And finally the main -core package

%define variant_summary The Linux kernel
%kernel_variant_package
%description core
The kernel package contains the Linux kernel (vmlinuz), the core of any
Linux operating system.  The kernel handles the basic functions
of the operating system: memory allocation, process allocation, device
input and output, etc.

%if %{with_ipaclones}
%kernel_ipaclones_package
%endif

%prep
# do a few sanity-checks for --with *only builds
%if %{with_baseonly}
%if !%{with_up}%{with_pae}
echo "Cannot build --with baseonly, up build is disabled"
exit 1
%endif
%endif

%if "%{baserelease}" == "0"
echo "baserelease must be greater than zero"
exit 1
%endif

# more sanity checking; do it quietly
if [ "%{patches}" != "%%{patches}" ] ; then
  for patch in %{patches} ; do
    if [ ! -f $patch ] ; then
      echo "ERROR: Patch  ${patch##/*/}  listed in specfile but is missing"
      exit 1
    fi
  done
fi 2>/dev/null

patch_command='patch -p1 -F1 -s'
ApplyPatch()
{
  local patch=$1
  shift
  if [ ! -f $RPM_SOURCE_DIR/$patch ]; then
    exit 1
  fi
  if ! grep -E "^Patch[0-9]+: $patch\$" %{_specdir}/${RPM_PACKAGE_NAME%%%%%{?variant}}.spec ; then
    if [ "${patch:0:8}" != "patch-5." ] ; then
      echo "ERROR: Patch  $patch  not listed as a source patch in specfile"
      exit 1
    fi
  fi 2>/dev/null
  case "$patch" in
  *.bz2) bunzip2 < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *.gz)  gunzip  < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *.xz)  unxz    < "$RPM_SOURCE_DIR/$patch" | $patch_command ${1+"$@"} ;;
  *) $patch_command ${1+"$@"} < "$RPM_SOURCE_DIR/$patch" ;;
  esac
}

# don't apply patch if it's empty
ApplyOptionalPatch()
{
  local patch=$1
  shift
  if [ ! -f $RPM_SOURCE_DIR/$patch ]; then
    exit 1
  fi
  local C=$(wc -l $RPM_SOURCE_DIR/$patch | awk '{print $1}')
  if [ "$C" -gt 9 ]; then
    ApplyPatch $patch ${1+"$@"}
  fi
}

# First we unpack the kernel tarball.
# If this isn't the first make prep, we use links to the existing clean tarball
# which speeds things up quite a bit.

# Update to latest upstream.
%if 0%{?released_kernel}
%define vanillaversion 5.%{base_sublevel}
# non-released_kernel case
%else
%if 0%{?rcrev}
%define vanillaversion 5.%{upstream_sublevel}-rc%{rcrev}
%if 0%{?gitrev}
%define vanillaversion 5.%{upstream_sublevel}-rc%{rcrev}-git%{gitrev}
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
%define vanillaversion 5.%{base_sublevel}-git%{gitrev}
%else
%define vanillaversion 5.%{base_sublevel}
%endif
%endif
%endif

# %%{vanillaversion} : the full version name, e.g. 2.6.35-rc6-git3
# %%{kversion}       : the base version, e.g. 2.6.34

# Use kernel-%%{kversion}%%{?dist} as the top-level directory name
# so we can prep different trees within a single git directory.

# Build a list of the other top-level kernel tree directories.
# This will be used to hardlink identical vanilla subdirs.
sharedirs=$(find "$PWD" -maxdepth 1 -type d -name 'kernel-5.*' \
            | grep -x -v "$PWD"/kernel-%{kversion}%{?dist}) ||:

# Delete all old stale trees.
if [ -d kernel-%{kversion}%{?dist} ]; then
  cd kernel-%{kversion}%{?dist}
  for i in linux-*
  do
     if [ -d $i ]; then
       # Just in case we ctrl-c'd a prep already
       rm -rf deleteme.%{_target_cpu}
       # Move away the stale away, and delete in background.
       mv $i deleteme-$i
       rm -rf deleteme* &
     fi
  done
  cd ..
fi

# Generate new tree
if [ ! -d kernel-%{kversion}%{?dist}/vanilla-%{vanillaversion} ]; then

  if [ -d kernel-%{kversion}%{?dist}/vanilla-%{kversion} ]; then

    # The base vanilla version already exists.
    cd kernel-%{kversion}%{?dist}

    # Any vanilla-* directories other than the base one are stale.
    for dir in vanilla-*; do
      [ "$dir" = vanilla-%{kversion} ] || rm -rf $dir &
    done

  else

    rm -f pax_global_header
    # Look for an identical base vanilla dir that can be hardlinked.
    for sharedir in $sharedirs ; do
      if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{kversion} ]] ; then
        break
      fi
    done
    if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{kversion} ]] ; then
%setup -q -n kernel-%{kversion}%{?dist} -c -T
      cp -al $sharedir/vanilla-%{kversion} .
    else
%setup -q -n kernel-%{kversion}%{?dist} -c
      mv linux-%{kversion} vanilla-%{kversion}
    fi

  fi

%if "%{kversion}" != "%{vanillaversion}"

  for sharedir in $sharedirs ; do
    if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{vanillaversion} ]] ; then
      break
    fi
  done
  if [[ ! -z $sharedir  &&  -d $sharedir/vanilla-%{vanillaversion} ]] ; then

    cp -al $sharedir/vanilla-%{vanillaversion} .

  else

    # Need to apply patches to the base vanilla version.
    cp -al vanilla-%{kversion} vanilla-%{vanillaversion}
    cd vanilla-%{vanillaversion}

cp %{SOURCE12} .

# Update vanilla to the latest upstream.
# (non-released_kernel case only)
%if 0%{?rcrev}
    xzcat %{SOURCE5000} | patch -p1 -F1 -s
%if 0%{?gitrev}
    xzcat %{SOURCE5001} | patch -p1 -F1 -s
%endif
%else
# pre-{base_sublevel+1}-rc1 case
%if 0%{?gitrev}
    xzcat %{SOURCE5000} | patch -p1 -F1 -s
%endif
%endif
    git init
    git config user.email "kernel-team@fedoraproject.org"
    git config user.name "Fedora Kernel Team"
    git config gc.auto 0
    git add .
    git commit -a -q -m "baseline"

    cd ..

  fi

%endif

else

  # We already have all vanilla dirs, just change to the top-level directory.
  cd kernel-%{kversion}%{?dist}

fi

# Now build the fedora kernel tree.
cp -al vanilla-%{vanillaversion} linux-%{KVERREL}

cd linux-%{KVERREL}
if [ ! -d .git ]; then
    git init
    git config user.email "kernel-team@fedoraproject.org"
    git config user.name "Fedora Kernel Team"
    git config gc.auto 0
    git add .
    git commit -a -q -m "baseline"
fi


# released_kernel with possible stable updates
%if 0%{?stable_base}
# This is special because the kernel spec is hell and nothing is consistent
xzcat %{SOURCE5000} | patch -p1 -F1 -s
git commit -a -m "Stable update"
%endif

# Note: Even in the "nopatches" path some patches (build tweaks and compile
# fixes) will always get applied; see patch defition above for details

git am %{patches}

# END OF PATCH APPLICATIONS

# Any further pre-build tree manipulations happen here.

chmod +x scripts/checkpatch.pl
chmod +x tools/objtool/sync-check.sh
mv COPYING COPYING-%{version}

# This Prevents scripts/setlocalversion from mucking with our version numbers.
touch .scmversion

# Mangle /usr/bin/python shebangs to /usr/bin/python3
# Mangle all Python shebangs to be Python 3 explicitly
# -p preserves timestamps
# -n prevents creating ~backup files
# -i specifies the interpreter for the shebang
# This fixes errors such as
# *** ERROR: ambiguous python shebang in /usr/bin/kvm_stat: #!/usr/bin/python. Change it to python3 (or python2) explicitly.
# We patch all sources below for which we got a report/error.
pathfix.py -i "%{__python3} %{py3_shbang_opts}" -p -n \
	tools/kvm/kvm_stat/kvm_stat \
	scripts/show_delta \
	scripts/diffconfig \
	scripts/bloat-o-meter \
	tools/perf/tests/attr.py \
	tools/perf/scripts/python/stat-cpi.py \
	tools/perf/scripts/python/sched-migration.py \
	Documentation \
	scripts/gen_compile_commands.py

# only deal with configs if we are going to build for the arch
%ifnarch %nobuildarches

if [ -L configs ]; then
	rm -f configs
fi
# Deal with configs stuff
mkdir configs
cd configs

# Drop some necessary files from the source dir into the buildroot
cp $RPM_SOURCE_DIR/kernel-*.config .
cp %{SOURCE1000} .
cp %{SOURCE55} .
cp %{SOURCE51} .
VERSION=%{version} ./generate_all_configs.sh %{primary_target} %{debugbuildsenabled}


# Merge in any user-provided local config option changes
%ifnarch %nobuildarches
for i in %{all_arch_configs}
do
  mv $i $i.tmp
  ./merge.pl %{SOURCE1000} $i.tmp > $i
  rm $i.tmp
done
%endif

%if !%{debugbuildsenabled}
rm -f kernel-%{version}-*debug.config
%endif

# enable GCOV kernel config options if gcov is on
%if %{with_gcov}
for i in *.config
do
  sed -i 's/# CONFIG_GCOV_KERNEL is not set/CONFIG_GCOV_KERNEL=y\nCONFIG_GCOV_PROFILE_ALL=y\n/' $i
done
%endif

cp %{SOURCE52} .
OPTS=""
%if %{with_configchecks}
	OPTS="$OPTS -w -n -c"
%endif
./process_configs.sh $OPTS kernel %{rpmversion}

cp %{SOURCE56} .
RPM_SOURCE_DIR=$RPM_SOURCE_DIR ./update_scripts.sh %{primary_target}

# end of kernel config
%endif

cd ..
# # End of Configs stuff

# get rid of unwanted files resulting from patch fuzz
find . \( -name "*.orig" -o -name "*~" \) -delete >/dev/null

# remove unnecessary SCM files
find . -name .gitignore -delete >/dev/null

cd ..

###
### build
###
%build

%if %{with_sparse}
%define sparse_mflags	C=1
%endif

cp_vmlinux()
{
  eu-strip --remove-comment -o "$2" "$1"
}

# These are for host programs that get built as part of the kernel and
# are required to be packaged in kernel-devel for building external modules.
# Since they are userspace binaries, they are required to pickup the hardening
# flags defined in the macros. The --build-id=uuid is a trick to get around
# debuginfo limitations: Typically, find-debuginfo.sh will update the build
# id of all binaries to allow for parllel debuginfo installs. The kernel
# can't use this because it breaks debuginfo for the vDSO so we have to
# use a special mechanism for kernel and modules to be unique. Unfortunately,
# we still have userspace binaries which need unique debuginfo and because
# they come from the kernel package, we can't just use find-debuginfo.sh to
# rewrite only those binaries. The easiest option right now is just to have
# the build id be a uuid for the host programs.
#
# Note we need to disable these flags for cross builds because the flags
# from redhat-rpm-config assume that host == target so target arch
# flags cause issues with the host compiler.
%if !%{with_cross}
%define build_hostcflags %{?build_cflags} -fipa-pta -flto=4 -fno-common -fgraphite-identity -floop-nest-optimize -O3 -fuse-linker-plugin -fno-semantic-interposition -falign-functions=32
%define build_hostldflags %{?build_ldflags} -Wl,--build-id=uuid %{?build_hostcflags}
%endif

%define make make %{?cross_opts} %{?make_opts} HOSTCFLAGS="%{?build_hostcflags}" HOSTLDFLAGS="%{?build_hostldflags}"

BuildKernel() {
    MakeTarget=$1
    KernelImage=$2
    Flavour=$4
    DoVDSO=$3
    Flav=${Flavour:++${Flavour}}
    InstallName=${5:-vmlinuz}

    DoModules=1
    if [ "$Flavour" = "zfcpdump" ]; then
	    DoModules=0
    fi

    # Pick the right config file for the kernel we're building
    Config=kernel-%{version}-%{_target_cpu}${Flavour:+-${Flavour}}.config
    DevelDir=/usr/src/kernels/%{KVERREL}${Flav}

    # When the bootable image is just the ELF kernel, strip it.
    # We already copy the unstripped file into the debuginfo package.
    if [ "$KernelImage" = vmlinux ]; then
      CopyKernel=cp_vmlinux
    else
      CopyKernel=cp
    fi

    KernelVer=%{version}-%{release}.%{_target_cpu}${Flav}
    echo BUILDING A KERNEL FOR ${Flavour} %{_target_cpu}...

    %if 0%{?stable_update}
    # make sure SUBLEVEL is incremented on a stable release.  Sigh 3.x.
    perl -p -i -e "s/^SUBLEVEL.*/SUBLEVEL = %{?stablerev}/" Makefile
    %endif

    # make sure EXTRAVERSION says what we want it to say
    perl -p -i -e "s/^EXTRAVERSION.*/EXTRAVERSION = -%{release}.%{_target_cpu}${Flav}/" Makefile

    # if pre-rc1 devel kernel, must fix up PATCHLEVEL for our versioning scheme
    %if !0%{?rcrev}
    %if 0%{?gitrev}
    perl -p -i -e 's/^PATCHLEVEL.*/PATCHLEVEL = %{upstream_sublevel}/' Makefile
    %endif
    %endif

    # and now to start the build process

    %{make} %{?_smp_mflags} mrproper
    cp configs/$Config .config

    %if %{signkernel}%{signmodules}
    cp $RPM_SOURCE_DIR/x509.genkey certs/.
    %endif

    Arch=`head -1 .config | cut -b 3-`
    echo USING ARCH=$Arch

    KCFLAGS="%{?kcflags}"

    # add kpatch flags for base kernel
    if [ "$Flavour" == "" ]; then
        KCFLAGS="$KCFLAGS %{?kpatch_kcflags}"
    fi

    %{make} ARCH=$Arch olddefconfig >/dev/null

    # This ensures build-ids are unique to allow parallel debuginfo
    perl -p -i -e "s/^CONFIG_BUILD_SALT.*/CONFIG_BUILD_SALT=\"%{KVERREL}\"/" .config
    %{make} ARCH=$Arch KCFLAGS="$KCFLAGS" WITH_GCOV="%{?with_gcov}" %{?_smp_mflags} $MakeTarget %{?sparse_mflags} %{?kernel_mflags}
    if [ $DoModules -eq 1 ]; then
	%{make} ARCH=$Arch KCFLAGS="$KCFLAGS" WITH_GCOV="%{?with_gcov}" %{?_smp_mflags} modules %{?sparse_mflags} || exit 1
    fi

    mkdir -p $RPM_BUILD_ROOT/%{image_install_path}
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer
%if %{with_debuginfo}
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/%{image_install_path}
%endif

%ifarch %{arm} aarch64
    %{make} ARCH=$Arch dtbs INSTALL_DTBS_PATH=$RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer
    %{make} ARCH=$Arch dtbs_install INSTALL_DTBS_PATH=$RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer
    cp -r $RPM_BUILD_ROOT/%{image_install_path}/dtb-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/dtb
    find arch/$Arch/boot/dts -name '*.dtb' -type f -delete
%endif

    # Start installing the results
    install -m 644 .config $RPM_BUILD_ROOT/boot/config-$KernelVer
    install -m 644 .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/config
    install -m 644 System.map $RPM_BUILD_ROOT/boot/System.map-$KernelVer
    install -m 644 System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/System.map

    # We estimate the size of the initramfs because rpm needs to take this size
    # into consideration when performing disk space calculations. (See bz #530778)
    dd if=/dev/zero of=$RPM_BUILD_ROOT/boot/initramfs-$KernelVer.img bs=1M count=20

    if [ -f arch/$Arch/boot/zImage.stub ]; then
      cp arch/$Arch/boot/zImage.stub $RPM_BUILD_ROOT/%{image_install_path}/zImage.stub-$KernelVer || :
      cp arch/$Arch/boot/zImage.stub $RPM_BUILD_ROOT/lib/modules/$KernelVer/zImage.stub-$KernelVer || :
    fi

    %if %{signkernel}
    if [ "$KernelImage" = vmlinux ]; then
        # We can't strip and sign $KernelImage in place, because
        # we need to preserve original vmlinux for debuginfo.
        # Use a copy for signing.
        $CopyKernel $KernelImage $KernelImage.tosign
        KernelImage=$KernelImage.tosign
        CopyKernel=cp
    fi

    # Sign the image if we're using EFI
    # aarch64 kernels are gziped EFI images
    KernelExtension=${KernelImage##*.}
    if [ "$KernelExtension" == "gz" ]; then
        SignImage=${KernelImage%.*}
    else
        SignImage=$KernelImage
    fi

    %ifarch x86_64 aarch64
    %pesign -s -i $SignImage -o vmlinuz.signed -a %{secureboot_ca} -c %{secureboot_key} -n %{pesign_name}
    %endif
    %ifarch s390x ppc64le
    if [ -x /usr/bin/rpm-sign ]; then
	rpm-sign --key "%{pesign_name}" --lkmsign $SignImage --output vmlinuz.signed
    elif [ $DoModules -eq 1 ]; then
	chmod +x scripts/sign-file
	./scripts/sign-file -p sha256 certs/signing_key.pem certs/signing_key.x509 $SignImage vmlinuz.signed
    else
	mv $SignImage vmlinuz.signed
    fi
    %endif

    if [ ! -s vmlinuz.signed ]; then
        echo "pesigning failed"
        exit 1
    fi
    mv vmlinuz.signed $SignImage
    if [ "$KernelExtension" == "gz" ]; then
        gzip -f9 $SignImage
    fi
    %endif
    $CopyKernel $KernelImage \
                $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    chmod 755 $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    cp $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer $RPM_BUILD_ROOT/lib/modules/$KernelVer/$InstallName

    # hmac sign the kernel for FIPS
    echo "Creating hmac file: $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac"
    ls -l $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer
    sha512hmac $RPM_BUILD_ROOT/%{image_install_path}/$InstallName-$KernelVer | sed -e "s,$RPM_BUILD_ROOT,," > $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac;
    cp $RPM_BUILD_ROOT/%{image_install_path}/.vmlinuz-$KernelVer.hmac $RPM_BUILD_ROOT/lib/modules/$KernelVer/.vmlinuz.hmac

    if [ $DoModules -eq 1 ]; then
	# Override $(mod-fw) because we don't want it to install any firmware
	# we'll get it from the linux-firmware package and we don't want conflicts
	%{make} ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT %{?_smp_mflags} modules_install KERNELRELEASE=$KernelVer mod-fw=
    fi

%if %{with_gcov}
    # install gcov-needed files to $BUILDROOT/$BUILD/...:
    #   gcov_info->filename is absolute path
    #   gcno references to sources can use absolute paths (e.g. in out-of-tree builds)
    #   sysfs symlink targets (set up at compile time) use absolute paths to BUILD dir
    find . \( -name '*.gcno' -o -name '*.[chS]' \) -exec install -D '{}' "$RPM_BUILD_ROOT/$(pwd)/{}" \;
%endif

    # add an a noop %%defattr statement 'cause rpm doesn't like empty file list files
    echo '%%defattr(-,-,-)' > ../kernel${Flavour:+-${Flavour}}-ldsoconf.list
    if [ $DoVDSO -ne 0 ]; then
        %{make} ARCH=$Arch INSTALL_MOD_PATH=$RPM_BUILD_ROOT vdso_install KERNELRELEASE=$KernelVer
        if [ -s ldconfig-kernel.conf ]; then
             install -D -m 444 ldconfig-kernel.conf \
                $RPM_BUILD_ROOT/etc/ld.so.conf.d/kernel-$KernelVer.conf
	     echo /etc/ld.so.conf.d/kernel-$KernelVer.conf >> ../kernel${Flavour:+-${Flavour}}-ldsoconf.list
        fi

        rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/vdso/.build-id
    fi

    # And save the headers/makefiles etc for building modules against
    #
    # This all looks scary, but the end result is supposed to be:
    # * all arch relevant include/ files
    # * all Makefile/Kconfig files
    # * all script/ files

    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/source
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    (cd $RPM_BUILD_ROOT/lib/modules/$KernelVer ; ln -s build source)
    # dirs for additional modules per module-init-tools, kbuild/modules.txt
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/extra
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/internal
    mkdir -p $RPM_BUILD_ROOT/lib/modules/$KernelVer/updates
    # CONFIG_KERNEL_HEADER_TEST generates some extra files in the process of
    # testing so just delete
    find . -name *.h.s -delete
    # first copy everything
    cp --parents `find  -type f -name "Makefile*" -o -name "Kconfig*"` $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp Module.symvers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp System.map $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    if [ -s Module.markers ]; then
      cp Module.markers $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    fi

    # create the kABI metadata for use in packaging
    # NOTENOTE: the name symvers is used by the rpm backend
    # NOTENOTE: to discover and run the /usr/lib/rpm/fileattrs/kabi.attr
    # NOTENOTE: script which dynamically adds exported kernel symbol
    # NOTENOTE: checksums to the rpm metadata provides list.
    # NOTENOTE: if you change the symvers name, update the backend too
    echo "**** GENERATING kernel ABI metadata ****"
    gzip -c9 < Module.symvers > $RPM_BUILD_ROOT/boot/symvers-$KernelVer.gz
    cp $RPM_BUILD_ROOT/boot/symvers-$KernelVer.gz $RPM_BUILD_ROOT/lib/modules/$KernelVer/symvers.gz
%if %{with_kabichk}
    echo "**** kABI checking is enabled in kernel SPEC file. ****"
    chmod 0755 $RPM_SOURCE_DIR/check-kabi
    if [ -e $RPM_SOURCE_DIR/Module.kabi_%{_target_cpu}$Flavour ]; then
        cp $RPM_SOURCE_DIR/Module.kabi_%{_target_cpu}$Flavour $RPM_BUILD_ROOT/Module.kabi
        $RPM_SOURCE_DIR/check-kabi -k $RPM_BUILD_ROOT/Module.kabi -s Module.symvers || exit 1
        rm $RPM_BUILD_ROOT/Module.kabi # for now, don't keep it around.
    else
        echo "**** NOTE: Cannot find reference Module.kabi file. ****"
    fi
%endif

%if %{with_kabidupchk}
    echo "**** kABI DUP checking is enabled in kernel SPEC file. ****"
    if [ -e $RPM_SOURCE_DIR/Module.kabi_dup_%{_target_cpu}$Flavour ]; then
        cp $RPM_SOURCE_DIR/Module.kabi_dup_%{_target_cpu}$Flavour $RPM_BUILD_ROOT/Module.kabi
        $RPM_SOURCE_DIR/check-kabi -k $RPM_BUILD_ROOT/Module.kabi -s Module.symvers || exit 1
        rm $RPM_BUILD_ROOT/Module.kabi # for now, don't keep it around.
    else
        echo "**** NOTE: Cannot find DUP reference Module.kabi file. ****"
    fi
%endif

%if %{with_kabidw_base}
    # Don't build kabi base for debug kernels
    if [ "$Flavour" != "kdump" -a "$Flavour" != "debug" ]; then
        mkdir -p $RPM_BUILD_ROOT/kabi-dwarf
        tar xjvf %{SOURCE301} -C $RPM_BUILD_ROOT/kabi-dwarf

        mkdir -p $RPM_BUILD_ROOT/kabi-dwarf/whitelists
        tar xjvf %{SOURCE300} -C $RPM_BUILD_ROOT/kabi-dwarf/whitelists

        echo "**** GENERATING DWARF-based kABI baseline dataset ****"
        chmod 0755 $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh
        $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh generate \
            "$RPM_BUILD_ROOT/kabi-dwarf/whitelists/kabi-current/kabi_whitelist_%{_target_cpu}" \
            "$(pwd)" \
            "$RPM_BUILD_ROOT/kabidw-base/%{_target_cpu}${Flavour:+.${Flavour}}" || :

        rm -rf $RPM_BUILD_ROOT/kabi-dwarf
    fi
%endif

%if %{with_kabidwchk}
    if [ "$Flavour" != "kdump" ]; then
        mkdir -p $RPM_BUILD_ROOT/kabi-dwarf
        tar xjvf %{SOURCE301} -C $RPM_BUILD_ROOT/kabi-dwarf
        if [ -d "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Flavour:+.${Flavour}}" ]; then
            mkdir -p $RPM_BUILD_ROOT/kabi-dwarf/whitelists
            tar xjvf %{SOURCE300} -C $RPM_BUILD_ROOT/kabi-dwarf/whitelists

            echo "**** GENERATING DWARF-based kABI dataset ****"
            chmod 0755 $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh
            $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh generate \
                "$RPM_BUILD_ROOT/kabi-dwarf/whitelists/kabi-current/kabi_whitelist_%{_target_cpu}" \
                "$(pwd)" \
                "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Flavour:+.${Flavour}}.tmp" || :

            echo "**** kABI DWARF-based comparison report ****"
            $RPM_BUILD_ROOT/kabi-dwarf/run_kabi-dw.sh compare \
                "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Flavour:+.${Flavour}}" \
                "$RPM_BUILD_ROOT/kabi-dwarf/base/%{_target_cpu}${Flavour:+.${Flavour}}.tmp" || :
            echo "**** End of kABI DWARF-based comparison report ****"
        else
            echo "**** Baseline dataset for kABI DWARF-BASED comparison report not found ****"
        fi

        rm -rf $RPM_BUILD_ROOT/kabi-dwarf
    fi
%endif

    # then drop all but the needed Makefiles/Kconfig files
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
    cp .config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    cp -a scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build
    rm -rf $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/tracing
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/spdxcheck.py
    if [ -f tools/objtool/objtool ]; then
      cp -a tools/objtool/objtool $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/tools/objtool/ || :
    fi
    if [ -d arch/$Arch/scripts ]; then
      cp -a arch/$Arch/scripts $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch} || :
    fi
    if [ -f arch/$Arch/*lds ]; then
      cp -a arch/$Arch/*lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/arch/%{_arch}/ || :
    fi
    if [ -f arch/%{asmarch}/kernel/module.lds ]; then
      cp -a --parents arch/%{asmarch}/kernel/module.lds $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*.o
    rm -f $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/scripts/*/*.o
%ifarch ppc64le
    cp -a --parents arch/powerpc/lib/crtsavres.[So] $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
%endif
    if [ -d arch/%{asmarch}/include ]; then
      cp -a --parents arch/%{asmarch}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
%ifarch aarch64
    # arch/arm64/include/asm/xen references arch/arm
    cp -a --parents arch/arm/include/asm/xen $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    # arch/arm64/include/asm/opcodes.h references arch/arm
    cp -a --parents arch/arm/include/asm/opcodes.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
%endif
    # include the machine specific headers for ARM variants, if available.
%ifarch %{arm}
    if [ -d arch/%{asmarch}/mach-${Flavour}/include ]; then
      cp -a --parents arch/%{asmarch}/mach-${Flavour}/include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    fi
    # include a few files for 'make prepare'
    cp -a --parents arch/arm/tools/gen-mach-types $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/arm/tools/mach-types $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/

%endif
    cp -a include $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include
%ifarch i686 x86_64
    # files for 'make prepare' to succeed with kernel-devel
    cp -a --parents arch/x86/entry/syscalls/syscall_32.tbl $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/entry/syscalls/syscalltbl.sh $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/entry/syscalls/syscallhdr.sh $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/entry/syscalls/syscall_64.tbl $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs_32.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs_64.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs_common.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/tools/relocs.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents tools/include/tools/le_byteshift.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/purgatory.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/stack.S $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/setup-x86_64.S $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/purgatory/entry64.S $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/boot/string.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/boot/string.c $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
    cp -a --parents arch/x86/boot/ctype.h $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/
%endif
    # Make sure the Makefile and version.h have a matching timestamp so that
    # external modules can be built
    touch -r $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/Makefile $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/generated/uapi/linux/version.h

    # Copy .config to include/config/auto.conf so "make prepare" is unnecessary.
    cp $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/.config $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/include/config/auto.conf

%if %{with_debuginfo}
    eu-readelf -n vmlinux | grep "Build ID" | awk '{print $NF}' > vmlinux.id
    cp vmlinux.id $RPM_BUILD_ROOT/lib/modules/$KernelVer/build/vmlinux.id

    #
    # save the vmlinux file for kernel debugging into the kernel-debuginfo rpm
    #
    mkdir -p $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
    cp vmlinux $RPM_BUILD_ROOT%{debuginfodir}/lib/modules/$KernelVer
%endif

    find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name "*.ko" -type f >modnames

    # mark modules executable so that strip-to-file can strip them
    xargs --no-run-if-empty chmod u+x < modnames

    # Generate a list of modules for block and networking.

    grep -F /drivers/ modnames | xargs --no-run-if-empty nm -upA |
    sed -n 's,^.*/\([^/]*\.ko\):  *U \(.*\)$,\1 \2,p' > drivers.undef

    collect_modules_list()
    {
      sed -r -n -e "s/^([^ ]+) \\.?($2)\$/\\1/p" drivers.undef |
        LC_ALL=C sort -u > $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      if [ ! -z "$3" ]; then
        sed -r -e "/^($3)\$/d" -i $RPM_BUILD_ROOT/lib/modules/$KernelVer/modules.$1
      fi
    }

    collect_modules_list networking \
      'register_netdev|ieee80211_register_hw|usbnet_probe|phy_driver_register|rt(l_|2x00)(pci|usb)_probe|register_netdevice'
    collect_modules_list block \
      'ata_scsi_ioctl|scsi_add_host|scsi_add_host_with_dma|blk_alloc_queue|blk_init_queue|register_mtd_blktrans|scsi_esp_register|scsi_register_device_handler|blk_queue_physical_block_size' 'pktcdvd.ko|dm-mod.ko'
    collect_modules_list drm \
      'drm_open|drm_init'
    collect_modules_list modesetting \
      'drm_crtc_init'

    # detect missing or incorrect license tags
    ( find $RPM_BUILD_ROOT/lib/modules/$KernelVer -name '*.ko' | xargs /sbin/modinfo -l | \
        grep -E -v 'GPL( v2)?$|Dual BSD/GPL$|Dual MPL/GPL$|GPL and additional rights$' ) && exit 1

    # remove files that will be auto generated by depmod at rpm -i time
    pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
        rm -f modules.{alias*,builtin.bin,dep*,*map,symbols*,devname,softdep}
    popd

    # Call the modules-extra script to move things around
    %{SOURCE17} $RPM_BUILD_ROOT/lib/modules/$KernelVer $RPM_SOURCE_DIR/mod-extra.list
    # Blacklist net autoloadable modules in modules-extra
    %{SOURCE19} $RPM_BUILD_ROOT lib/modules/$KernelVer
    # Call the modules-extra script for internal modules
    %{SOURCE17} $RPM_BUILD_ROOT/lib/modules/$KernelVer %{SOURCE54} internal

    #
    # Generate the kernel-core and kernel-modules files lists
    #

    # Copy the System.map file for depmod to use, and create a backup of the
    # full module tree so we can restore it after we're done filtering
    cp System.map $RPM_BUILD_ROOT/.
    pushd $RPM_BUILD_ROOT
    mkdir restore
    cp -r lib/modules/$KernelVer/* restore/.

    # don't include anything going into k-m-e in the file lists
    rm -rf lib/modules/$KernelVer/{extra,internal}


    if [ $DoModules -eq 1 ]; then
	# Find all the module files and filter them out into the core and
	# modules lists.  This actually removes anything going into -modules
	# from the dir.
	find lib/modules/$KernelVer/kernel -name *.ko | sort -n > modules.list
	cp $RPM_SOURCE_DIR/filter-*.sh .
	./filter-modules.sh modules.list %{_target_cpu}
	rm filter-*.sh

	# Run depmod on the resulting module tree and make sure it isn't broken
	depmod -b . -aeF ./System.map $KernelVer &> depmod.out
	if [ -s depmod.out ]; then
	    echo "Depmod failure"
	    cat depmod.out
	    exit 1
	else
	    rm depmod.out
	fi
    else
	# Ensure important files/directories exist to let the packaging succeed
	echo '%%defattr(-,-,-)' > modules.list
	echo '%%defattr(-,-,-)' > k-d.list
	mkdir -p lib/modules/$KernelVer/kernel
	# Add files usually created by make modules, needed to prevent errors
	# thrown by depmod during package installation
	touch lib/modules/$KernelVer/modules.order
	touch lib/modules/$KernelVer/modules.builtin
    fi

    # remove files that will be auto generated by depmod at rpm -i time
    pushd $RPM_BUILD_ROOT/lib/modules/$KernelVer/
        rm -f modules.{alias*,builtin.bin,dep*,*map,symbols*,devname,softdep}
    popd

    # Go back and find all of the various directories in the tree.  We use this
    # for the dir lists in kernel-core
    find lib/modules/$KernelVer/kernel -mindepth 1 -type d | sort -n > module-dirs.list

    # Cleanup
    rm System.map
    cp -r restore/* lib/modules/$KernelVer/.
    rm -rf restore
    popd

    # Make sure the files lists start with absolute paths or rpmbuild fails.
    # Also add in the dir entries
    sed -e 's/^lib*/\/lib/' %{?zipsed} $RPM_BUILD_ROOT/k-d.list > ../kernel${Flavour:+-${Flavour}}-modules.list
    sed -e 's/^lib*/%dir \/lib/' %{?zipsed} $RPM_BUILD_ROOT/module-dirs.list > ../kernel${Flavour:+-${Flavour}}-core.list
    sed -e 's/^lib*/\/lib/' %{?zipsed} $RPM_BUILD_ROOT/modules.list >> ../kernel${Flavour:+-${Flavour}}-core.list

    # Cleanup
    rm -f $RPM_BUILD_ROOT/k-d.list
    rm -f $RPM_BUILD_ROOT/modules.list
    rm -f $RPM_BUILD_ROOT/module-dirs.list

%if %{signmodules}
    if [ $DoModules -eq 1 ]; then
	# Save the signing keys so we can sign the modules in __modsign_install_post
	cp certs/signing_key.pem certs/signing_key.pem.sign${Flav}
	cp certs/signing_key.x509 certs/signing_key.x509.sign${Flav}
    fi
%endif

    # Move the devel headers out of the root file system
    mkdir -p $RPM_BUILD_ROOT/usr/src/kernels
    mv $RPM_BUILD_ROOT/lib/modules/$KernelVer/build $RPM_BUILD_ROOT/$DevelDir

    # This is going to create a broken link during the build, but we don't use
    # it after this point.  We need the link to actually point to something
    # when kernel-devel is installed, and a relative link doesn't work across
    # the F17 UsrMove feature.
    ln -sf $DevelDir $RPM_BUILD_ROOT/lib/modules/$KernelVer/build

    # prune junk from kernel-devel
    find $RPM_BUILD_ROOT/usr/src/kernels -name ".*.cmd" -delete

    # build a BLS config for this kernel
    %{SOURCE53} "$KernelVer" "$RPM_BUILD_ROOT" "%{?variant}"

    # Red Hat UEFI Secure Boot CA cert, which can be used to authenticate the kernel
    mkdir -p $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer
    install -m 0644 %{secureboot_ca} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/kernel-signing-ca.cer
    %ifarch s390x ppc64le
    if [ $DoModules -eq 1 ]; then
	if [ -x /usr/bin/rpm-sign ]; then
	    install -m 0644 %{secureboot_key} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{signing_key_filename}
	else
	    install -m 0644 certs/signing_key.x509.sign${Flav} $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/kernel-signing-ca.cer
	    openssl x509 -in certs/signing_key.pem.sign${Flav} -outform der -out $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{signing_key_filename}
	    chmod 0644 $RPM_BUILD_ROOT%{_datadir}/doc/kernel-keys/$KernelVer/%{signing_key_filename}
	fi
    fi
    %endif

%if %{with_ipaclones}
    MAXPROCS=$(echo %{?_smp_mflags} | sed -n 's/-j\s*\([0-9]\+\)/\1/p')
    if [ -z "$MAXPROCS" ]; then
        MAXPROCS=1
    fi
    if [ "$Flavour" == "" ]; then
        mkdir -p $RPM_BUILD_ROOT/$DevelDir-ipaclones
        find . -name '*.ipa-clones' | xargs -i{} -r -n 1 -P $MAXPROCS install -m 644 -D "{}" "$RPM_BUILD_ROOT/$DevelDir-ipaclones/{}"
    fi
%endif

}

###
# DO it...
###

# prepare directories
rm -rf $RPM_BUILD_ROOT
mkdir -p $RPM_BUILD_ROOT/boot
mkdir -p $RPM_BUILD_ROOT%{_libexecdir}

cd linux-%{KVERREL}


%if %{with_debug}
BuildKernel %make_target %kernel_image %{_use_vdso} debug
%endif

%if %{with_zfcpdump}
BuildKernel %make_target %kernel_image %{_use_vdso} zfcpdump
%endif

%if %{with_pae}
BuildKernel %make_target %kernel_image %{use_vdso} lpae
%endif

%if %{with_up}
BuildKernel %make_target %kernel_image %{_use_vdso}
%endif

%if %{with_selftests}
%{make} -s ARCH=$Arch V=1 samples/bpf/
pushd tools/testing/selftests
# We need to install here because we need to call make with ARCH set which
# doesn't seem possible to do in the install section.
%{make} -s ARCH=$Arch V=1 TARGETS="bpf livepatch net" INSTALL_PATH=%{buildroot}%{_libexecdir}/kselftests install
popd
%endif

%if %{with_doc}
# Make the HTML pages.
make htmldocs || %{doc_build_fail}

# sometimes non-world-readable files sneak into the kernel source tree
chmod -R a=rX Documentation
find Documentation -type d | xargs chmod u+w
%endif

# In the modsign case, we do 3 things.  1) We check the "flavour" and hard
# code the value in the following invocations.  This is somewhat sub-optimal
# but we're doing this inside of an RPM macro and it isn't as easy as it
# could be because of that.  2) We restore the .tmp_versions/ directory from
# the one we saved off in BuildKernel above.  This is to make sure we're
# signing the modules we actually built/installed in that flavour.  3) We
# grab the arch and invoke mod-sign.sh command to actually sign the modules.
#
# We have to do all of those things _after_ find-debuginfo runs, otherwise
# that will strip the signature off of the modules.
#
# Don't sign modules for the zfcpdump flavour as it is monolithic.

%define __modsign_install_post \
  if [ "%{signmodules}" -eq "1" ]; then \
    if [ "%{with_pae}" -ne "0" ]; then \
       %{modsign_cmd} certs/signing_key.pem.sign+lpae certs/signing_key.x509.sign+lpae $RPM_BUILD_ROOT/lib/modules/%{KVERREL}+lpae/ \
    fi \
    if [ "%{with_debug}" -ne "0" ]; then \
      %{modsign_cmd} certs/signing_key.pem.sign+debug certs/signing_key.x509.sign+debug $RPM_BUILD_ROOT/lib/modules/%{KVERREL}+debug/ \
    fi \
    if [ "%{with_up}" -ne "0" ]; then \
      %{modsign_cmd} certs/signing_key.pem.sign certs/signing_key.x509.sign $RPM_BUILD_ROOT/lib/modules/%{KVERREL}/ \
    fi \
  fi \
  if [ "%{zipmodules}" -eq "1" ]; then \
    find $RPM_BUILD_ROOT/lib/modules/ -type f -name '*.ko' | %{SOURCE79} %{?_smp_mflags}; \
  fi \
%{nil}

###
### Special hacks for debuginfo subpackages.
###

# This macro is used by %%install, so we must redefine it before that.
%define debug_package %{nil}

%if %{with_debuginfo}

%ifnarch noarch
%global __debug_package 1
%files -f debugfiles.list debuginfo-common-%{_target_cpu}
%endif

%endif

# We don't want to package debuginfo for self-tests and samples but
# we have to delete them to avoid an error messages about unpackaged
# files.
# Delete the debuginfo for for kernel-devel files
%define __remove_unwanted_dbginfo_install_post \
  if [ "%{with_selftests}" -ne "0" ]; then \
    rm -rf $RPM_BUILD_ROOT/usr/lib/debug/usr/libexec/ksamples; \
    rm -rf $RPM_BUILD_ROOT/usr/lib/debug/usr/libexec/kselftests; \
  fi \
  rm -rf $RPM_BUILD_ROOT/usr/lib/debug/usr/src; \
%{nil}

#
# Disgusting hack alert! We need to ensure we sign modules *after* all
# invocations of strip occur, which is in __debug_install_post if
# find-debuginfo.sh runs, and __os_install_post if not.
#
%define __spec_install_post \
  %{?__debug_package:%{__debug_install_post}}\
  %{__arch_install_post}\
  %{__os_install_post}\
  %{__remove_unwanted_dbginfo_install_post}\
  %{__modsign_install_post}

###
### install
###

%install

cd linux-%{KVERREL}

%if %{with_doc}
docdir=$RPM_BUILD_ROOT%{_datadir}/doc/kernel-doc-%{rpmversion}

# copy the source over
mkdir -p $docdir
tar -h -f - --exclude=man --exclude='.*' -c Documentation | tar xf - -C $docdir

%endif

# We have to do the headers install before the tools install because the
# kernel headers_install will remove any header files in /usr/include that
# it doesn't install itself.

%if %{with_headers}
# Install kernel headers
make ARCH=%{hdrarch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr headers_install

find $RPM_BUILD_ROOT/usr/include \
     \( -name .install -o -name .check -o \
        -name ..install.cmd -o -name ..check.cmd \) -delete

%endif

%if %{with_cross_headers}
HDR_ARCH_LIST='arm arm64 powerpc s390 x86'
mkdir -p $RPM_BUILD_ROOT/usr/tmp-headers

for arch in $HDR_ARCH_LIST; do
	mkdir $RPM_BUILD_ROOT/usr/tmp-headers/arch-${arch}
	make ARCH=${arch} INSTALL_HDR_PATH=$RPM_BUILD_ROOT/usr/tmp-headers/arch-${arch} headers_install
done

find $RPM_BUILD_ROOT/usr/tmp-headers \
     \( -name .install -o -name .check -o \
        -name ..install.cmd -o -name ..check.cmd \) -delete

# Copy all the architectures we care about to their respective asm directories
for arch in $HDR_ARCH_LIST ; do
	mkdir -p $RPM_BUILD_ROOT/usr/${arch}-linux-gnu/include
	mv $RPM_BUILD_ROOT/usr/tmp-headers/arch-${arch}/include/* $RPM_BUILD_ROOT/usr/${arch}-linux-gnu/include/
done

rm -rf $RPM_BUILD_ROOT/usr/tmp-headers
%endif

%if %{with_kernel_abi_whitelists}
# kabi directory
INSTALL_KABI_PATH=$RPM_BUILD_ROOT/lib/modules/
mkdir -p $INSTALL_KABI_PATH
# install kabi releases directories
tar xjvf %{SOURCE300} -C $INSTALL_KABI_PATH
%endif

%if %{with_selftests}
pushd samples
install -d %{buildroot}%{_libexecdir}/ksamples
# install bpf samples
pushd bpf
install -d %{buildroot}%{_libexecdir}/ksamples/bpf
find -type f -executable -exec install -m755 {} %{buildroot}%{_libexecdir}/ksamples/bpf \;
install -m755 *.sh %{buildroot}%{_libexecdir}/ksamples/bpf
# test_lwt_bpf.sh compiles test_lwt_bpf.c when run; this works only from the
# kernel tree. Just remove it.
rm %{buildroot}%{_libexecdir}/ksamples/bpf/test_lwt_bpf.sh
install -m644 tcp_bpf.readme %{buildroot}%{_libexecdir}/ksamples/bpf
popd
# install pktgen samples
pushd pktgen
install -d %{buildroot}%{_libexecdir}/ksamples/pktgen
find . -type f -executable -exec install -m755 {} %{buildroot}%{_libexecdir}/ksamples/pktgen/{} \;
find . -type f ! -executable -exec install -m644 {} %{buildroot}%{_libexecdir}/ksamples/pktgen/{} \;
popd
popd
# install drivers/net/mlxsw selftests
pushd tools/testing/selftests/drivers/net/mlxsw
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/drivers/net/mlxsw/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/mlxsw/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/drivers/net/mlxsw/{} \;
popd
# install net/forwarding selftests
pushd tools/testing/selftests/net/forwarding
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/net/forwarding/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/net/forwarding/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/net/forwarding/{} \;
popd
# install tc-testing selftests
pushd tools/testing/selftests/tc-testing
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/tc-testing/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/tc-testing/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/tc-testing/{} \;
popd
# install livepatch selftests
pushd tools/testing/selftests/livepatch
find -type d -exec install -d %{buildroot}%{_libexecdir}/kselftests/livepatch/{} \;
find -type f -executable -exec install -D -m755 {} %{buildroot}%{_libexecdir}/kselftests/livepatch/{} \;
find -type f ! -executable -exec install -D -m644 {} %{buildroot}%{_libexecdir}/kselftests/livepatch/{} \;
popd
%endif

###
### clean
###

###
### scripts
###

#
# This macro defines a %%post script for a kernel*-devel package.
#	%%kernel_devel_post [<subpackage>]
# Note we don't run hardlink if ostree is in use, as ostree is
# a far more sophisticated hardlink implementation.
# https://github.com/projectatomic/rpm-ostree/commit/58a79056a889be8814aa51f507b2c7a4dccee526
#
%define kernel_devel_post() \
%{expand:%%post %{?1:%{1}-}devel}\
if [ -f /etc/sysconfig/kernel ]\
then\
    . /etc/sysconfig/kernel || exit $?\
fi\
if [ "$HARDLINK" != "no" -a -x /usr/sbin/hardlink -a ! -e /run/ostree-booted ] \
then\
    (cd /usr/src/kernels/%{KVERREL}%{?1:+%{1}} &&\
     /usr/bin/find . -type f | while read f; do\
       hardlink -c /usr/src/kernels/*%{?dist}.*/$f $f\
     done)\
fi\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-extra package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_extra_post [<subpackage>]
#
%define kernel_modules_extra_post() \
%{expand:%%post %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-extra}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules-internal package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_internal_post [<subpackage>]
#
%define kernel_modules_internal_post() \
%{expand:%%post %{?1:%{1}-}modules-internal}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules-internal}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

#
# This macro defines a %%post script for a kernel*-modules package.
# It also defines a %%postun script that does the same thing.
#	%%kernel_modules_post [<subpackage>]
#
%define kernel_modules_post() \
%{expand:%%post %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}\
%{expand:%%postun %{?1:%{1}-}modules}\
/sbin/depmod -a %{KVERREL}%{?1:+%{1}}\
%{nil}

# This macro defines a %%posttrans script for a kernel package.
#	%%kernel_variant_posttrans [<subpackage>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_posttrans() \
%{expand:%%posttrans %{?1:%{1}-}core}\
/bin/kernel-install add %{KVERREL}%{?1:+%{1}} /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz || exit $?\
%{nil}

#
# This macro defines a %%post script for a kernel package and its devel package.
#	%%kernel_variant_post [-v <subpackage>] [-r <replace>]
# More text can follow to go at the end of this variant's %%post.
#
%define kernel_variant_post(v:r:) \
%{expand:%%kernel_devel_post %{?-v*}}\
%{expand:%%kernel_modules_post %{?-v*}}\
%{expand:%%kernel_modules_extra_post %{?-v*}}\
%{expand:%%kernel_modules_internal_post %{?-v*}}\
%{expand:%%kernel_variant_posttrans %{?-v*}}\
%{expand:%%post %{?-v*:%{-v*}-}core}\
%{-r:\
if [ `uname -i` == "x86_64" -o `uname -i` == "i386" ] &&\
   [ -f /etc/sysconfig/kernel ]; then\
  /bin/sed -r -i -e 's/^DEFAULTKERNEL=%{-r*}$/DEFAULTKERNEL=kernel%{?-v:-%{-v*}}/' /etc/sysconfig/kernel || exit $?\
fi}\
%{nil}

#
# This macro defines a %%preun script for a kernel package.
#	%%kernel_variant_preun <subpackage>
#
%define kernel_variant_preun() \
%{expand:%%preun %{?1:%{1}-}core}\
/bin/kernel-install remove %{KVERREL}%{?1:+%{1}} /lib/modules/%{KVERREL}%{?1:+%{1}}/vmlinuz || exit $?\
%{nil}

%kernel_variant_preun
%kernel_variant_post -r kernel-smp

%if %{with_pae}
%kernel_variant_preun lpae
%kernel_variant_post -v lpae -r (kernel|kernel-smp)
%endif

%kernel_variant_preun debug
%kernel_variant_post -v debug

%if %{with_zfcpdump}
%kernel_variant_preun zfcpdump
%kernel_variant_post -v zfcpdump
%endif

if [ -x /sbin/ldconfig ]
then
    /sbin/ldconfig -X || exit $?
fi

###
### file lists
###

%if %{with_headers}
%files headers
/usr/include/*
%endif

%if %{with_cross_headers}
%files cross-headers
/usr/*-linux-gnu/include/*
%endif

%if %{with_kernel_abi_whitelists}
%files -n kernel-abi-whitelists
/lib/modules/kabi-*
%endif

%if %{with_kabidw_base}
%ifarch x86_64 s390x ppc64 ppc64le aarch64
%files kabidw-base
%defattr(-,root,root)
/kabidw-base/%{_target_cpu}/*
%endif
%endif

# only some architecture builds need kernel-doc
%if %{with_doc}
%files doc
%defattr(-,root,root)
%{_datadir}/doc/kernel-doc-%{rpmversion}/Documentation/*
%dir %{_datadir}/doc/kernel-doc-%{rpmversion}/Documentation
%dir %{_datadir}/doc/kernel-doc-%{rpmversion}
%endif

%if %{with_selftests}
%files selftests-internal
%{_libexecdir}/ksamples
%{_libexecdir}/kselftests
%endif

# empty meta-package
%ifnarch %nobuildarches noarch
%files
%endif

%if %{with_gcov}
%ifarch x86_64 s390x ppc64le aarch64
%files gcov
%{_builddir}
%endif
%endif

# This is %%{image_install_path} on an arch where that includes ELF files,
# or empty otherwise.
%define elf_image_install_path %{?kernel_image_elf:%{image_install_path}}

#
# This macro defines the %%files sections for a kernel package
# and its devel and debuginfo packages.
#	%%kernel_variant_files [-k vmlinux] <condition> <subpackage> <without_modules>
#
%define kernel_variant_files(k:) \
%if %{2}\
%{expand:%%files -f kernel-%{?3:%{3}-}core.list %{?1:-f kernel-%{?3:%{3}-}ldsoconf.list} %{?3:%{3}-}core}\
%{!?_licensedir:%global license %%doc}\
%license linux-%{KVERREL}/COPYING-%{version}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/%{?-k:%{-k*}}%{!?-k:vmlinuz}\
%ghost /%{image_install_path}/%{?-k:%{-k*}}%{!?-k:vmlinuz}-%{KVERREL}%{?3:+%{3}}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/.vmlinuz.hmac \
%ghost /%{image_install_path}/.vmlinuz-%{KVERREL}%{?3:+%{3}}.hmac \
%ifarch %{arm} aarch64\
/lib/modules/%{KVERREL}%{?3:+%{3}}/dtb \
%ghost /%{image_install_path}/dtb-%{KVERREL}%{?3:+%{3}} \
%endif\
%attr(600,root,root) /lib/modules/%{KVERREL}%{?3:+%{3}}/System.map\
%ghost /boot/System.map-%{KVERREL}%{?3:+%{3}}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/symvers.gz\
/lib/modules/%{KVERREL}%{?3:+%{3}}/config\
%ghost /boot/symvers-%{KVERREL}%{?3:+%{3}}.gz\
%ghost /boot/config-%{KVERREL}%{?3:+%{3}}\
%ghost /boot/initramfs-%{KVERREL}%{?3:+%{3}}.img\
%dir /lib/modules\
%dir /lib/modules/%{KVERREL}%{?3:+%{3}}\
%dir /lib/modules/%{KVERREL}%{?3:+%{3}}/kernel\
/lib/modules/%{KVERREL}%{?3:+%{3}}/build\
/lib/modules/%{KVERREL}%{?3:+%{3}}/source\
/lib/modules/%{KVERREL}%{?3:+%{3}}/updates\
/lib/modules/%{KVERREL}%{?3:+%{3}}/bls.conf\
%{_datadir}/doc/kernel-keys/%{KVERREL}%{?3:+%{3}}/kernel-signing-ca.cer\
%ifarch s390x ppc64le\
%if 0%{!?4:1}\
%{_datadir}/doc/kernel-keys/%{KVERREL}%{?3:+%{3}}/%{signing_key_filename} \
%endif\
%endif\
%if %{1}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/vdso\
%endif\
/lib/modules/%{KVERREL}%{?3:+%{3}}/modules.*\
%{expand:%%files -f kernel-%{?3:%{3}-}modules.list %{?3:%{3}-}modules}\
%{expand:%%files %{?3:%{3}-}devel}\
%defverify(not mtime)\
/usr/src/kernels/%{KVERREL}%{?3:+%{3}}\
%{expand:%%files %{?3:%{3}-}modules-extra}\
%config(noreplace) /etc/modprobe.d/*-blacklist.conf\
/lib/modules/%{KVERREL}%{?3:+%{3}}/extra\
%{expand:%%files %{?3:%{3}-}modules-internal}\
/lib/modules/%{KVERREL}%{?3:+%{3}}/internal\
%if %{with_debuginfo}\
%ifnarch noarch\
%{expand:%%files -f debuginfo%{?3}.list %{?3:%{3}-}debuginfo}\
%endif\
%endif\
%if %{?3:1} %{!?3:0}\
%{expand:%%files %{3}}\
%endif\
%endif\
%{nil}

%kernel_variant_files %{_use_vdso} %{with_up}
%kernel_variant_files %{_use_vdso} %{with_debug} debug
%kernel_variant_files %{use_vdso} %{with_pae} lpae
%kernel_variant_files %{_use_vdso} %{with_zfcpdump} zfcpdump 1

%define kernel_variant_ipaclones(k:) \
%if %{1}\
%if %{with_ipaclones}\
%{expand:%%files %{?2:%{2}-}ipaclones-internal}\
%defattr(-,root,root)\
%defverify(not mtime)\
/usr/src/kernels/%{KVERREL}%{?2:+%{2}}-ipaclones\
%endif\
%endif\
%{nil}

%kernel_variant_ipaclones %{with_up}

# plz don't put in a version string unless you're going to tag
# and build.
#
#
%changelog
* Tue Jan 21 2020 Piotr Rogowski <piotr.rogowski@creativestyle.pl> - 5.4.12-201
- Add UKSM

* Tue Jan 14 2020 Jeremy Cline <jcline@redhat.com> - 5.4.12-200
- Linux v5.4.12

* Mon Jan 13 2020 Justin M. Forbes <jforbes@fedoraproject.org> - 5.4.10-202
- Add Documentation back to kernel-devel as it has Kconfig now (rhbz 1789641)

* Mon Jan 13 2020 Peter Robinson <pbrobinson@gmail.com> - 5.4.11-200
- Linux v5.4.11

* Thu Jan 09 2020 Jeremy Cline <jcline@redhat.com> - 5.4.10-200
- Linux v5.4.10

* Mon Jan 06 2020 Laura Abbott <labbott@redhat.com>
- Fix for tpm usercopy (rhbz 1788653)

* Mon Jan 06 2020 Hans de Goede <hdegoede@redhat.com>
- Make the MFD Intel LPSS driver builtin, some devices require this to be
  available early during boot (rhbz#1787997)

* Mon Jan 06 2020 Jeremy Cline <jcline@redhat.com> - 5.4.8-200
- Linux v5.4.8
- Fix a firmware load issue on some Intel wireless cards (rhbz 1788150)

* Tue Dec 31 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.4.7-200
- Linux v5.4.7

* Mon Dec 23 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.4.6-300
- Linux v5.4.6
- Fix rhbz 1781288

* Thu Dec 19 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.4.5-300
- Linux v5.4.5 rebase

* Wed Dec 18 2019 Laura Abbott <labbott@redhat.com> - 5.3.18-300
- Linux v5.3.18

* Tue Dec 17 2019 Laura Abbott <labbott@redhat.com> - 5.3.17-300
- Linux v5.3.17

* Fri Dec 13 2019 Laura Abbott <labbott@redhat.com> - 5.3.16-300
- Linux v5.3.16

* Thu Dec 05 2019 Laura Abbott <labbott@redhat.com> - 5.3.15-300
- Linux v5.3.15

* Wed Dec 04 2019 Laura Abbott <labbott@redhat.com>
- Add powerpc virt fix (rhbz 1769600)

* Mon Dec 02 2019 Laura Abbott <labbott@redhat.com> - 5.3.14-300
- Linux v5.3.14

* Mon Dec 02 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Fix CVE-2019-18808 (rhbz 1777418 1777421)
- Fix CVE-2019-18809 (rhbz 1777449 1777451)
- Fix CVE-2019-18811 (rhbz 1777455 1777456)
- Fix CVE-2019-18812 (rhbz 1777458 1777459)
- Fix CVE-2019-16232 (rhbz 1760351 1760352)

* Tue Nov 26 2019 Justin M. Forbes <jforbes@fedoraproject.org> 
- Fix CVE-2019-19082 (rhbz 1776832 1776833)

* Mon Nov 25 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.3.13-300
- Fix CVE-2019-14895 (rhbz 1774870 1776139)
- Fix CVE-2019-14896 (rhbz 1774875 1776143)
- Fix CVE-2019-14897 (rhbz 1774879 1776146)
- Fix CVE-2019-14901 (rhbz 1773519 1776184)
- Fix CVE-2019-19078 (rhbz 1776354 1776353)

* Mon Nov 25 2019 Laura Abbott <labbott@redhat.com>
- Linux v5.3.13

* Fri Nov 22 2019 Justin M. Forbes <jforbes@fedoraproject.org> 
- Fix CVE-2019-19077 rhbz 1775724 1775725

* Thu Nov 21 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.3.12-300
- Fix CVE-2019-19074 (rhbz 1774933 1774934)
- Fix CVE-2019-19073 (rhbz 1774937 1774939)
- Fix CVE-2019-19072 (rhbz 1774946 1774947)
- Fix CVE-2019-19071 (rhbz 1774949 1774950)
- Fix CVE-2019-19070 (rhbz 1774957 1774958)
- Fix CVE-2019-19068 (rhbz 1774963 1774965)
- Fix CVE-2019-19043 (rhbz 1774972 1774973)
- Fix CVE-2019-19066 (rhbz 1774976 1774978)
- Fix CVE-2019-19046 (rhbz 1774988 1774989)
- Fix CVE-2019-19050 (rhbz 1774998 1775002)
- Fix CVE-2019-19062 (rhbz 1775021 1775023)
- Fix CVE-2019-19064 (rhbz 1775010 1775011)
- Fix CVE-2019-19063 (rhbz 1775015 1775016)
- Fix CVE-2019-19059 (rhbz 1775042 1775043)
- Fix CVE-2019-19058 (rhbz 1775047 1775048)
- Fix CVE-2019-19057 (rhbz 1775050 1775051)
- Fix CVE-2019-19053 (rhbz 1775956 1775110)
- Fix CVE-2019-19056 (rhbz 1775097 1775115)
- Fix CVE-2019-19055 (rhbz 1775074 1775116)
- Fix CVE-2019-19054 (rhbz 1775063 1775117)

* Thu Nov 21 2019 Laura Abbott <labbott@redhat.com>
- Linux v5.3.12

* Tue Nov 12 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.3.11-300
- Linux v5.3.11
- Fixes CVE-2019-11135	(rhbz 1753062 1771649)
- Fixes CVE-2018-12207	(rhbz 1646768 1771645)
- Fixes CVE-2019-0154	(rhbz 1724393 1771642)
- Fixes CVE-2019-0155	(rhbz 1724398 1771644)

* Mon Nov 11 2019 Laura Abbott <labbott@redhat.com> - 5.3.10-300
- Linux v5.3.10

* Thu Nov 07 2019 Jeremy Cline <jcline@redhat.com>
- Add support for a number of Macbook keyboards and touchpads (rhbz 1769465)

* Wed Nov 06 2019 Laura Abbott <labbott@redhat.com> - 5.3.9-300
- Linux v5.3.9

* Tue Oct 29 2019 Laura Abbott <labbott@redhat.com> - 5.3.8-300
- Linux v5.3.8

* Mon Oct 21 2019 Laura Abbott <labbott@redhat.com> - 5.3.7-301
- Fix CVE-2019-17666 (rhbz 1763692)

* Fri Oct 18 2019 Laura Abbott <labbott@redhat.com> - 5.3.7-300
- Linux v5.3.7

* Mon Oct 14 2019 Laura Abbott <labbott@redhat.com> - 5.3.6-300
- Linux v5.3.6

* Fri Oct 11 2019 Laura Abbott <labbott@redhat.com>
- Fix disappearing cursor issue (rhbz 1738614)

* Fri Oct 11 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Last iwlwifi fix for the recent firmware issues (rhbz 1733369)

* Tue Oct 08 2019 Laura Abbott <labbott@redhat.com> - 5.3.5-300
- Linux v5.3.5

* Mon Oct  7 2019 Laura Abbott <labbott@redhat.com>
- selinux fix (rhbz 1758597)

* Mon Oct  7 2019 Peter Robinson <pbrobinson@fedoraproject.org> 5.3.4-300
- Linux v5.3.4

* Sun Oct  6 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Fixes for RockPro64
- Fixes for Jetson-TX series devices

* Thu Oct 03 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Fix CVE-2019-17052 CVE-2019-17053 CVE-2019-17054 CVE-2019-17055 CVE-2019-17056
  (rhbz 1758239 1758240 1758242 1758243 1758245 1758246 1758248 1758249 1758256 1758257)

* Tue Oct 01 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.3.2-300
- Linux v5.3.2

* Mon Sep 30 2019 Laura Abbott <labbott@redhat.com>
- Fix for tpm crashes (rhbz 1752961)

* Mon Sep 23 2019 Peter Robinson <pbrobinson@fedoraproject.org> 5.3.1-300
- Upstream patch for iwlwifi 8000 series FW issues (rhbz: 1749949)

* Mon Sep 23 2019 Laura Abbott <labbott@redhat.com> - 5.3.1-100
- Linux v5.3.1

* Thu Sep 19 2019 Laura Abbott <labbott@redhat.com>
- Fix for dwc3 (rhbz 1753099)

* Mon Sep 16 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-1
- Linux v5.3

* Tue Sep 10 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc8.git0.1
- Linux v5.3-rc8

* Tue Sep 10 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Thu Sep 05 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc7.git1.1
- Linux v5.3-rc7-2-g3b47fd5ca9ea

* Thu Sep 05 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Tue Sep 03 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc7.git0.1
- Linux v5.3-rc7

* Tue Sep 03 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Thu Aug 29 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc6.git2.1
- Linux v5.3-rc6-119-g9cf6b756cdf2

* Wed Aug 28 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc6.git1.1
- Linux v5.3-rc6-115-g9e8312f5e160

* Wed Aug 28 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Aug 26 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc6.git0.1
- Linux v5.3-rc6

* Mon Aug 26 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Fri Aug 23 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc5.git2.1
- Linux v5.3-rc5-224-gdd469a456047

* Thu Aug 22 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc5.git1.1
- Linux v5.3-rc5-149-gbb7ba8069de9

* Thu Aug 22 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Aug 19 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc5.git0.1
- Linux v5.3-rc5

* Mon Aug 19 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Fri Aug 16 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc4.git3.1
- Linux v5.3-rc4-71-ga69e90512d9d

* Thu Aug 15 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc4.git2.1
- Linux v5.3-rc4-53-g41de59634046

* Wed Aug 14 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc4.git1.1
- Linux v5.3-rc4-4-gee1c7bd33e66

* Wed Aug 14 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Tue Aug 13 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc4.git0.1
- Linux v5.3-rc4

* Tue Aug 13 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Wed Aug 07 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc3.git1.1
- Linux v5.3-rc3-282-g33920f1ec5bf

* Wed Aug 07 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Aug 05 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc3.git0.1
- Linux v5.3-rc3

* Mon Aug 05 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Fri Aug 02 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc2.git4.1
- Linux v5.3-rc2-70-g1e78030e5e5b

* Thu Aug 01 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc2.git3.1
- Linux v5.3-rc2-60-g5c6207539aea
- Enable 8250 serial ports on powerpc

* Wed Jul 31 2019 Peter Robinson <pbrobinson@fedoraproject.org> 5.3.0-0.rc2.git2.2
- Enable IMA Appraisal

* Wed Jul 31 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc2.git2.1
- Linux v5.3-rc2-51-g4010b622f1d2

* Tue Jul 30 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc2.git1.1
- Linux v5.3-rc2-11-g2a11c76e5301

* Tue Jul 30 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Jul 29 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc2.git0.1
- Linux v5.3-rc2

* Mon Jul 29 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Fri Jul 26 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc1.git4.1
- Linux v5.3-rc1-96-g6789f873ed37
- Enable nvram driver (rhbz 1732612)

* Thu Jul 25 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc1.git3.1
- Linux v5.3-rc1-82-gbed38c3e2dca

* Wed Jul 24 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc1.git2.1
- Linux v5.3-rc1-59-gad5e427e0f6b

* Tue Jul 23 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc1.git1.1
- Linux v5.3-rc1-56-g7b5cf701ea9c

* Tue Jul 23 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Sun Jul 21 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc1.git0.1
- Linux v5.3-rc1

* Sun Jul 21 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Fri Jul 19 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- RHBZ Bug 1576593 - work around while vendor investigates

* Thu Jul 18 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git7.1
- Linux v5.2-11564-g22051d9c4a57

* Wed Jul 17 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git6.1
- Linux v5.2-11043-g0a8ad0ffa4d8

* Tue Jul 16 2019 Jeremy Cline <jcline@redhat.com>
- Fix a firmware crash in Intel 7000 and 8000 devices (rhbz 1716334)

* Tue Jul 16 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git5.1
- Linux v5.2-10808-g9637d517347e

* Fri Jul 12 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Turn off i686 builds

* Fri Jul 12 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git4.1
- Linux v5.2-7109-gd7d170a8e357

* Thu Jul 11 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git3.1
- Linux v5.2-3311-g5450e8a316a6

* Wed Jul 10 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git2.1
- Linux v5.2-3135-ge9a83bd23220

* Tue Jul 09 2019 Laura Abbott <labbott@redhat.com> - 5.3.0-0.rc0.git1.1
- Linux v5.2-915-g5ad18b2e60b7

* Tue Jul 09 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Jul 08 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-1
- Linux v5.2.0
- Disable debugging options.

* Wed Jul 03 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc7.git1.1
- Linux v5.2-rc7-8-geca94432934f
- Reenable debugging options.

* Mon Jul 01 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc7.git0.1
- Linux v5.2-rc7

* Mon Jul 01 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri Jun 28 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc6.git2.1
- Linux v5.2-rc6-93-g556e2f6020bf

* Tue Jun 25 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc6.git1.1
- Linux v5.2-rc6-15-g249155c20f9b
- Reenable debugging options.

* Mon Jun 24 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc6.git0.1
- Linux v5.2-rc6

* Mon Jun 24 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Sat Jun 22 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- QCom ACPI fixes

* Fri Jun 21 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc5.git4.1
- Linux v5.2-rc5-290-g4ae004a9bca8

* Thu Jun 20 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc5.git3.1
- Linux v5.2-rc5-239-g241e39004581

* Wed Jun 19 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc5.git2.1
- Linux v5.2-rc5-224-gbed3c0d84e7e

* Tue Jun 18 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc5.git1.1
- Linux v5.2-rc5-177-g29f785ff76b6
- Reenable debugging options.

* Mon Jun 17 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc5.git0.1
- Linux v5.2-rc5

* Mon Jun 17 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri Jun 14 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc4.git3.1
- Linux v5.2-rc4-129-g72a20cee5d99

* Fri Jun 14 2019 Jeremy Cline <jcline@redhat.com>
- Fix the long-standing bluetooth breakage

* Fri Jun 14 2019 Hans de Goede <hdegoede@redhat.com>
- Fix the LCD panel an Asus EeePC 1025C not lighting up (rhbz#1697069)
- Add small bugfix for new Logitech wireless keyboard support

* Thu Jun 13 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc4.git2.1
- Linux v5.2-rc4-45-gc11fb13a117e

* Wed Jun 12 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Raspberry Pi: move to cpufreq driver accepted for upstream \o/

* Wed Jun 12 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc4.git1.1
- Linux v5.2-rc4-20-gaa7235483a83
- Reenable debugging options.

* Mon Jun 10 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc4.git0.1
- Linux v5.2-rc4

* Mon Jun 10 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri Jun 07 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc3.git3.1
- Linux v5.2-rc3-77-g16d72dd4891f

* Thu Jun 06 2019 Jeremy Cline <jcline@redhat.com>
- Fix incorrect permission denied with lock down off (rhbz 1658675)

* Thu Jun 06 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc3.git2.1
- Linux v5.2-rc3-37-g156c05917e09

* Tue Jun 04 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc3.git1.1
- Linux v5.2-rc3-24-g788a024921c4
- Reenable debugging options.

* Mon Jun 03 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc3.git0.1
- Linux v5.2-rc3

* Mon Jun 03 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri May 31 2019 Peter Robinson <pbrobinson@fedoraproject.org> 5.2.0-0.rc2.git1.2
- Bump for ARMv7 fix

* Thu May 30 2019 Justin M. Forbes <jforbes@redhat.com> - 5.2.0-0.rc2.git1.1
- Linux v5.2-rc2-24-gbec7550cca10
- Reenable debugging options.

* Mon May 27 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc2.git0.1
- Linux v5.2-rc2

* Mon May 27 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri May 24 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc1.git3.1
- Linux v5.2-rc1-233-g0a72ef899014

* Wed May 22 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc1.git2.1
- Linux v5.2-rc1-165-g54dee406374c

* Tue May 21 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc1.git1.1
- Linux v5.2-rc1-129-g9c7db5004280

* Tue May 21 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc1.git0.2
- Reenable debugging options.

* Mon May 20 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc1.git0.1
- Disable debugging options.
- Linux V5.2-rc1

* Sun May 19 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Arm config updates

* Fri May 17 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git9.1
- Linux v5.1-12505-g0ef0fd351550

* Thu May 16 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git8.1
- Linux v5.1-12065-g8c05f3b965da

* Wed May 15 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git7.1
- Linux v5.1-10909-g2bbacd1a9278

* Tue May 14 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git6.1
- Linux v5.1-10326-g7e9890a3500d

* Mon May 13 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git5.1
- Linux v5.1-10135-ga13f0655503a

* Fri May 10 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git4.1
- Linux v5.1-9573-gb970afcfcabd

* Thu May 09 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git3.1
- Linux v5.1-8122-ga2d635decbfa

* Wed May 08 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git2.1
- Linux v5.1-5445-g80f232121b69

* Tue May 07 2019 Justin M. Forbes <jforbes@fedoraproject.org> - 5.2.0-0.rc0.git1.1
- Linux v5.1-1199-g71ae5fc87c34
- Reenable debugging options.

* Mon May  6 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable Arm STM32MP1

* Mon May 06 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-1
- Linux v5.1

* Fri May 03 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc7.git4.1
- Linux v5.1-rc7-131-gea9866793d1e

* Thu May 02 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc7.git3.1
- Linux v5.1-rc7-29-g600d7258316d

* Wed May 01 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc7.git2.1
- Linux v5.1-rc7-16-gf2bc9c908dfe

* Tue Apr 30 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc7.git1.1
- Linux v5.1-rc7-5-g83a50840e72a

* Tue Apr 30 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Tue Apr 30 2019 Hans de Goede <hdegoede@redhat.com>
- Fix wifi on various ideapad models not working (rhbz#1703338)

* Mon Apr 29 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc7.git0.1
- Linux v5.1-rc7

* Mon Apr 29 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Apr 26 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc6.git4.1
- Linux v5.1-rc6-72-g8113a85f8720

* Thu Apr 25 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc6.git3.1
- Linux v5.1-rc6-64-gcd8dead0c394

* Thu Apr 25 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Fix CVE-2019-3900 (rhbz 1698757 1702940)

* Wed Apr 24 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc6.git2.1
- Linux v5.1-rc6-15-gba25b50d582f

* Tue Apr 23 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc6.git1.1
- Linux v5.1-rc6-4-g7142eaa58b49

* Tue Apr 23 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Tue Apr 23 2019 Jeremy Cline <jcline@redhat.com>
- Allow modules signed by keys in the platform keyring (rbhz 1701096)

* Mon Apr 22 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc6.git0.1
- Linux v5.1-rc6

* Mon Apr 22 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Wed Apr 17 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc5.git2.1
- Linux v5.1-rc5-36-g444fe9913539

* Tue Apr 16 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc5.git1.1
- Linux v5.1-rc5-10-g618d919cae2f

* Tue Apr 16 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Mon Apr 15 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc5.git0.1
- Linux v5.1-rc5

* Mon Apr 15 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Apr 12 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc4.git4.1
- Linux v5.1-rc4-184-g8ee15f324866

* Thu Apr 11 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc4.git3.1
- Linux v5.1-rc4-58-g582549e3fbe1

* Wed Apr 10 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc4.git2.1
- Linux v5.1-rc4-43-g771acc7e4a6e

* Tue Apr 09 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc4.git1.1
- Linux v5.1-rc4-34-g869e3305f23d

* Tue Apr 09 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Mon Apr 08 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc4.git0.1
- Linux v5.1-rc4

* Mon Apr 08 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Apr 05 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc3.git3.1
- Linux v5.1-rc3-206-gea2cec24c8d4

* Wed Apr 03 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc3.git2.1
- Linux v5.1-rc3-35-g8ed86627f715

* Tue Apr 02 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc3.git1.1
- Linux v5.1-rc3-14-g5e7a8ca31926

* Tue Apr 02 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Mon Apr 01 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc3.git0.1
- Linux v5.1-rc3

* Mon Apr 01 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Mar 29 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc2.git4.1
- Linux v5.1-rc2-247-g9936328b41ce
- Pick up a mm fix causing hangs (rhbz 1693525)

* Thu Mar 28 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc2.git3.1
- Linux v5.1-rc2-243-g8c7ae38d1ce1

* Wed Mar 27 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc2.git2.1
- Linux v5.1-rc2-24-g14c741de9386

* Wed Mar 27 2019 Jeremy Cline <jeremy@jcline.org>
- Build iptable_filter as module

* Tue Mar 26 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc2.git1.1
- Linux v5.1-rc2-16-g65ae689329c5

* Tue Mar 26 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Tue Mar 26 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Initial NXP i.MX8 enablement

* Mon Mar 25 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc2.git0.1
- Linux v5.1-rc2

* Mon Mar 25 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Sat Mar 23 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Fixes for Tegra Jetson TX series
- Initial support for NVIDIA Jetson Nano

* Fri Mar 22 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc1.git2.1
- Linux v5.1-rc1-66-gfd1f297b794c

* Wed Mar 20 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc1.git1.1
- Linux v5.1-rc1-15-gbabf09c3837f
- Reenable debugging options.

* Wed Mar 20 2019 Hans de Goede <hdegoede@redhat.com>
- Make the mainline vboxguest drv feature set match VirtualBox 6.0.x (#1689750)

* Mon Mar 18 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc1.git0.1
- Linux v5.1-rc1

* Mon Mar 18 2019 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Sun Mar 17 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Updates for Arm

* Fri Mar 15 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git9.1
- Linux v5.0-11520-gf261c4e529da

* Thu Mar 14 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git8.1
- Linux v5.0-11139-gfa3d493f7a57

* Wed Mar 13 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git7.1
- Linux v5.0-11053-gebc551f2b8f9

* Tue Mar 12 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git6.1
- Linux v5.0-10742-gea295481b6e3

* Tue Mar 12 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Arm config updates and fixes

* Mon Mar 11 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git5.1
- Linux v5.0-10360-g12ad143e1b80

* Fri Mar 08 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git4.1
- Linux v5.0-7001-g610cd4eadec4

* Thu Mar 07 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git3.1
- Linux v5.0-6399-gf90d64483ebd

* Wed Mar 06 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git2.1
- Linux v5.0-3452-g3717f613f48d

* Tue Mar 05 2019 Jeremy Cline <jcline@redhat.com> - 5.1.0-0.rc0.git1.1
- Linux v5.0-510-gcd2a3bf02625

* Tue Mar 05 2019 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Mon Mar 04 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-1
- Linux v5.0.0

* Tue Feb 26 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc8.git1.1
- Linux v5.0-rc8-3-g7d762d69145a

* Tue Feb 26 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Feb 25 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc8.git0.1
- Linux v5.0-rc8
- Disable debugging options.

* Fri Feb 22 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc7.git3.1
- Linux v5.0-rc7-118-g8a61716ff2ab

* Wed Feb 20 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Improvements to 96boards Rock960

* Wed Feb 20 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc7.git2.1
- Linux v5.0-rc7-85-g2137397c92ae

* Tue Feb 19 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc7.git1.1
- Linux v5.0-rc7-11-gb5372fe5dc84

* Tue Feb 19 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Feb 18 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc7.git0.1
- Linux v5.0-rc7
- Disable debugging options.

* Wed Feb 13 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc6.git1.1
- Linux v5.0-rc6-42-g1f947a7a011f

* Wed Feb 13 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Wed Feb 13 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Wed Feb 13 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable NXP Freescale Layerscape platform

* Mon Feb 11 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc6.git0.1
- Linux v5.0-rc6
- Disable debugging options.
- Tweaks to gcc9 fixes

* Mon Feb 04 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc5.git0.1
- Linux v5.0-rc5
- Disable debugging options.

* Fri Feb 01 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc4.git3.1
- Linux v5.0-rc4-106-g5b4746a03199

* Thu Jan 31 2019 Hans de Goede <hdegoede@redhat.com>
- Add patches from -next to enable i915.fastboot by default on Skylake+ for
  https://fedoraproject.org/wiki/Changes/FlickerFreeBoot

* Wed Jan 30 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc4.git2.1
- Linux v5.0-rc4-59-g62967898789d

* Tue Jan 29 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc4.git1.1
- Linux v5.0-rc4-1-g4aa9fc2a435a

* Tue Jan 29 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Jan 28 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc4.git0.1
- Linux v5.0-rc4
- Disable debugging options.

* Wed Jan 23 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc3.git1.1
- Linux v5.0-rc3-53-g333478a7eb21

* Wed Jan 23 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Jan 21 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc3.git0.1
- Linux v5.0-rc3
- Disable debugging options.

* Fri Jan 18 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc2.git4.1
- Linux v5.0-rc2-211-gd7393226d15a

* Thu Jan 17 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc2.git3.1
- Linux v5.0-rc2-145-g7fbfee7c80de

* Wed Jan 16 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc2.git2.1
- Linux v5.0-rc2-141-g47bfa6d9dc8c

* Tue Jan 15 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc2.git1.1
- Linux v5.0-rc2-36-gfe76fc6aaf53

* Tue Jan 15 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Jan 14 2019 Laura Abbott <labbott@redhat.com>
- Enable CONFIG_GPIO_LEDS and CONFIG_GPIO_PCA953X  (rhbz 1601623)

* Mon Jan 14 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc2.git0.1
- Linux v5.0-rc2

* Mon Jan 14 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Sun Jan 13 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Raspberry Pi updates
- Update AllWinner A64 timer errata workaround

* Fri Jan 11 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc1.git4.1
- Linux v5.0-rc1-43-g1bdbe2274920

* Thu Jan 10 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc1.git3.1
- Linux v5.0-rc1-26-g70c25259537c

* Wed Jan 09 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc1.git2.1
- Linux v5.0-rc1-24-g4064e47c8281

* Wed Jan 09 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Fix CVE-2019-3701 (rhbz 1663729 1663730)

* Tue Jan 08 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc1.git1.1
- Linux v5.0-rc1-2-g7b5585136713

* Tue Jan 08 2019 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Jan 07 2019 Justin M. Forbes <jforbes@fedoraproject.org>
- Updates for secure boot

* Mon Jan 07 2019 Laura Abbott <labbott@redhat.com> - 5.0.0-0.rc1.git0.1
- Linux v5.0-rc1

* Mon Jan 07 2019 Laura Abbott <labbott@redhat.com>
- Disable debugging options.

* Fri Jan 04 2019 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git7.1
- Linux v4.20-10979-g96d4f267e40f

* Fri Jan  4 2019 Peter Robinson <pbrobinson@fedoraproject.org>
- Updates for Arm plaforms
- IoT related updates

* Thu Jan 03 2019 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git6.1
- Linux v4.20-10911-g645ff1e8e704

* Wed Jan 02 2019 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git5.1
- Linux v4.20-10595-g8e143b90e4d4

* Mon Dec 31 2018 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git4.1
- Linux v4.20-9221-gf12e840c819b

* Sun Dec 30 2018 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git3.1
- Linux v4.20-9163-g195303136f19

* Fri Dec 28 2018 Laura Abbott <labbott@redhat.com>
- Enable CONFIG_BPF_LIRC_MODE2 (rhbz 1628151)
- Enable CONFIG_NET_SCH_CAKE (rhbz 1655155)

* Fri Dec 28 2018 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git2.1
- Linux v4.20-6428-g00c569b567c7

* Thu Dec 27 2018 Hans de Goede <hdegoede@redhat.com>
- Set CONFIG_REALTEK_PHY=y to workaround realtek ethernet issues (rhbz 1650984)

* Wed Dec 26 2018 Laura Abbott <labbott@redhat.com> - 4.21.0-0.rc0.git1.1
- Linux v4.20-3117-ga5f2bd479f58

* Wed Dec 26 2018 Laura Abbott <labbott@redhat.com>
- Reenable debugging options.

* Mon Dec 24 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-1
- Linux v4.20.0

* Mon Dec 24 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Another fix for issue affecting Raspberry Pi 3-series WiFi (rhbz 1652093)

* Fri Dec 21 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc7.git3.1
- Linux v4.20-rc7-214-g9097a058d49e

* Thu Dec 20 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc7.git2.1
- Linux v4.20-rc7-202-g1d51b4b1d3f2

* Wed Dec 19 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Initial support for Raspberry Pi model 3A+
- Stability fixes for Raspberry Pi MMC (sdcard) driver

* Tue Dec 18 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc7.git1.1
- Linux v4.20-rc7-6-gddfbab46539f
- Reenable debugging options.

* Mon Dec 17 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc7.git0.1
- Linux v4.20-rc7

* Mon Dec 17 2018 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri Dec 14 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Enhancements for Raspberrp Pi Camera

* Thu Dec 13 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc6.git2.1
- Linux v4.20-rc6-82-g65e08c5e8631

* Wed Dec 12 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc6.git1.2
- Reenable debugging options.

* Tue Dec 11 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc6.git1.1
- Linux v4.20-rc6-25-gf5d582777bcb

* Tue Dec 11 2018 Hans de Goede <hdegoede@redhat.com>
- Really fix non functional hotkeys on Asus FX503VD (#1645070)

* Mon Dec 10 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc6.git0.1
- Linux v4.20-rc6

* Mon Dec 10 2018 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri Dec 07 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc5.git3.1
- Linux v4.20-rc5-86-gb72f711a4efa

* Wed Dec 05 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc5.git2.1
- Linux v4.20-rc5-44-gd08970904582

* Wed Dec 05 2018 Jeremy Cline <jeremy@jcline.org>
- Fix corruption bug in direct dispatch for blk-mq

* Tue Dec 04 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc5.git1.1
- Linux v4.20-rc5-21-g0072a0c14d5b
- Reenable debugging options.

* Mon Dec 03 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc5.git0.1
- Linux v4.20-rc5

* Mon Dec 03 2018 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Mon Dec  3 2018 Hans de Goede <hdegoede@redhat.com>
- Fix non functional hotkeys on Asus FX503VD (#1645070)

* Fri Nov 30 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc4.git2.1
- Linux v4.20-rc4-156-g94f371cb7394

* Wed Nov 28 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc4.git1.1
- Linux v4.20-rc4-35-g121b018f8c74
- Reenable debugging options.

* Mon Nov 26 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc4.git0.1
- Linux v4.20-rc4
- Disable debugging options.

* Tue Nov 20 2018 Jeremy Cline <jcline@redhat.com> - 4.20.0-0.rc3.git1.1
- Linux v4.20-rc3-83-g06e68fed3282

* Tue Nov 20 2018 Jeremy Cline <jcline@redhat.com>
- Reenable debugging options.

* Tue Nov 20 2018 Hans de Goede <hdegoede@redhat.com>
- Turn on CONFIG_PINCTRL_GEMINILAKE on x86_64 (rhbz#1639155)
- Add a patch fixing touchscreens on HP AMD based laptops (rhbz#1644013)
- Add a patch fixing KIOX010A accelerometers (rhbz#1526312)

* Mon Nov 19 2018 Jeremy Cline <jcline@redhat.com> - 4.20.0-0.rc3.git0.1
- Linux v4.20-rc3

* Mon Nov 19 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Sat Nov 17 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Fix WiFi on Raspberry Pi 3 on aarch64 (rhbz 1649344)
- Fixes for Raspberry Pi hwmon driver and firmware interface

* Fri Nov 16 2018 Hans de Goede <hdegoede@redhat.com>
- Enable a few modules needed for accelerometer and other sensor support
  on some HP X2 2-in-1s

* Thu Nov 15 2018 Justin M. Forbes <jforbes@redhat.com> - 4.20.0-0.rc2.git2.1
- Linux v4.20-rc2-52-g5929a1f0ff30

* Wed Nov 14 2018 Justin M. Forbes <jforbes@redhat.com> - 4.20.0-0.rc2.git1.1
- Linux v4.20-rc2-37-g3472f66013d1
- Reenable debugging options.

* Mon Nov 12 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Further updates for ARM
- More Qualcomm SD845 enablement
- FPGA Device Feature List (DFL) support
- Minor cleanups

* Sun Nov 11 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc2.git0.1
- Linux v4.20-rc2
- Disable debugging options.

* Fri Nov 09 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc1.git4.1
- Linux v4.20-rc1-145-gaa4330e15c26

* Thu Nov  8 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Initial Qualcomm SD845 enablement

* Thu Nov 08 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc1.git3.1
- Linux v4.20-rc1-98-gb00d209241ff

* Wed Nov 07 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc1.git2.1
- Linux v4.20-rc1-87-g85758777c2a2

* Wed Nov  7 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Initial Arm config updates for 4.20

* Tue Nov 06 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc1.git1.1
- Linux v4.20-rc1-62-g8053e5b93eca
- Reenable debugging options.

* Mon Nov 05 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc1.git0.1
- Linux v4.20-rc1

* Mon Nov 05 2018 Justin M. Forbes <jforbes@fedoraproject.org>
- Disable debugging options.

* Fri Nov 02 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git9.1
- Linux v4.19-12532-g8adcc59974b8

* Thu Nov 01 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git8.1
- Linux v4.19-12279-g5b7449810ae6

* Wed Oct 31 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git7.1
- Linux v4.19-11807-g310c7585e830

* Tue Oct 30 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git6.1
- Linux v4.19-11706-g11743c56785c

* Mon Oct 29 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git5.1
- Linux v4.19-9448-g673c790e7282

* Fri Oct 26 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git4.1
- Linux v4.19-6148-ge5f6d9afa341

* Thu Oct 25 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git3.1
- Linux v4.19-5646-g3acbd2de6bc3

* Wed Oct 24 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git2.1
- Linux v4.19-4345-g638820d8da8e

* Tue Oct 23 2018 Justin M. Forbes <jforbes@fedoraproject.org> - 4.20.0-0.rc0.git1.1
- Linux v4.19-1676-g0d1b82cd8ac2
- Reenable debugging options.

* Mon Oct 22 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-1
- Linux v4.19
- Disable debugging options.

* Sat Oct 20 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Fix network on some i.MX6 devices (rhbz 1628209)

* Fri Oct 19 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc8.git4.1
- Linux v4.19-rc8-95-g91b15613ce7f
- Enable pinctrl-cannonlake (rhbz 1641057)

* Thu Oct 18 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc8.git3.1
- Linux v4.19-rc8-27-gfa520c47eaa1

* Wed Oct 17 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc8.git2.1
- Linux v4.19-rc8-16-gc343db455eb3

* Tue Oct 16 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Fixes to Rock960 series of devices, improves stability considerably
- Raspberry Pi graphics fix

* Tue Oct 16 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc8.git1.1
- Linux v4.19-rc8-11-gb955a910d7fd
- Re-enable debugging options.

* Mon Oct 15 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc8.git0.1
- Linux v4.19-rc8

* Mon Oct 15 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Oct 12 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Rebase device specific NVRAM files on brcm WiFi devices to latest

* Fri Oct 12 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc7.git4.1
- Linux v4.19-rc7-139-g6b3944e42e2e

* Thu Oct 11 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc7.git3.1
- Linux v4.19-rc7-61-g9f203e2f2f06

* Wed Oct 10 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc7.git2.1
- Linux v4.19-rc7-33-gbb2d8f2f6104

* Tue Oct 09 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc7.git1.1
- Linux v4.19-rc7-15-g64c5e530ac2c
- Re-enable debugging options.

* Mon Oct 08 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc7.git0.1
- Linux v4.19-rc7

* Mon Oct 08 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Oct 05 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc6.git4.1
- Linux v4.19-rc6-223-gbefad944e231

* Thu Oct 04 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc6.git3.1
- Linux v4.19-rc6-177-gcec4de302c5f

* Wed Oct 03 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc6.git2.1
- Linux v4.19-rc6-37-g6bebe37927f3

* Tue Oct 02 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc6.git1.1
- Linux v4.19-rc6-29-g1d2ba7fee28b
- Re-enable debugging options.

* Mon Oct 01 2018 Laura Abbott <labbott@redhat.com>
- Disable CONFIG_CRYPTO_DEV_SP_PSP (rhbz 1608242)

* Mon Oct 01 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc6.git0.1
- Linux v4.19-rc6

* Mon Oct 01 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Mon Oct  1 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Support loading device specific NVRAM files on brcm WiFi devices

* Fri Sep 28 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc5.git3.1
- Linux v4.19-rc5-159-gad0371482b1e

* Wed Sep 26 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Add thermal trip to bcm283x (Raspberry Pi) cpufreq
- Add initial RockPro64 DT support

* Wed Sep 26 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc5.git2.1
- Linux v4.19-rc5-143-gc307aaf3eb47

* Tue Sep 25 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc5.git1.1
- Linux v4.19-rc5-99-g8c0f9f5b309d
- Re-enable debugging options.

* Mon Sep 24 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc5.git0.1
- Linux v4.19-rc5

* Mon Sep 24 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Sep 21 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc4.git4.1
- Linux v4.19-rc4-176-g211b100a5ced

* Thu Sep 20 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc4.git3.1
- Linux v4.19-rc4-137-gae596de1a0c8

* Wed Sep 19 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc4.git2.1
- Linux v4.19-rc4-86-g4ca719a338d5

* Tue Sep 18 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc4.git1.1
- Linux v4.19-rc4-78-g5211da9ca526
- Enable debugging options.

* Mon Sep 17 2018 Jeremy Cline <jeremy@jcline.org> - 4.19.0-0.rc4.git0.1
- Linux v4.19-rc4

* Mon Sep 17 2018 Jeremy Cline <jcline@redhat.com>
- Stop including the i686-PAE config in the sources
- Disable debugging options.

* Fri Sep 14 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc3.git3.1
- Linux v4.19-rc3-247-gf3c0b8ce4840

* Thu Sep 13 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc3.git2.1
- Linux v4.19-rc3-130-g54eda9df17f3

* Thu Sep 13 2018 Hans de Goede <hdegoede@redhat.com>
- Add patch silencing "EFI stub: UEFI Secure Boot is enabled." at boot

* Wed Sep 12 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc3.git1.1
- Linux v4.19-rc3-21-g5e335542de83
- Re-enable debugging options.

* Mon Sep 10 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc3.git0.1
- Linux v4.19-rc3

* Mon Sep 10 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Sep 07 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc2.git3.1
- Linux v4.19-rc2-205-ga49a9dcce802

* Thu Sep 06 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc2.git2.1
- Linux v4.19-rc2-163-gb36fdc6853a3

* Wed Sep 05 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc2.git1.1
- Linux v4.19-rc2-107-g28619527b8a7
- Re-enable debugging options

* Mon Sep  3 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Enable bcm283x VCHIQ, camera and analog audio drivers
- ARM config updates for 4.19

* Mon Sep 03 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc2.git0.1
- Linux v4.19-rc2

* Mon Sep 03 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Fri Aug 31 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc1.git4.1
- Linux v4.19-rc1-195-g4658aff6eeaa

* Thu Aug 30 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc1.git3.1
- Linux v4.19-rc1-124-g58c3f14f86c9

* Wed Aug 29 2018 Jeremy Cline <jeremy@jcline.org>
- Enable the AFS module (rhbz 1616016)

* Wed Aug 29 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc1.git2.1
- Linux v4.19-rc1-95-g3f16503b7d22

* Tue Aug 28 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc1.git1.1
- Linux v4.19-rc1-88-g050cdc6c9501
- Re-enable debugging options

* Mon Aug 27 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc1.git0.1
- Linux v4.19-rc1

* Mon Aug 27 2018 Jeremy Cline <jcline@redhat.com>
- Disable debugging options.

* Sat Aug 25 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git12.1
- Linux v4.18-12872-g051935978432

* Fri Aug 24 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git11.1
- Linux v4.18-12721-g33e17876ea4e

* Thu Aug 23 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git10.1
- Linux v4.18-11682-g815f0ddb346c

* Wed Aug 22 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git9.1
- Linux v4.18-11219-gad1d69735878

* Tue Aug 21 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git8.1
- Linux v4.18-10986-g778a33959a8a

* Mon Aug 20 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git7.1
- Linux v4.18-10721-g2ad0d5269970

* Sun Aug 19 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git6.1
- Linux v4.18-10568-g08b5fa819970

* Sat Aug 18 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git5.1
- Linux v4.18-8895-g1f7a4c73a739

* Fri Aug 17 2018 Laura Abbott <labbott@redhat.com>
- Enable CONFIG_AF_KCM (rhbz 1613819)

* Fri Aug 17 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git4.1
- Linux v4.18-8108-g5c60a7389d79
- Re-enable AEGIS and MORUS ciphers (rhbz 1610180)

* Thu Aug 16 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git3.1
- Linux v4.18-7873-gf91e654474d4

* Wed Aug 15 2018 Peter Robinson <pbrobinson@fedoraproject.org>
- Drop PPC64 (Big Endian) configs

* Wed Aug 15 2018 Laura Abbott <labbott@redhat.com> - 4.19.0-0.rc0.git2.1
- Linux v4.18-2978-g1eb46908b35d

* Tue Aug 14 2018 Jeremy Cline <jcline@redhat.com> - 4.19.0-0.rc0.git1.1
- Reenable debugging options.
- Linux v4.18-1283-g10f3e23f07cb

* Mon Aug 13 2018 Laura Abbott <labbott@redhat.com> - 4.18.0-1
- Linux v4.18
- Disable debugging options.
