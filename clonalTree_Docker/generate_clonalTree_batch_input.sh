# Step 1: List directories and save to a local file
gsutil ls -d gs://proevo-ab/lineages/fastbcr/output/runs/*/ > clonalTree_input_directories.txt

# Step 2: Upload the file to the desired GCS location
gsutil cp clonalTree_input_directories.txt gs://proevo-ab/lineages/clonalTree/batch/clonalTree_input_directories.txt

# Step 3: (Optional) Remove the local file if no longer needed
rm clonalTree_input_directories.txt
