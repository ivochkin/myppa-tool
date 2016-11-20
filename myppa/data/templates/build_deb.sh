#!/bin/sh
# Tree structure of the cwd:

taskid=$(uuidgen)

git clone --recursive --branch={{git_revision}} {{git_repository}} src
version={{version}}
{% if version_script %}
cd src
version=$({{version_script}})
cd -
{% endif %}
{% if version_append_codename %}
version=${version}~{{codename}}
{% endif %}

# myppa-install-prerequisite.sh
cat <<EOT > myppa-install-prerequisite.sh
#!/usr/bin/env bash
{% for package in build_depends %}
apt-get install -y {{package}}
{%- endfor %}
EOT

# myppa-install-project.sh
cat <<EOT > myppa-install-project.sh
#!/usr/bin/env bash
cd /myppa/src
{{before_configure}}
mkdir /myppa/build
cd /myppa/build
{% if builder == "cmake" %}
cmake {% for k, v in cmake_args.items() %}-D{{k}}={{v}} {% endfor %}../src
{% elif builder == "autotools" %}
../src/configure {% for k, v in (configure_args or {}).items() %}--{{k}}={{v}} {% endfor %}
{% endif %}
cd /myppa/src
{{after_configure}}
cd /myppa/src
{{before_compile}}
cd /myppa/build
make
cd /myppa/src
{{after_compile}}
cd /myppa/src
{{before_install}}
cd /myppa/build
make install
cd /myppa/src
{{after_install}}
EOT

# myppa-pack-deb.sh
cat <<EOT >myppa-pack-deb.sh
#!/usr/bin/env bash
for i in \$(cat myppa-new-files-raw); do
  if ! grep -q "^\$i/" myppa-new-files-raw; then
    echo \$i >> myppa-new-files-no-dirs
  fi
done
cat myppa-new-files-no-dirs | egrep '({{install_paths | join(")|(")}})' > myppa-new-files
<myppa-new-files xargs tar czf data.tar.gz
<myppa-new-files xargs md5sum > md5sums
fakeroot tar czvf control.tar.gz control changelog copyright md5sums
fakeroot ar cr {{name}}_${version}_{{architecture}}.deb debian-binary control.tar.gz data.tar.gz
EOT

cat <<EOT >control
Package: {{name}}
Priority: {{deb_priority}}
Section: {{deb_section}}
Maintainer: {{maintainer}}
Architecture: {{architecture}}
Version: ${version}
Homepage: {{homepage}}
Description: dfk library
EOT

cat <<EOT >changelog
{{name}} ($version) unstable; urgency=low

  * Initial release

 -- {{maintainer}}  Mon, 31 Oct 2016 00:00:00 +0300

EOT

cat <<EOT >copyright
Files: *
Copyright: 2014-2016 {{maintainer}}
License: {{license}}
EOT

cat <<EOT >debian-binary
2.0
EOT

baseimage=ivochkin/myppa:{{distribution}}.{{codename}}.{{architecture}}
docker pull $baseimage
docker run --volume $(pwd):/myppa -w /myppa --cidfile stage1.cid $baseimage bash myppa-install-prerequisite.sh
stage1cid=$(cat stage1.cid)
stage1iid=myppa:$taskid-1
docker commit $stage1cid $stage1iid
docker run --volume $(pwd):/myppa -w /myppa --cidfile stage2.cid $stage1iid bash myppa-install-project.sh
stage2cid=$(cat stage2.cid)
stage2iid=myppa:$taskid-2
docker diff $stage2cid | grep -e '^A' | awk '{print $2}' > myppa-new-files-raw
docker commit $stage2cid $stage2iid
docker run --rm --volume $(pwd):/myppa -w /myppa $stage2iid bash myppa-pack-deb.sh
docker rm $stage2cid $stage1cid
docker rmi $stage1iid $stage2iid
