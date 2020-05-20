function accumulate_line_values(vals_per_datatype) {
    vals_per_datatype = vals_per_datatype.map(function (x) {
        return parseFloat(x);
    })
    var sorted_vals = vals_per_datatype.sort((a, b) => a - b);
    const len_sor = sorted_vals.length;
    let q1 = sorted_vals[(len_sor / 4).toFixed() - 1];
    let q2 = sorted_vals[(2 * len_sor / 4).toFixed() - 1];
    let q3 = sorted_vals[(3 * len_sor / 4).toFixed() - 1];
    //data_points_for_box_plots["box-plot-" + x[0] + alg_name] = vals_per_datatype;
    //return "<div id='box-plot-" + x[0] + alg_name + "'></div>";

    if (typeof (q1) === "number") {
        return [q1.toFixed(4),
            q2.toFixed(4),
            q3.toFixed(4)]
    } else {
        // is a roc value
    }
}

function map_to_table_format(data_vals) {
    console.log(data_vals)
    var acc_line = []
    acc_line.push(data_vals[0][0]) // name of the algorithm
    for (var idx = 2; idx < data_vals[0].length; idx++) {
        if (data_vals[0][idx] != null) {
            var vals_per_datatype = []
            data_vals.forEach(function (x) {
                vals_per_datatype.push(x[idx]);
            })
            console.log("vals per datatype", vals_per_datatype)
            acc_line.push(accumulate_line_values(vals_per_datatype))
        }
    }
    return acc_line.flat();
}

function spead_data_for_detail_rows(vals) {
    var lines = [];
    for (var i = 0; i < Object.values(vals[1][1]).length; i++) {
        var line = []
        line.push(vals[0][1]);
        line.push(Object.keys(Object.values(vals[1])[1])[i]);
        for (var j = 1; j < vals.length; j++) {
            let metric_value_one_set = Object.values(vals[j][1]);
            let metric_value = metric_value_one_set[i];
            line.push(null)
            line.push(metric_value.toFixed(6))
            line.push(null)
        }
        lines.push(line);
    }
    return lines;
}

var create_boxplots = function create_boxplots_for_datapoints(datapoints) {
    const all_between_0_and_1 = Object.values(datapoints).every(function (x) {
        return x < 0.5 || x > 1;
    });
    console.log(all_between_0_and_1);
    Object.entries(datapoints).forEach(function (entry) {
        const trace1 = {
            y: entry[1],
            type: 'box',
            name: ''
        };
        const data = [trace1];
        if (all_between_0_and_1) {
            var layout = {
                title: '',
                yaxis: {
                    range: [0, 1]
                },
                margin: {
                    l: 20,
                    r: 0,
                    b: 20,
                    t: 0
                }
            };
        } else {
            var layout = {
                title: '',
                margin: {
                    l: 20,
                    r: 0,
                    b: 20,
                    t: 0
                }
            };
        }
        Plotly.newPlot(entry[0], data, layout);
    })
}

export { create_boxplots }
