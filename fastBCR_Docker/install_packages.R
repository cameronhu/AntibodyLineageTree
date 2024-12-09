# install_packages.R

if (!require("BiocManager", quietly = TRUE)) {
    install.packages("BiocManager")
}

BiocManager::install(c("proj4","msa","ggtree","ggmsa"))

install.packages("argparse")

if(!require(devtools)) {
    install.packages('devtools')
}
devtools::install_local('profluent-fastBCR')