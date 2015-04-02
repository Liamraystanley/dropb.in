$(function() {
    // $('pre code').each(function(i, block) {
    //     hljs.highlightBlock(block);
    // });
    $('#text-input').focus();
    $('[data-toggle="tooltip"]').tooltip({
        container: 'body',
        placement: 'left'
    });
    $('[data-toggle="popover"]').popover({
        container: 'body',
        placement: 'left',
        html: true,
        content: '<a href="/login" class="btn btn-primary btn-md">Sign in using Github <i class="fa fa-github"></i></a>'
    });
});


/*--------------------------------------------/
/ Possibly something to use in the future, to /
/ make it so when using the textarea, it will /
/ show line #'s. Breaks atm because layout.   /
/--------------------------------------------*/
// $(function(){
//     $('#text-input').bind('input propertychange', function() {
//         var n_lines = $('#text-input').val().split('\n').length + 1;
//         var lines_data = '';
//         console.log(n_lines);
//         for (var i = 1; i < n_lines; i++) {
//             //$("#lines").append('<div>' + i + '.</div>');
//             var lines_data = lines_data.concat('<div>' + i + '.</div>');
//         };
//         console.log(lines_data);
//         $("#lines-edit").html(lines_data);
//     });
// });

function fetch(id) {
    $.ajax("/api/" + id, {
        type: "get",
        dataType: "json",
        success: function(data) {
            s = hljs.highlightAuto(data.paste);
            $("#box").html(s.value);
            // Add line numbers here
            for (var i = 0; i < data.lines; i++) {
                $("#lines").append('<a href="#' + (i + 1) + '"><div id="' + (i + 1) + '">' + (i + 1) + '.</div></a>');
            }
            $("#more-info").append("<span>" + s.language + "</span>");
            $("#more-info").append("<span>" + Number(data.lines).toLocaleString('en') + " lines</span>");
            $("#more-info").append("<span>" + Number(data.chars).toLocaleString('en') + " chars</span>");

            // As pre doesn't like to disable line wrapping, we're going to have to support it, due to the way the template is setup.
            // As such.. the best method is to split up the paste, find which lines are longer than the parent div, and append a <br>
            // to the line number id'd div. Slightly degrades performance on larger pastes.

            // Need to implement multiple-line splitting! Currently only works with ONE line!
            var id = 1;
            $($('#box').text().split('\n')).each(function(index, value) {
                id += 1;
                var measure = document.createElement("span");
                measure.innerText = value;
                measure.style.display = 'none';
                $('#box')[0].appendChild(measure);
                var linewidth = $(measure).width();
                if (linewidth >= $("#box").width()) {
                    $("#" + (id - 1)).html((id - 1) + '.' + '<br><br>');
                }
                // console.log(index + ": " + $(this).text());
            });
        },
        error: function(e) {
            $("#box").html('<div class="alert alert-danger" role="alert"><center>Unable to load the paste... <a href="/' + id + '" class="alert-link">Try to reload the page.</a></center></div>');
        }
    });
}
