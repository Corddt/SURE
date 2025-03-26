python3 main.py \
--batch-size 64 \
--gpu 0 \
--epochs 30 \
--nb-run 1 \
--model-name resnet50 \
--optim-name fmfp \
--crl-weight 0.2 \
--mixup-weight 1 \
--mixup-beta 10 \
--lr 0.01 \
--swa-lr 0.005 \
--swa-epoch-start 22 \
--use-cosine True \
--save-dir ./PlantImage_out/resnet18_out \
PlantImage_Balanced_Split

python3 test.py \
--batch-size 64 \
--gpu 0 \
--nb-run 1 \
--model-name resnet50 \
--optim-name fmfp \
--crl-weight 0.2 \
--mixup-weight 1 \
--use-cosine True \
--save-dir ./PlantImage_out/resnet18_out \
PlantImage_Balanced_Split