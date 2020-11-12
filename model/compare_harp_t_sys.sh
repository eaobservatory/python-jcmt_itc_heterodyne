#!/bin/bash

set -ex

mkdir -p harp_combined_median
python model/combine_rxinfo.py -v --instrument HARP \
    --date-start 20100101 --date-end 20201111 \
    --dir rxinfo --outdir harp_combined_median --median

python model/make_comparison.py -v --dir harp_combined_median --outdir harp_combined_median --receiver HARP

python model/plot_comparison.py -v --receiver HARP --plot harp_combined_median/tsys_comparison.pdf \
    harp_combined_median/comparison_median_LSB.txt \
    harp_combined_median/comparison_median_USB.txt
