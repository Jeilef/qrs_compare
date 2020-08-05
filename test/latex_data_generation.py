import os


def group_metrics_by_splice_size():
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

    os.makedirs(grouped_metric_file_path, exist_ok=True)
    for metric_name, grouped_metrics in files_to_group.items():
        for noise_level, noise_metric_vals in grouped_metrics.items():
            save_str = ""
            grouped_metric_file_name = "{}-{}.dat".format(metric_name, noise_level)
            abs_file_path = os.path.join(grouped_metric_file_path, grouped_metric_file_name)

            for splice_size, metric_vals in noise_metric_vals.items():
                summed_val = sum(metric_vals) / len(metric_vals)
                save_str += "{} {}\n".format(splice_size, summed_val)
            with open(abs_file_path, "w") as grouped_metric_file:
                grouped_metric_file.write(save_str)


def group_metrics_by_beat_position():
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

    os.makedirs(grouped_metric_file_path, exist_ok=True)
    for metric_name, grouped_metrics in files_to_group.items():
        for alg, alg_vals in grouped_metrics.items():
            save_str = ""
            grouped_metric_file_name = "{}-{}.dat".format(metric_name, alg)
            abs_file_path = os.path.join(grouped_metric_file_path, grouped_metric_file_name)

            for beat_pos, metric_vals in alg_vals.items():
                summed_val = sum(metric_vals) / len(metric_vals)
                save_str += "{} {}\n".format(beat_pos, summed_val)
            with open(abs_file_path, "w") as grouped_metric_file:
                grouped_metric_file.write(save_str)


if __name__ == '__main__':
    group_metrics_by_beat_position()
    # group_metrics_by_splice_size()
