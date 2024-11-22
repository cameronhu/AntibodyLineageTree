# Script to be run from within Docker container
# Two arguments should be passed in: input_folder and output_folder

# Load required libraries
library(fastBCR)
library(argparse)

# Parse arguments
parser <- ArgumentParser(description = "Run fastBCR pipeline with specified input and output folders.")
parser$add_argument("--input_folder", type = "character", required = TRUE,
                    help = "Path to the input folder containing data.")
parser$add_argument("--output_folder", type = "character", required = TRUE,
                    help = "Path to the output folder for storing results.")

args <- parser$parse_args()

input_folder <- args$input_folder
output_folder <- args$output_folder

start_time = Sys.time()

oas_raw_data_list = data.load(folder_path = input_folder, storage_format = "csv")
# example/OAS only contains one file for a single individual

oas_proc_data_list = data.preprocess(data_list = oas_raw_data_list, count_col_name = "Redundancy")

oas_clusters_list = data.BCR.clusters(pro_data_list = oas_proc_data_list)

oas_cluster = oas_clusters_list[[1]]
# Since we only have one individual and one input file, 
# there is only one list stored in the clusters_list. Accessing the single cluster

clonal.tree.generation(bcr_clusters = oas_cluster, raw_data = oas_raw_data_list[[1]], output_dir = output_folder)
# Function to generate clonal tree input for only one of the clonal families in this individual

end_time = Sys.time()

print(paste("fastBCR pipeline took:", difftime(end_time, start_time, units = "secs")))

