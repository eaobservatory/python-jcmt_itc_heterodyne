#!/bin/bash

RECEPTORS="H00 H01 H02 H03 H04 H05 H06 H07 H08 H09 H10 H11 H12 H13 H15"

set -ex

mkdir -p harp_combined
python combine_rxinfo.py -v --instrument HARP \
    --date-start 20100101 --date-end 20190920 \
    --dir rxinfo --outdir harp_combined

for RECEPTOR in $RECEPTORS
do
    python bin_combined_data.py -v \
        harp_combined/merged_${RECEPTOR}_{LSB,USB}.txt \
        > harp_combined/merged_${RECEPTOR}_bin.txt
done

python fit_t_rx_model.py -v --remove-outliers \
    --out harp_combined/model.txt --out-trx harp_combined/t_rx.txt \
    harp_combined/merged_H00_bin.txt \
    harp_combined/merged_H01_bin.txt \
    harp_combined/merged_H03_bin.txt \
    harp_combined/merged_H05_bin.txt \
    harp_combined/merged_H07_bin.txt \
    harp_combined/merged_H08_bin.txt \
    harp_combined/merged_H09_bin.txt \
    harp_combined/merged_H12_bin.txt
