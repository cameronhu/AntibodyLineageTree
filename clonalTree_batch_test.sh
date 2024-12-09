cd clonalTree_Docker

# Run clonal tree batch input generation script (stores file in GCS)
./generate_clonalTree_batch_input.sh

# # run test
export BATCH_TASK_INDEX=0
input=proevo-ab/lineages/clonalTree/batch/clonalTree_input_directories.txt

python clonalTree_batch_pipeline.py --batch_size=1 --batch_input=$input