var jar = document.cookie;
var cookies = jar.split(';');
var oldPalette = ['blue-grey', 'teal'];
var ColorPalette = ['blue-grey', 'teal'];
// 0: Background 1: Buttons

var hasBgColor = (new RegExp("(?:^|;\\s*)" + encodeURIComponent('bgColor').replace(/[\-\.\+\*]/g, "\\$&") + "\\s*\\=")).test(document.cookie);
var hasBtnColor = (new RegExp("(?:^|;\\s*)" + encodeURIComponent('btnColor').replace(/[\-\.\+\*]/g, "\\$&") + "\\s*\\=")).test(document.cookie);

if(hasBtnColor && hasBgColor) {
	var bgColor = document.cookie.replace(/(?:(?:^|.*;\s*)bgColor\s*\=\s*([^;]*).*$)|^.*$/, "$1");
	var btnColor = document.cookie.replace(/(?:(?:^|.*;\s*)btnColor\s*\=\s*([^;]*).*$)|^.*$/, "$1");
	ColorPalette.length = 0;
	ColorPalette.push(bgColor);
	ColorPalette.push(btnColor);
}

$(document).ready(function(){
	var numberSelected = 0;
	updateColors();	

	$('#button-palette').click(function(){
		$('#palette-main').fadeToggle();
	});

	$('.palette-box').click(function(){
		if(numberSelected >= 2) {
			numberSelected = 0;
			$('.palette-box').each(function() {
				$(this).html('');
			});
		}
		$(this).html('<i class="small">X</i>');
		var classes = $(this).attr('class');
		var classesSplit = classes.split(' ');
		var color = classesSplit[1];
		ColorPalette.splice(0, 1)
		ColorPalette.push(color);
		numberSelected += 1;
		updateColors();

		document.cookie = 'bgColor=' + ColorPalette[0] + '; expires=Fri, 31 Dec 9999 23:59:59 GMT; path=/';
		document.cookie = 'btnColor=' + ColorPalette[1] + '; expires=Fri, 31 Dec 9999 23:59:59 GMT; path=/';
	});
});

function updateColors() {
	$('.card').each(function() {
		$(this).removeClass(oldPalette[0]);
		$(this).addClass(ColorPalette[0]);
	});

	$('.btn').each(function() {
		$(this).removeClass(oldPalette[1]);
		$(this).addClass(ColorPalette[1]);
	});

	oldPalette = ColorPalette.slice(0);
}