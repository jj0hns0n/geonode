$(function() {
    prepCustomizeForm();
    $("body").append("<div id=\"form-modal\" class=\"modal fade\"><div class=\"modal-body\"></div></div>");
      $(".btn-toolbar a.add").click(function (e) {
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
            if ($("#form-modal form#form-link-add").size() || 
              $("#form-modal form#form-document-add").size()) prepCategoryForm();
          });
      });
      $("#id_summary").wysihtml5();
});

function prepCustomizeForm() {
    $("#customize_form fieldset").each(function() {
        $(this).find("label").hide();
        var $n = $(this).find("input[name$='name']");
        var $v = $(this).find("input[name$='value']");
        $n.after("<span class=\"name\">"+$n.val()+"</span>").hide();
        if ($n.val().search("color") != -1) $v.miniColors();
        else if ($n.val().search("font") != -1) $v.fontSelector();
    });
    $("a.customize").bind("click", function(e) {
        e.preventDefault();
        $("#customize-modal").modal("show", {
            backdrop:true,
            keyboard:true
        });
    });
}

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