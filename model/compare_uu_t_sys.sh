#!/bin/bash

set -ex

mkdir -p uu_combined_mean
python model/combine_rxinfo.py -v --instrument UU \
    --date-start 20200721 --date-end 20201111 \
    --dir rxinfo --outdir uu_combined_mean --mean

python model/make_comparison.py -v --receiver UU --sideband --if \
    --dir uu_combined_mean --outdir uu_combined_mean

python model/plot_comparison.py -v --receiver UU --sideband --ratio \
    --plot uu_combined_mean/tsys_comparison.pdf --ymax 3.0 \
    uu_combined_mean/comparison_mean_LSB.txt \
    uu_combined_mean/comparison_mean_USB.txt
