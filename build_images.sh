
for SUBDIR in minio postgres frontend backend
do
    ( cd $SUBDIR/docker ; ./build_images.sh )
done

