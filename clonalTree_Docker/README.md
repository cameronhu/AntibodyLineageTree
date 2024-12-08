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

## Testing of interactive Docker container
Build test container: 
```docker build -f Dockerfile_testing . -t clonaltree:latest```
```docker run -it --rm clonaltree:latest```

## Testing of Production Docker container

Building of production Docker container, and push to artifact registry
```
docker build --no-cache . -t clonaltree:prod_timing
docker tag clonaltree:prod_timing us-central1-docker.pkg.dev/profluent-evo/ab-lineages/clonaltree:prod_timing
docker push us-central1-docker.pkg.dev/profluent-evo/ab-lineages/clonaltree:prod_timing
```

Test production container
```
docker run --rm clonaltree:prod_timing --batch_task_index=0 --batch_size=1 --batch_input=proevo-ab/lineages/clonalTree/batch/clonalTree_batch_input.txt
```

# Batch Job Notes

Total number of FASTA files as of 12/8 is 706458. First run batch job has 5000 tasks, with batch_size of 150 (150 fasta files per compute instance). No memory consideration implemented yet.