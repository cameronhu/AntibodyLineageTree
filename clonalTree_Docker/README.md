# Clonal Tree Docker Pipeline Notes

## Test clonalTree_batch_pipeline.py script

Python script needs to be run with at least 3 inputs, batch_task_index, batch_size, batch_input. Run the following bash commands to test just the script with a local batch_input file.
```
python clonalTree_batch_pipeline.py --batch_task_index=0 --batch_size=1 --batch_input=clonalTree_batch_input.txt
```

To test with a GCS batch input file (production), replace the --batch_input with the path to the input on GCS
```
python clonalTree_batch_pipeline.py --batch_task_index=0 --batch_size=1 --batch_input=proevo-ab/lineages/clonalTree/batch/clonalTree_batch_input.txt
```