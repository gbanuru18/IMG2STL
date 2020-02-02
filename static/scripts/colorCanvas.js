var canvas;
var ctx;
var iActiveImage = 0;

$(document).ready(function(){

    canvas = document.getElementById('panel');
    ctx = canvas.getContext('2d');
    // drawing active image
    var image = new Image();
    image.onload = function () {
        var activeWidth = 400;
        var activeHeight = Math.floor((activeWidth*this.naturalHeight)/this.naturalWidth)
        canvas.width = activeWidth;
        canvas.height = activeHeight;
        ctx.drawImage(image, 0, 0, activeWidth, activeHeight); // draw the image on the canvas
    }
    image.src = images[iActiveImage];
    // creating canvas object
    $('#panel').mousemove(function(e) { // mouse move handler
        var canvasOffset = $(canvas).offset();
        var canvasX = Math.floor(e.pageX - canvasOffset.left);
        var canvasY = Math.floor(e.pageY - canvasOffset.top);
        var imageData = ctx.getImageData(canvasX, canvasY, 1, 1);
        var pixel = imageData.data;
        var pixelColor = "rgba("+pixel[0]+", "+pixel[1]+", "+pixel[2]+", "+pixel[3]+")";
        $('#preview').css('backgroundColor', pixelColor);
    });
    $('#panel').click(function(e) { // mouse click handler
        var canvasOffset = $(canvas).offset();
        var canvasX = Math.floor(e.pageX - canvasOffset.left);
        var canvasY = Math.floor(e.pageY - canvasOffset.top);
        var imageData = ctx.getImageData(canvasX, canvasY, 1, 1);
        var pixel = imageData.data;
        $('#rVal').val(pixel[0]);
        $('#gVal').val(pixel[1]);
        $('#bVal').val(pixel[2]);
        $('#rgbVal').val(pixel[0]+','+pixel[1]+','+pixel[2]);
        $('#rgbaVal').val(pixel[0]+','+pixel[1]+','+pixel[2]+','+pixel[3]);
        var dColor = pixel[2] + 256 * pixel[1] + 65536 * pixel[0];
        $('#hexVal').val( '#' + dColor.toString(16) );
    });
    $('#swImage').click(function(e) { // switching images
        image.src = images[iActiveImage];
    });
});