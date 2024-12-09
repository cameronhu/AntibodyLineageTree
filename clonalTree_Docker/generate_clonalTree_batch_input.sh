# Generates the batch_input for ClonalTree
# Batch input is a list of FASTA files

gsutil ls -r "gs://proevo-ab/lineages/fastbcr/output/runs/**/*.fasta" > clonalTree_batch_input.txt

# Step 2: Upload the file to the desired GCS location
gsutil cp clonalTree_batch_input.txt gs://proevo-ab/lineages/clonalTree/batch/clonalTree_batch_input.txt

