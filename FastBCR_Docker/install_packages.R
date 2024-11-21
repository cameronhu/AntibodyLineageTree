# # install_packages.R

# # Set the library path explicitly
# lib_path <- "/usr/local/lib/R/site-library"

# # Ensure the library directory exists
# dir.create(lib_path, showWarnings = FALSE, recursive = TRUE)

# # Set the library path
# .libPaths(c(lib_path, .libPaths()))

# # Install necessary packages
# install.packages("BiocManager", lib = lib_path)
# BiocManager::install(c("proj4", "msa", "ggtree", "ggmsa"), lib = lib_path, ask = FALSE)
# install.packages("devtools", lib = lib_path)
# devtools::install_github("ZhangLabTJU/fastBCR", ref = "v1.1.3")

# # Print library paths to verify
# print(.libPaths())

if (!require("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager")
}

BiocManager::install(c("proj4","msa","ggtree", "ggmsa"))

# install.packages(c('systemfonts', 'textshaping', 'ragg', 'pkgdown'))

if(!require(devtools)) {
    install.packages('devtools')
}