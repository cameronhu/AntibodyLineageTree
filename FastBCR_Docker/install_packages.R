# install_packages.R

# Set the library path explicitly
# lib_path <- "/usr/local/lib/R/site-library"

# Ensure the library directory exists
# dir.create(lib_path, showWarnings = FALSE, recursive = TRUE)

# Set the library path
# .libPaths(c(lib_path, .libPaths()))




# BiocManager
install.packages("BiocManager")
BiocManager::install(c("proj4", "msa", "ggtree", "ggmsa"), ask = FALSE)

# install.packages("BiocManager", lib = lib_path)
# BiocManager::install(c("proj4", "msa", "ggtree", "ggmsa"), lib = lib_path, ask = FALSE)

# devtools
install.packages(c('systemfonts', 'textshaping', 'ragg', 'pkgdown'))
install.packages("devtools")
# install.packages("devtools", lib = lib_path)

# fastBCR
devtools::install_github("ZhangLabTJU/fastBCR", ref = "v1.1.3")

# Print library paths to verify
print(.libPaths())
