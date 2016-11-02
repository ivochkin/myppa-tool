#!/bin/bash

### settings
chroot_dir="$(uuidgen)"
chroot_original_dir=$chroot_dir.original
bintools_dir=$(pwd)/destroot
apt_mirror='http://archive.ubuntu.com/ubuntu'

### make sure that the required tools are installed
packages="debootstrap fakeroot fakechroot proot"
for i in $packages ; do
  which $i || ( echo "Missing $i" && exit 1 )
done

### apt-get have been removed from 16.04
apt=apt

### install a minbase system with debootstrap
export DEBIAN_FRONTEND=noninteractive
fakeroot fakechroot debootstrap --variant=fakechroot --arch={{architecture}} {{codename}} $chroot_dir $apt_mirror

# Remove symlinks created by debootstrap
rm -f $chroot_dir/proc
rm -f $chroot_dir/dev

prootsh() {
  proot --rootfs=$chroot_dir --pwd=/ --root-id --bind=/proc --bind=/dev --bind=/sys "$@"
  rm -rf $chroot_dir/proc $chroot_dir/dev $chroot_dir/sys
}

### install ubuntu-minimal
files_to_copy="/etc/resolv.conf"
for i in $files_to_copy ; do
  cp $i $chroot_dir/$i
done
prootsh $apt install -y build-essential cmake git wget libtool autoconf autogen
{% for package in build_depends %}
prootsh $apt install -y {{package}}
{%- endfor %}

cp -rl $chroot_dir $chroot_original_dir

cat <<EOT > $chroot_dir/build_install_clean.sh
git clone --recursive --branch={{git_revision}} {{git_repository}} {{name}}
cd {{name}}
{{before_configure}}
{% if builder == "cmake" %}
mkdir build
cd build
cmake {% for k, v in cmake_args.items() %}-D{{k}}={{v}} {% endfor %}..
{% elif builder == "autotools" %}
./configure {% for k, v in (configure_args or {}).items() %}--{{k}}={{v}} {% endfor %}
{% endif %}
{{after_configure}}
{{before_compile}}
make
{{after_compile}}
{{before_install}}
make install
{{after_install}}
rm -rf /{{name}}
EOT
prootsh bash build_install_clean.sh
rm $chroot_dir/build_install_clean.sh

### Build a list of files created after running build_install_clean.sh
### Then compress them into data.tar.gz
( cd $chroot_dir && find . > files )
( cd $chroot_original_dir && find . > files )
diff --new-line-format="" --unchanged-line-format="" $chroot_dir/files $chroot_original_dir/files > addedfiles.all
for i in $(cat addedfiles.all); do grep -q "$i/" addedfiles.all || echo $i; done > addedfiles
( cd $chroot_dir && fakeroot tar -c -z -v -f ../data.tar.gz $(cat ../addedfiles) )
( cd $chroot_dir && for i in $(cat ../addedfiles); do md5sum $i >> ../md5sums ; done )
rm addedfiles
rm addedfiles.all

cat <<EOT >control
Package: {{name}}
Priority: {{deb_priority}}
Section: {{deb_section}}
Maintainer: {{maintainer}}
Architecture: {{architecture}}
Version: {{version}}
Homepage: {{homepage}}
Description: dfk library
EOT

cat <<EOT >changelog
{{name}} ({{version}}) unstable; urgency=low

  * Initial release

 -- {{maintainer}}  Mon, 31 Oct 2016 00:00:00 +0300

EOT

cat <<EOT >copyright
Files: *
Copyright: 2014-2016 {{maintainer}}
License: {{license}}
EOT

echo "2.0" > debian-binary

fakeroot tar czvf control.tar.gz control changelog copyright md5sums
fakeroot ar cr {{name}}_{{version}}_{{architecture}}.deb debian-binary control.tar.gz data.tar.gz

rm control.tar.gz data.tar.gz debian-binary control changelog copyright md5sums

### cleanup
rm -rf $chroot_dir
rm -rf $chroot_original_dir
