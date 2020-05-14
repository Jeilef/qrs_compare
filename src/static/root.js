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
    for(const metric_line in $metric){
        if($metric.hasOwnProperty(metric_line)){
            var m_line = $metric[metric_line];
            var vals = Object.values(m_line);
            var rounded_vals = vals.map(function (x) {
                 if(typeof(x) === "number"){
                     return x.toFixed(6);
                 }else{
                     return x;
                 }
            });
            while(rounded_vals.length < title_cols.length){
                rounded_vals.add(-1)
            }
            tab.row.add(rounded_vals).draw(false);
        }
    }
    // create Roc curve plot
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
    Plotly.newPlot('tester', data);
});
// make that filename is shown after file was selected
$(".custom-file-input").on("change", function() {
    const fileName = $(this).val().split("\\").pop();
    $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});