$(document).ready( function () {
    var title_cols = new Set();
    var titles = [];
    for(const metric_line in $metric){
        if($metric.hasOwnProperty(metric_line)){
            const m_line = $metric[metric_line];
            Object.keys(m_line).forEach(function (a) {
                title_cols.add(a);
            })
        }
    }
    title_cols.forEach(function (x) {
        titles.push({"title": x});
    })
    const tab = $('#results-table').DataTable({
        "data": [],
        "columns": titles
    });
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
} );

$(".custom-file-input").on("change", function() {
    const fileName = $(this).val().split("\\").pop();
    $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});