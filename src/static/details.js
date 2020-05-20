let chart_num = 0;

function ppv_chart() {
    const data = create_trace_for_metric($metric.PPV);
    console.log("ppv", data)
    const layout = {
        title: 'PPV values per beat type',
        width: 1500,
        height: 500,
        barmode: 'stack',
        showlegend: true,
        legend: {
            x: 1,
            y: 0.5
        }
    };
    Plotly.newPlot('bar-chart-ppv', data, layout);
}

function sens_chart() {
    const data = create_trace_for_metric($metric.Sens);
    const layout = {
        title: 'Sensitivity values per beat type',
        barmode: 'stack',
        width: 1500,
        height: 500,
        showlegend: true,
        legend: {
            x: 1,
            y: 0.5,
            xanchor: 'left'
        }
    };
    Plotly.newPlot('bar-chart-sens', data, layout);
}

function f1_chart() {
    const data = create_trace_for_metric($metric["F1 Score"]);
    const layout = {
        title: 'F1 Score values per beat type',
        barmode: 'stack',
        width: 1500,
        height: 500,
        showlegend: true,
        legend: {
            x: 1,
            y: 0.5,
            xanchor: 'left'
        }
    };
    Plotly.newPlot('bar-chart-f1', data, layout);
}

function me_chart() {
    const data = create_trace_for_metric($metric["ME"]);
    const layout = {
        title: 'Mean Error per beat type',
        barmode: 'stack',
        width: 1500,
        height: 500,
        showlegend: true,
        legend: {
            x: 1,
            y: 0.5,
            xanchor: 'left'
        }
    };
    Plotly.newPlot('bar-chart-me', data, layout);
}

function mse_chart() {
    const data = create_trace_for_metric($metric["MSE"]);
    const layout = {
        title: 'Mean Squared Error per beat type',
        barmode: 'stack',
        width: 1500,
        height: 500,
        showlegend: true,
        legend: {
            x: 1,
            y: 0.5,
            xanchor: 'left'
        }
    };
    Plotly.newPlot('bar-chart-mse', data, layout);
}

function mae_chart() {
    const data = create_trace_for_metric($metric["MAE"]);
    const layout = {
        title: 'Mean Squared Error per beat type',
        barmode: 'stack',
        width: 1500,
        height: 500,
        showlegend: true,
        legend: {
            x: 1,
            y: 0.5,
            xanchor: 'left'
        }
    };
    Plotly.newPlot('bar-chart-mae', data, layout);
}

$(document).ready(function () {
    ppv_chart();
    sens_chart();
    f1_chart()
    me_chart()
    mse_chart()
    mae_chart()
})

function create_trace_for_metric(metric){
    chart_num++;
    const sorted_values = sort_metric_values(metric);
    const names = sorted_values[0];
    const metric_values = sorted_values[1];
    var data = [];
    const values_to_str = metric_values.map((x) => String(x.toFixed(4)));
    names.forEach(function (x, i) {
        var trace = {
            name: names[i] + ": " + map_beat_type_to_description(names[i]),
            x: [x],
            y: [metric_values[i]],
            xaxis: "x" + String(chart_num),
            yaxis: "y" + String(chart_num),
            type: 'bar',
            text: values_to_str[i],
            textposition: 'auto',
            hoverinfo: 'none',
            marker: {
                color: 'rgb(158,202,225)',
                opacity: 0.6,
                line: {
                    color: 'rgb(8,48,107)',
                    width: 1.5
                }
            }
        }
        data.push(trace);
    })
    return data
}

function sort_metric_values(metric_values){
    const sorted_entries = Object.entries(metric_values)
        .sort((a, b) => parseFloat(b[1]) -  parseFloat(a[1]))
    const names = sorted_entries.map((a) => a[0])
    const values = sorted_entries.map((a) => a[1])
    return [names, values]
}

function map_beat_type_to_description(beat_type){
    var description = ""
    Object.entries($code_mapping).forEach(function (x) {
        if(beat_type === x[0]){
            description = x[1]
        }
    })
    return description
}
