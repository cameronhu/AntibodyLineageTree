cd fastBCR_docker

# Log file to record timings
LOG_FILE="timings_log.txt"

# Clear log file if it already exists
> $LOG_FILE

# Loop to run the script 10 times
for i in {0..9}; do
  export BATCH_TASK_INDEX=$i
  echo "Running with BATCH_TASK_INDEX=$BATCH_TASK_INDEX" | tee -a $LOG_FILE
  python fastBCR_batch_pipeline.py --batch_size=1 --batch_input=human_unpaired_heavy_run_to_files.tsv >> $LOG_FILE 2>&1
done

exit 0
