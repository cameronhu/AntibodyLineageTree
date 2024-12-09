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
