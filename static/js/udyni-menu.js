$(document).ready(function() {

  // Get current location
  var current_location = window.location.pathname;

  // Search for all
  $("#accordionSidebar a.collapse-item").each(function() {
    if($(this).attr('href') != "") {
      //console.log("L:"+current_location+", H:"+$(this).attr('href'));
      if(current_location.startsWith($(this).attr('href'))) {
        // Found location
        $(this).addClass('active');
        $(this).closest("div.collapse").addClass('show');
        $(this).closest("li.nav-item").addClass('active');
      }
    }
  });
});
