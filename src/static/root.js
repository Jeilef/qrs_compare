$(document).ready( function () {
    var roc_vals = [];
    var title_cols = new Set();
    var titles = [];
    // find table cols
    for(const metric_line in $metric){
        if($metric.hasOwnProperty(metric_line)){
            const m_line = $metric[metric_line];
            /*if(m_line.hasOwnProperty("RoC")){
                roc_vals.push(m_line.RoC);
                delete m_line.RoC;
            }*/
            Object.keys(m_line).forEach(function (a) {
                title_cols.add(a);
            })
        }
    }
    title_cols.forEach(function (x) {
        titles.push({"title": x});
    })
    // set table cols
    const tab = $('#results-table').DataTable({
        "data": [],
        "columns": titles
    });
    // insert vals into table
    var data_points_for_box_plots = {};
    for(const metric_line in $metric){
        if($metric.hasOwnProperty(metric_line)){
            var m_line = $metric[metric_line];
            var alg_name = m_line.Name;
            var vals = Object.entries(m_line);
            var prepared_vals = vals.map(function (x) {
                // split up data per datatype
                if(x[0] === "Name"){
                    return x[1];
                }
                var keys_per_datatype = Object.keys(x[1]);
                var vals_per_datatype = Object.values(x[1]);
                 if(typeof(x) === "number"){
                     return x.toFixed(6);
                 }else{
                     data_points_for_box_plots["box-plot-" + x[0] + alg_name] = vals_per_datatype;
                     return "<div id='box-plot-" + x[0] + alg_name + "'></div>";
                 }
            });
            while(prepared_vals.length < title_cols.length){
                prepared_vals.add(-1)
            }
            tab.row.add(prepared_vals).draw(false);
        }
    }
    create_boxplots_for_datapoints(data_points_for_box_plots);
    // create Roc curve plot
    /*
    console.log(roc_vals);
    var data = [];
    roc_vals.forEach(function (rv) {
        var trace = {
            x: rv.map(function (x) {
                return x[1]
            }),
            y: rv.map(function (x) {
                return x[0]
            }),
            mode: 'lines+markers'
        };
        data.push(trace);
    });
    Plotly.newPlot('tester', data);*/
});
// make that filename is shown after file was selected
$(".custom-file-input").on("change", function() {
    const fileName = $(this).val().split("\\").pop();
    $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});

function create_boxplots_for_datapoints(datapoints){
    const all_between_0_and_1 = Object.values(datapoints).every(function (x) {
        return x < 0.5 || x > 1;
    });
    console.log(all_between_0_and_1);
    Object.entries(datapoints).forEach(function(entry){
        const trace1 = {
            y: entry[1],
            type: 'box',
            name: ''
        };
        const data = [trace1];
        if(all_between_0_and_1){
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
        }else {
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
