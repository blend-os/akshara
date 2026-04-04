#!/bin/bash

check() {
    return 0
}

depends() {
    echo base
    return 0
}

installkernel() {
    return 0
}

install() {
    inst touch

    inst_hook pre-pivot 15 "$moddir/handle-update.sh"
}
