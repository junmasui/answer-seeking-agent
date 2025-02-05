
for SUBDIR in langfuse minio postgres frontend backend
do
    ( cd $SUBDIR/docker ; ./build_images.sh )
done

