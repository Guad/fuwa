var oldPalette = ['blue-grey', 'teal'];
var ColorPalette = ['blue-grey', 'teal'];
// 0: Background 1: Buttons
$(document).ready(function(){
	var numberSelected = 0;

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
		$(this).html('<i class="small material-icons">done</i>');
		var classes = $(this).attr('class');
		var classesSplit = classes.split(' ');
		var color = classesSplit[1];
		ColorPalette.splice(0, 1)
		ColorPalette.push(color);
		numberSelected += 1;
		updateColors();
		//console.log(ColorPalette);
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