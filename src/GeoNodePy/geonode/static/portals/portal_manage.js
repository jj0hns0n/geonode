$(function() {
    $("body").append("<div id=\"form-modal\" class=\"modal fade\"><div class=\"modal-body\"></div></div>");
      $(".add,.edit").click(function (e) {
          e.preventDefault();
          $("#form-modal .modal-body").html("");
          var t = $(this).attr("href") + " #main";
          $('#form-modal .modal-body').load(t, function() {
            $("#form-modal").modal("show", {
                backdrop:true,
                keyboard:true
            });
            $("#form-modal .cancel").bind("click", function(e) {
                e.preventDefault();
                $("#form-modal").modal("hide");
            });
            if ($("#form-modal form#form-link-form").size() ||
              $("#form-modal form#form-document-form").size()) prepCategoryForm();
          });
      });
      $("form").delegate(".edit-inline", "click", function(e) {
        e.preventDefault();
        $(this).parents().eq(0).addClass("hide").siblings("div.field").delegate("button", "click", function(e) {
          e.preventDefault();
          var $form = $(this).parents("form");
          $.post($form.attr("action"), $form.serialize(), function(data) {
            $form.html($(data).find("form").html());
          });
        }).show().find("input,textarea").focus();
      });
});

function prepCategoryForm() {
  if ($("#id_parent option").size() > 1) {
      $("#id_parent").after(
          $("<a/>", {
              href: "#",
              "class": "category",
              html: "Create New Category",
              "click": function(e) {
                  e.preventDefault();
                  morphForm();
              }
          })
      );
  } else {
      morphForm();
  }
}
function morphForm() {
    $("#id_parent,#id_link,#id_file").parents("p").hide();
    $("label[for=id_label]").html("Description");
    $(".modal-body #main h1").each(function() {
      $(this).html($(this).html() + " Category");
    });
}