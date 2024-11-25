# Lineage Tree Generation

Lineage tree generation for clonal families of antibody sequences, leveraging the FastBCR and ClonalTree tools

## Running fastBCR Docker Container in interactive mode

A Docker container exits to run the fastBCR input generation and fastBCR pipeline: `fastbcr`. For timing purposes, run the following command to mount the `lineage_tree` repository to the container:

```
docker run -it -v /home/cameronhu/lineage_tree:/lineage_tree fastbcr bash
```

Then, within the container, run the following script to perform a timing test on the first 10 generated inputs:

```
cd ../lineage_tree;
chmod +x batch_timing_loop.sh
./batch_timing_loop.sh
tail -f timings_log.txt
```


## FastBCR Input Generation Notes

- `list_samples()` generates 3660 runs from just the human heavy chains. There are ~4000 runs total when querying the BigQuery db.
- Running pipeline on 64 GB had insufficient memory for run: "proevo-ab/lineages/fastbcr/input/runs/SRR8365422". Increased to 124GB and testing.
- Completed SRR8365422 at 124 GB, but was close to 100 GB of total memory. SRR8365422 has 4_545_677 unique  sequences, and 6_177_127 total sequences. ~950 seconds to complete this processing.
- SRR8365433 crashed memory, has 25,705,003 total sequences, ~5 million unique sequences
- Updated to 250 GB memory, was able to run SRR8283795 with 7.6 million unique sequences

