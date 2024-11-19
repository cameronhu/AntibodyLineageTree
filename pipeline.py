from collections import defaultdict
import multiprocessing
import os
import numpy as np


# get list of files associated with each run
def list_samples():
    run_to_files = defaultdict(list)
    dir = "/export/share/cameronhu/oas/unpaired/unpaired_human/unpaired_human_heavy"
    for subdir in os.listdir(dir):
        for file in os.listdir(os.path.join(dir, subdir)):
            filepath = "/".join([dir, subdir, file])
            # split file path to extract run_id
            run_id = file.split("_")[0]
            # print(file)
            # print(run_id)
            # print(filepath)
            # break
            run_to_files[run_id].append(filepath)
    return run_to_files


# # generate data reader function
# def read_data(file_paths):
# 	data = ... # df of data
# 	for file in file_paths:
# 		file_data = .... # read and append to data
# 	return data

# # generate function to prepare fastbcr_input from data object
# def oas_to_fastbcr(data):
# 	# generates fastbcr_input
# 	# returns fastbcr data

# # writes fastbcr data to GCS
# # ask chatgpt for function here
# def write_to_gcs(data, path):
# 	pass

# def pipeline(file_paths, out_path):
# 	oas_data = read_data(file_paths)
# 	fastbcr_data = oas_to_fastbcr(data)
# 	write_to_gcs(fastbcr_data, out_path)

# def parallel_process(run_to_files, out_dir):
#     def process_run(run_id, file_paths):
#         try:
#             print(f"Processing run {run_id}...")
#             output_path = os.path.join(out_dir, f"{run_id}_output")
#             pipeline(file_paths, output_path)
#             print(f"Completed run {run_id}")
#         except Exception as e:
#             print(f"Error in run {run_id}: {e}")

#     with multiprocessing.Pool(processes=multiprocessing.cpu_count()) as pool:
#         tasks = [(run_id, file_paths) for run_id, file_paths in run_to_files.items()]
#         results = [pool.apply_async(process_run, args=(run_id, file_paths)) for run_id, file_paths in tasks]
#         for result in results:
#             result.get()


# if __name__ == "__main__":
#     run_to_files = list_samples()
#     out_dir = "/path/to/output"
#     import time
#     run_ids = np.random.choice(list(run_to_files.keys(), 20))
#     for run in run_ids:
# 		file_paths = run_to_files[run]
# 		start = time.time()
# 		output_path = ...
# 		pipeline(file_paths, output_path)
# 		end = time.time()
# 		print(f"time for {run}:", end-start)


# #if __name__ == "__main__":
# #    run_to_files = list_samples()
# #    out_dir = "/path/to/output"
# #    parallel_process(run_to_files, out_dir)
