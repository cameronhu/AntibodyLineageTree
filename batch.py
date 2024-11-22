import argparse
import tempfile
import sys
import os
import Bio.SeqIO
import sys
import os
import gzip
import json
import time
import numpy as np
import shutil
import multiprocessing as mp
import subprocess as sp

from pprint import pprint
from google.cloud import storage

__version__ = "0.0.1"


def gcs_copy(bucket_name, src_name, dst_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(src_name)
    blob.download_to_filename(dst_name)


def gcs_upload(src_name, bucket_name, dst_name):
    client = storage.Client()
    bucket = client.bucket(bucket_name)
    blob = bucket.blob(dst_name)
    blob.upload_from_filename(src_name)


def gcs_read(bucket_name, src_name):
    client = storage.Client()
    bucket = client.get_bucket(bucket_name)
    blob = bucket.blob(src_name)
    try:
        return blob.download_as_text()
    except Exception as e:
        print(f"Error reading file from GCS: {e}")
        return None


def split_fasta(input_path, output_dir, num_splits):
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    total_size = 0
    for r in Bio.SeqIO.parse(input_path, "fasta"):
        total_size += len(r.seq)
    split_size = int(total_size / num_splits)
    split = -1
    cursize = 0
    out = None
    for r in Bio.SeqIO.parse(input_path, "fasta"):
        if out is None or cursize >= split_size:
            split += 1
            cursize = 0
            out = open(os.path.join(output_dir, str(split)), "w")
        out.write(">" + r.description + "\n" + str(r.seq) + "\n")
        cursize += len(r.seq)
    out.close()


def filter_contigs(input_path, output_path, sample_name, min_contig_len, max_n_fract):
    with gzip.open(input_path, "rt") as fin:
        with open(output_path, "w") as fout:
            for i, r in enumerate(Bio.SeqIO.parse(fin, "fasta")):
                seq = str(r.seq).upper()
                if len(seq) < min_contig_len:
                    continue
                elif 1.0 * seq.count("N") / len(seq) > max_n_fract:
                    continue
                fout.write(f">{sample_name}_{i} {r.description}\n{seq}\n")


def run_command(cmd):
    proc = sp.Popen(cmd, shell=True, stdout=sp.PIPE, stderr=sp.PIPE)
    out, err = proc.communicate()
    try:
        retcode = proc.retcode
    except AttributeError:
        retcode = proc.returncode
    if retcode != 0:
        raise Exception(f"Subprocess error running: {cmd.split()}")


def calculate_n50(contig_lengths):
    total_length = sum(contig_lengths)
    half_length = total_length / 2
    running_sum = 0
    for length in sorted(contig_lengths, reverse=True):
        running_sum += length
        if running_sum >= half_length:
            return length


def compute_summary_stats(contigs, proteins, output):
    stats = {}

    aalen = {"full": [], "partial": [], "all": []}
    with open(proteins, "rt") as handle:
        for _ in Bio.SeqIO.parse(handle, "fasta"):
            info = dict([_.split("=") for _ in _.description.split()[-1].split(";")])
            aalen["all"].append(len(_.seq))
            if info["partial"] == "00":
                aalen["full"].append(len(_.seq))
            else:
                aalen["partial"].append(len(_.seq))

    stats["protein"] = {}
    for type in ["all", "full", "partial"]:
        stats["protein"][type] = {}
        stats["protein"][type]["count"] = len(aalen[type])
        stats["protein"][type]["min_len"] = (
            min(aalen[type]) if len(aalen[type]) > 0 else None
        )
        stats["protein"][type]["max_len"] = (
            max(aalen[type]) if len(aalen[type]) > 0 else None
        )
        stats["protein"][type]["avg_len"] = (
            round(np.mean(aalen[type]), 2) if len(aalen[type]) > 0 else None
        )
        stats["protein"][type]["sum_len"] = sum(aalen[type])

    with open(contigs, "rt") as handle:
        contig_lengths = [len(_.seq) for _ in Bio.SeqIO.parse(handle, "fasta")]
        stats["contig"] = {}
        stats["contig"]["count"] = len(contig_lengths)
        stats["contig"]["min_len"] = (
            min(contig_lengths) if len(contig_lengths) > 0 else None
        )
        stats["contig"]["max_len"] = (
            max(contig_lengths) if len(contig_lengths) > 0 else None
        )
        stats["contig"]["avg_len"] = (
            round(np.mean(contig_lengths), 2) if len(contig_lengths) > 0 else None
        )
        stats["contig"]["sum_len"] = sum(contig_lengths)
        stats["contig"]["n50"] = calculate_n50(contig_lengths)
        stats["contig"]["cds_density"] = (
            round(
                100 * stats["protein"]["full"]["sum_len"] * 3 / sum(contig_lengths), 2
            )
            if len(contig_lengths) > 0
            else None
        )

    with open(output, "w") as fout:
        fout.write(json.dumps(stats, indent=2))


class Pipeline:
    def __init__(self):
        self.parse_args()
        self.fetch_inputs()
        pprint(self.args)

    def fetch_inputs(self):

        input_start = self.args["batch_size"] * self.args["batch_task_index"]
        input_stop = input_start + self.args["batch_size"]

        if os.path.exists(self.args["batch_input"]):
            input_list = [_.split() for _ in open(self.args["batch_input"])]
        else:
            bucket, path = self.args["batch_input"].split("/", 1)
            input_list = [_.split("\t")[0] for _ in gcs_read(bucket, path).split("\n")]

        self.input_list = input_list[input_start:input_stop]

    def parse_args(self):

        parser = argparse.ArgumentParser()
        parser.add_argument(
            "--batch_task_index", type=int, default=os.environ.get("BATCH_TASK_INDEX")
        )
        parser.add_argument("--batch_size", type=int)
        parser.add_argument("--batch_input", type=str)
        parser.add_argument("--cpu_count", type=int, default=os.cpu_count())
        parser.add_argument("--tmp_dir", type=str, default=tempfile.mkdtemp())
        args = vars(parser.parse_args())
        required = ["batch_task_index", "batch_size", "batch_input"]
        for field in required:
            if args[field] is None:
                sys.exit("Error: required field missing: %s" % field)
        self.args = args

    def run_main(self):
        for input in self.input_list:
            try:
                self.main(input)
                print(f"input: {input}: success")
            except Exception as error:
                print(f"input: {input}: failure: {error}")

    def main(self, input, threads=1):
        # parse inputs
        input = input.replace("gs://", "")
        gcs_bucket, gcs_path = input.split("/", 1)
        run_name = os.path.basename(gcs_path).replace(".csv", "")

        # make tmpdir
        tmp_dir = os.path.join(self.args["tmp_dir"], run_name)
        os.makedirs(tmp_dir, exist_ok=True)

        # copy input
        dst_name = f"{tmp_dir}/{os.path.basename(gcs_path)}"
        gcs_copy(gcs_bucket, gcs_path, dst_name)

        # run fastbr
        # ....
        # ....
        # ....

        files = ["ERR4077973.csv"]
        dst_dir = f"lineages/fastbcr/output/runs/{run_name}"
        for file in files:
            gcs_upload(
                src_name=os.path.join(tmp_dir, file),  # path to file in tmp_dir
                bucket_name=gcs_bucket,  # destination gcs_bucket
                dst_name=os.path.join(dst_dir, file),
            )

        # clean up
        shutil.rmtree(f"{tmp_dir}")


if __name__ == "__main__":

    pipeline = Pipeline()
    pipeline.run_main()


# Have to set BATCH_TASK_INDEX ENV variable

"""
The Docker container should have an entrypoint into this Python script. This Python script requires additional arguments, hence the argparse().
These additional arguments include --batch_input, --batch_size, and --BATCH_TASK_INDEX
However, these additional arguments should be supplied by the GCP Batch job script.
"""
