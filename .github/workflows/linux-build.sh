#!/usr/bin/env bash

set -euo pipefail

run () {
  arch="$1"
  EXTRA_PACKAGES=""
  if [ "$arch" = "amd64" ] || [ "$arch" == "i386" ]; then
    EXTRA_PACKAGES="g++-multilib"
  fi

  apt-get update
  apt-mark hold php* google* libobjc* libpq* libidn* postgresql* python3-httplib2 samba* >/dev/null
  apt-get upgrade -y
  apt-get install -y binutils-dev libcurl4-openssl-dev libdw-dev libiberty-dev gcc g++ make cmake libssl-dev git python3 python2 $EXTRA_PACKAGES

  export PATH="${PATH}:${HOME}/kcov/bin"
  mkdir build build-tests

  cd build
  cmake -DCMAKE_INSTALL_PREFIX=/usr/local .. || exit 64
  make || exit 64
  make install || exit 64
  cd ..

  cd build-tests
  cmake ../tests || exit 64
  make || exit 64
  cd ..

  tar czf kcov-"$1".tar.gz /usr/local/bin/kcov* /usr/local/share/doc/kcov/* /usr/local/share/man/man1/kcov.1
  readelf -h /usr/local/bin/kcov
  if [[ -e "kcov-$1.tar.gz" ]]; then
    echo "Built for $1".
  fi

  kcov --include-pattern=test-executable.sh coverage .github/workflows/test-executable.sh

  local coverage="$(<coverage/test-executable.sh/coverage.json)"
  local percent="${coverage##*percent_covered\": \"}"
  local total_lines="${coverage##*total_lines\": }"
  local covered_lines="${coverage##*covered_lines\": }"
  
  echo -e "Coverage: ${covered_lines%%,*}/${total_lines%%,*} ${percent%%\"*}%"
}

run "$@"
