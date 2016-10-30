#!/bin/bash

### settings
arch=amd64
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
wget https://github.com/ivochkin/dfk/archive/v0.0.1.tar.gz
tar xzvf v0.0.1.tar.gz
cd dfk-0.0.1
bash scripts/bootstrap.sh
mkdir build
cd build
cmake -DCMAKE_BUILD_TYPE=Release -DBUILD_SHARED_LIBS=ON ..
make
make install
rm -rf /dfk-0.0.1
rm -rf /v0.0.1.tar.gz
EOT
prootsh bash build_install_clean.sh
rm $chroot_dir/build_install_clean.sh

### Build a list of files created after running build_install_clean.sh
### Then compress them into package.tar.gz
( cd $chroot_dir && find . > files )
( cd $chroot_original_dir && find . > files )
diff --new-line-format="" --unchanged-line-format="" $chroot_dir/files $chroot_original_dir/files > addedfiles
( cd $chroot_dir && tar -c -z -v -f ../package.tar.gz $(cat ../addedfiles) )
rm addedfiles

### cleanup
rm -rf $chroot_dir
rm -rf $chroot_original_dir
