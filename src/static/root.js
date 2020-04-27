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
    console.log(titles)
    const tab = $('#results-table').DataTable({
        "data": [],
        "columns": titles
    });
    for(const metric_line in $metric){
        if($metric.hasOwnProperty(metric_line)){
            const m_line = $metric[metric_line];
            tab.row.add([
            m_line.name,
            m_line.tp,
            m_line.fp,
            m_line.fn
            ]).draw(false);
        }
    }
} );

$(".custom-file-input").on("change", function() {
    const fileName = $(this).val().split("\\").pop();
    $(this).siblings(".custom-file-label").addClass("selected").html(fileName);
});