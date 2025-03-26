python3 main.py \
--batch-size 32 \
--gpu 0 \
--epochs 100 \
--nb-run 1 \
--model-name resnet18 \
--optim-name fmfp \
--crl-weight 0 \
--mixup-weight 1 \
--mixup-beta 10 \
--use-cosine \
--save-dir ./PlantImage_out/resnet18_out \
PlantImage_Balanced_Split