import os


def save_grouped_metrics(files_to_group, grouped_metric_file_path):
    os.makedirs(grouped_metric_file_path, exist_ok=True)
    for k1, v1 in files_to_group.items():
        for k2, v2 in v1.items():
            save_str = ""
            grouped_metric_file_name = "{}-{}.dat".format(k1, k2)
            abs_file_path = os.path.join(grouped_metric_file_path, grouped_metric_file_name)

            for k3, v3 in v2.items():
                summed_val = sum(v3) / len(v3)
                save_str += "{} {}\n".format(k3, summed_val)
            with open(abs_file_path, "w") as grouped_metric_file:
                grouped_metric_file.write(save_str)

def group_metrics_for_splice_size_noise_level():
    metric_file_path = "data/latex_data/direct-metrics"
    grouped_metric_file_path = "data/latex_data/direct-metrics-grouped"

    files_to_group = {}
    for dirpath, subdir, filenames in os.walk(metric_file_path):
        for fn in filenames:
            metric_name = fn.split("-")[-1].split(".")[0]
            splice_size = fn.split("-")[0].split("_")[-1]
            noise_level = fn.split("-")[0].split("_")[1]
            files_to_group.setdefault(metric_name, {}).setdefault(noise_level, {}).setdefault(splice_size, [])

            with open(os.path.join(metric_file_path, fn), "r") as metric_file:
                metric_value = float(metric_file.readlines()[0])
            files_to_group[metric_name][noise_level][splice_size].append(metric_value)

    save_grouped_metrics(files_to_group, grouped_metric_file_path)


def group_metrics_for_beat_position_algorithm():
    metric_file_path = "data/latex_data/beat-pos-direct-metrics"
    grouped_metric_file_path = "data/latex_data/beat-pos-direct-metrics-grouped"

    files_to_group = {}
    for dirpath, subdir, filenames in os.walk(metric_file_path):
        for fn in filenames:
            metric_name = fn.split("--")[-1].split(".")[0]
            beat_pos = fn.split("--")[0].split("_")[-2]
            algorithm = fn.split("--")[1]
            files_to_group.setdefault(metric_name, {}).setdefault(algorithm, {}).setdefault(beat_pos, [])

            with open(os.path.join(metric_file_path, fn), "r") as metric_file:
                metric_value = float(metric_file.readlines()[0])
            files_to_group[metric_name][algorithm][beat_pos].append(metric_value)

    save_grouped_metrics(files_to_group, grouped_metric_file_path)


def group_metrics_for_splice_size_noise_level():
    metric_file_path = "data/latex_data/direct-metrics"
    grouped_metric_file_path = "data/latex_data/direct-metrics-grouped"

    files_to_group = {}
    for dirpath, subdir, filenames in os.walk(metric_file_path):
        for fn in filenames:
            metric_name = fn.split("-")[-1].split(".")[0]
            splice_size = fn.split("-")[0].split("_")[-1]
            noise_level = fn.split("-")[0].split("_")[1]
            files_to_group.setdefault(metric_name, {}).setdefault(noise_level, {}).setdefault(splice_size, [])

            with open(os.path.join(metric_file_path, fn), "r") as metric_file:
                metric_value = float(metric_file.readlines()[0])
            files_to_group[metric_name][noise_level][splice_size].append(metric_value)

    save_grouped_metrics(files_to_group, grouped_metric_file_path)


def group_metrics_for_algorithm_splice_size():
    metric_file_path = "data/latex_data/direct-metrics-per-alg"
    grouped_metric_file_path = "data/latex_data/direct-metrics-per-alg-grouped"

    files_to_group = {}
    for dirpath, subdir, filenames in os.walk(metric_file_path):
        for fn in filenames:
            metric = fn.split("--")[-1].split(".")[0]
            splice_size = fn.split("--")[0].split("_")[-1]
            algorithm = fn.split("--")[1]
            files_to_group.setdefault(metric, {}).setdefault(algorithm, {}).setdefault(splice_size, [])

            with open(os.path.join(metric_file_path, fn), "r") as metric_file:
                metric_value = float(metric_file.readlines()[0])
            files_to_group[metric][algorithm][splice_size].append(metric_value)

    save_grouped_metrics(files_to_group, grouped_metric_file_path)


def group_metrics_for_algorithm_and_beat_type():
    # transforms TP, FP, TN, FN to PPV Sens and Spec
    metric_file_path = "data/latex_data/paper-comparison-only-normal"
    grouped_metric_file_path = "data/latex_data/paper-comparison-only-normal-grouped"

    files_to_group = {}
    for dirpath, subdir, filenames in os.walk(metric_file_path):
        for fn in filenames:
            metric = fn.split("--")[-1].split(".")[0]
            algorithm = fn.split("--")[1]
            beat_type = fn.split("_")[0]
            files_to_group.setdefault(algorithm, {}).setdefault(metric, {}).setdefault(beat_type, [])

            with open(os.path.join(metric_file_path, fn), "r") as metric_file:
                metric_value = float(metric_file.readlines()[0])
            files_to_group[algorithm][metric][beat_type].append(metric_value)

    regrouped_files = group_submetrics(files_to_group)

    save_grouped_metrics(regrouped_files, grouped_metric_file_path)


def group_submetrics(files_to_group):
    regrouped_files = {}
    for alg, alg_vals in files_to_group.items():
        regrouped_files.setdefault(alg, {})
        regrouped_files[alg]["ME"] = files_to_group[alg]["ME"]
        tp_vals = alg_vals["TP"]
        fp_vals = alg_vals["FP"]
        tn_vals = alg_vals["TN"]
        fn_vals = alg_vals["FN"]
        for beat_type in tp_vals:
            regrouped_files[alg].setdefault("Spec", {}).setdefault(beat_type, [])
            regrouped_files[alg].setdefault("Sens", {}).setdefault(beat_type, [])
            regrouped_files[alg].setdefault("PPV", {}).setdefault(beat_type, [])
            for idx, metric_val in enumerate(tp_vals[beat_type]):
                regrouped_files[alg]["Spec"][beat_type].append(double_metric_compute(tn_vals[beat_type][idx],
                                                                                     fp_vals[beat_type][idx]))
                regrouped_files[alg]["Sens"][beat_type].append(double_metric_compute(tp_vals[beat_type][idx],
                                                                                     fn_vals[beat_type][idx]))
                regrouped_files[alg]["PPV"][beat_type].append(double_metric_compute(tp_vals[beat_type][idx],
                                                                                    fp_vals[beat_type][idx]))
    return regrouped_files


def double_metric_compute(a, b):
    if a == 0 and b == 0:
        return 1
    else:
        return a / (a + b)


if __name__ == '__main__':
    # group_metrics_for_algorithm_splice_size()
    # group_metrics_for_beat_position_algorithm()
    # group_metrics_by_splice_size()
    group_metrics_for_algorithm_and_beat_type()
