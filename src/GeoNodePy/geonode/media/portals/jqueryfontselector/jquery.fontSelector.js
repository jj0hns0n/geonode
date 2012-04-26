/**
* Font selector plugin
* turns an ordinary input field into a list of web-safe fonts
* Usage: $('select').fontSelector();
*
* Author     : James Carmichael
* Website    : www.siteclick.co.uk
* License    : MIT
*/
jQuery.fn.fontSelector = function(options) {

// S Swett added all these options 4/6/12; values below are defaults

options = $.extend({
inputElementId:"fontInput",
popupElementId:"fontPopup",
onChangeCallbackFunction:new Function(""),
fontsArray:new Array(
'Courier New=Courier New,Courier,monospace',
'Georgia=Georgia,serif',
'Helvetica=Helvetica Neue,Helvetica,Arial,sans-serif',
'Lucida Console=Lucida Console,Monaco,monospace',
'Lucida Sans Unicode=Lucida Sans Unicode,Lucida Grande,sans-serif',
'Palatino Linotype=Palatino Linotype,Book Antiqua,Palatino,serif',
'Tahoma=Tahoma,Geneva,sans-serif',
'Times New Roman=Times New Roman,Times,serif',
'Trebuchet MS=Trebuchet MS,Helvetica,sans-serif',
'Verdana=Verdana,Geneva,sans-serif')
}, options);

return this.each(function(){

// Get input field
var sel = this;

// Add a ul to hold fontsArray
var ul = $("<ul class=\"fontselector\"></ul>");
$('body').prepend(ul);
$(ul).hide();

jQuery.each(options.fontsArray, function(i, item) {
    var itemParts = item.split("=");
    var fontTitle = itemParts[0];
    var fontNameWithFallback = itemParts[1];

    var anchorId = options.inputElementId + "a" + i;

    // S Swett added "id" attribute below 4/6/12
    $(ul).append('<li><a href="#" id="'+anchorId+'" class="font_' + i + '" style="font-family: ' + fontNameWithFallback + '">' + fontTitle+ '</a></li>');

    // Prevent real select from working
    $(sel).focus(function(ev) {

    ev.preventDefault();

    // Show font list
    $(ul).show();

    // Position font list
    $(ul).css({ top: $(sel).offset().top + $(sel).height() + 4,
    left: $(sel).offset().left});

    // Blur field
    $(this).blur();
    return false;
    });

    $(ul).find('#' + anchorId).click(function(e) {
        e.preventDefault();
        var font = options.fontsArray[$(this).attr('class').split('_')[1]];
        var fontValue = font.split("=")[1];
        $(sel).val(fontValue);
        $(ul).hide();
        options.onChangeCallbackFunction(); // S Swett added this callback function 4/6/12
    });
});

});

};

