$('#form').submit(function(){
    var data = $(this).serialize();
    console.log(data)
    $.ajax({
        type: "POST",
        url: "go",
        dataType:"html",
        data: data,
        success: function(html){
            $('#answer').html(html);
        }
    });
    return false;
});
$('.collapse').collapse();