#!/bin/bash

### settings
arch=i386
suite=trusty
chroot_dir="$(uuidgen)"
chroot_original_dir=$chroot_dir.original
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
fakeroot fakechroot debootstrap --variant=fakechroot --arch=$arch $suite $chroot_dir $apt_mirror

# Remove symlinks created by debootstrap
rm -f $chroot_dir/proc
rm -f $chroot_dir/dev

function prootsh {
  proot --rootfs=$chroot_dir --pwd=/ --root-id --bind=/proc --bind=/dev --bind=/sys "$@"
  rm -rf $chroot_dir/proc $chroot_dir/dev $chroot_dir/sys
}

### install ubuntu-minimal
files_to_copy="/etc/resolv.conf"
for i in $files_to_copy ; do
  cp $i $chroot_dir/$i
done
prootsh $apt install -y build-essential cmake git wget libtool autoconf autogen
prootsh $apt install -y libcurl4-openssl-dev

cp -rl $chroot_dir $chroot_original_dir

cat <<EOT > $chroot_dir/build_install_clean.sh
git clone --recursive --branch=v0.0.2 https://github.com/ivochkin/dfk.git
cd dfk
bash scripts/bootstrap.sh
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON -DDFK_MAINTAINER_MODE=ON -DDFK_BUILD_CPP_BINDINGS=ON -DDFK_BUILD_SAMPLES=OFF -DDFK_BUILD_UNIT_TESTS=OFF -DDFK_BUILD_AUTO_TESTS=OFF ..
make
make install
rm -rf /dfk
EOT
prootsh bash build_install_clean.sh
rm $chroot_dir/build_install_clean.sh

### Build a list of files created after running build_install_clean.sh
### Then compress them into data.tar.gz
( cd $chroot_dir && find . > files )
( cd $chroot_original_dir && find . > files )
diff --new-line-format="" --unchanged-line-format="" $chroot_dir/files $chroot_original_dir/files > addedfiles
( cd $chroot_dir && fakeroot tar -c -z -v -f ../data.tar.gz $(cat ../addedfiles) )
( cd $chroot_dir && for i in $(cat ../addedfiles); do md5sum $i >> ../md5sums ; done )
#rm addedfiles

cat <<EOT >control
Package: dfk
Priority: optional
Section: libs
Maintainer: Stanislav Ivochkin <isn@extrn.org>
Architecture: $arch
Version: 0.0.2
Homepage: https://dfk.extrn.org
Description: dfk library
EOT

cat <<EOT >changelog
dfk (0.0.2) unstable; urgency=low

  * Initial release

 -- Stanislav Ivochkin <isn@extrn.org>  Mon, 31 Oct 2016 00:00:00 +0300

EOT

cat <<EOT >copyright
Files: *
Copyright: 2014-2016 Stanislav Ivochkin
License: Expat
EOT

echo "2.0" > debian-binary

fakeroot tar czvf control.tar.gz control changelog copyright md5sums
fakeroot ar cr dfk_0.0.2_i386.deb debian-binary control.tar.gz data.tar.gz

rm control.tar.gz data.tar.gz debian-binary control changelog copyright md5sums

### cleanup
#rm -rf $chroot_dir
#rm -rf $chroot_original_dir
