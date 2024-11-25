cd lineage_tree

# # list gcs inputs
# gsutil ls gs://proevo-ab/lineages/fastbcr/input/runs/*.csv > gcs_input_list.txt

# # copy input file to gcs
# gsutil cp gcs_input_list.txt gs://proevo-ab/lineages/fastbcr/batch/gcs_input_list.txt

# # run test
export BATCH_TASK_INDEX=0
# input=proevo-ab/lineages/fastbcr/batch/gcs_input_list.txt
# python batch.py --batch_size=1 --batch_input=$input


python batch_pipeline.py --batch_size=1 --batch_input=human_unpaired_heavy_run_to_files.tsv



