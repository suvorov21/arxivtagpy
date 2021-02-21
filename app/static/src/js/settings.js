/*global allCatsArray, CATS, TAGS, PREF, parseTex, MathJax*/
/*eslint no-undef: "error"*/

// ************************** UTILS ********************************************
function raiseAlert(text="Text", type="alert") {
  let parent = document.createElement("div");
  parent.setAttribute("class", "alert alert-dismissible fade show alert-" + type);
  parent.setAttribute("role", "alert");

  let content = document.createElement("span");
  content.textContent = text;

  let close = document.createElement("button");
  close.setAttribute("class", "close");
  close.setAttribute("data-dismiss", "alert");
  close.setAttribute("aria-label", "Close");

  let time = document.createElement("span");
  time.innerHTML = "&times;";

  document.body.insertBefore(parent, document.getElementById("main-container"));
  parent.appendChild(content);
  parent.appendChild(close);
  close.appendChild(time);
}

var dragTarget;
var tagEdited = false;

// ************************  RENDERS *******************************************
function addCat(cat) {
  // Dots replace with 111 to be a legal
  // name for JS elements
  // TODO proper escape dot with \\.
  let parent = document.createElement("div");
  parent.setAttribute("class", "d-flex cat-parent");
  parent.setAttribute("id", "par-cat-"+cat.replaceAll(".", "111"));
  parent.draggable = true;

  parent.ondragstart = function(event) {
    let moved = event.target.getAttribute("id").split("-").slice(2);
    moved = moved.join("-").replaceAll("111", ".");
    event.dataTransfer.setData("Text", moved);
  };

  parent.ondragover = function(event) {
    let target = event.target.getAttribute("id").split("-").slice(2);
    dragTarget = target.join("-").replaceAll("111", ".");
  };

  let close = document.createElement("button");
  close.setAttribute("id", "close_"+cat.replaceAll(".", "111"));
  close.setAttribute("class", "close close-btn");
  close.innerHTML = "&times";

  close.onclick = function(event) {
    let name = event.target.getAttribute("id").split("_")[1];
    $("#par-cat-" + name).removeClass("d-flex");
    $("#par-cat-" + name).fadeOut();
    $(".btn").removeClass("disabled");
    const catId = CATS.indexOf(name.replace("111", "."));
    if (catId > -1) {
      CATS.splice(catId, 1);
    }
  };

  let catElement = document.createElement("div");
  catElement.setAttribute("class", "pl-2");
  catElement.setAttribute("id", "cat-name-" + cat.replaceAll(".", "111"));
  catElement.textContent = allCatsArray[cat];

  document.getElementById("cats-list").appendChild(parent);
  parent.appendChild(close);
  parent.appendChild(catElement);
}

function renderCats() {
  $("#cats-list").empty();
  CATS.forEach((cat) => {
    addCat(cat);
  });

  document.getElementById("cats-list").ondragover = function(event) {
    event.preventDefault();
  };
  document.getElementById("cats-list").ondrop = function(event) {
    event.preventDefault();
    let moved = event.dataTransfer.getData("Text");
    let movedId = CATS.indexOf(moved);
    let targetId = CATS.indexOf(dragTarget);
    CATS[parseInt(movedId, 10)] = dragTarget;
    CATS[parseInt(targetId, 10)] = moved;

    $(".btn").removeClass("disabled");
    reloadSettings();
  };
}

const findTagIdByName = (name) => {
  for (let tagId = 0; tagId < TAGS.length; tagId++) {
    if (TAGS[tagId]["name"] === name) {
      return tagId;
    }
  }
  return -1;
}

function renderTags() {
  $("#tag-list").empty();
  TAGS.forEach((tag, num) => {
    let tagElement = document.createElement("div");
    tagElement.setAttribute("class", "tag-label");
    tagElement.setAttribute("id", "tag-label-"+tag.name);
    tagElement.setAttribute("style", "background-color: " + tag.color);
    tagElement.draggable = true;
    tagElement.textContent = tag.name;
    document.getElementById("tag-list").appendChild(tagElement);

    tagElement.ondragstart = function(event) {
      if (tagEdited) {
        event.preventDefault();
        return;
      }
      let moved = event.target.getAttribute("id").split("-").slice(2);
      moved = moved.join("-").replaceAll("111", "-");
      moved = findTagIdByName(moved);
      event.dataTransfer.setData("Text", moved);
    };

    tagElement.ondragover = function(event) {
      let target = event.target.getAttribute("id").split("-").slice(2);
      dragTarget = target.join("-").replaceAll("111", "-");
      dragTarget = findTagIdByName(dragTarget);
    };
  });

  document.getElementById("tag-list").ondragover = function(event) {
    event.preventDefault();
  }

  document.getElementById("tag-list").ondrop = function(event) {
    event.preventDefault();
    let moved = event.dataTransfer.getData("Text");
    let movedId = parseInt(moved, 10);
    let targetId = parseInt(dragTarget, 10);
    let buffer = TAGS[parseInt(movedId, 10)];
    TAGS[parseInt(movedId, 10)] = TAGS[parseInt(targetId, 10)];
    TAGS[parseInt(targetId, 10)] = buffer;

    $(".btn").removeClass("disabled");
    reloadSettings();
  }

  if (parseTex) {
    MathJax.typesetPromise();
  }
  // new tag button
  let tagElement = document.createElement("div");
  tagElement.setAttribute("class", "add-set tag-label");
  tagElement.setAttribute("id", "add-tag");
  tagElement.textContent = "+New";

  document.getElementById("tag-list").appendChild(tagElement);
}

function renderPref() {
  if (PREF["tex"]) {
    document.getElementById("tex-check").checked = true;
  }

  // if (PREF["easy_and"]) {
  //   document.getElementById("and-check").checked = true;
  // }
  return;
}

function reloadSettings() {
  if ($("#cats-link").hasClass("active")) {
    renderCats();
  }
  else if ($("#tags-link").hasClass("active")) {
    renderTags();
    document.forms["add-tag"]["tag_name"].value = "";
    document.forms["add-tag"]["tag_rule"].value = "";
    document.forms["add-tag"]["tag_color"].value = "";
  }
  else if ($("#pref-link").hasClass("active")) {
    renderPref();
  }
}

window.onload = function() {
  $.each(allCatsArray, function(val, text) {
    $("#catsDataList").append($("<option>").attr("value", val).text(text));
  });

  reloadSettings();
};

// ******************** CATEGORIES *********************************************
function submitCat() {
  let url = "mod_cat";
  $.post(url, {"list": CATS})
  .done(function() {
    CATS = Array.from(CATS);
    reloadSettings();
    $(".btn-save").addClass("disabled");
    raiseAlert("Settings are saved", "success");
    return false;
  }).fail(function(){
    raiseAlert("Settings are not saved. Please try later", "danger");
    return false;
  });
  return false;
}

function fillCatForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  submitCat();
  return false;
}

$("#add-cat-btn").click(() => {
  let cat = document.forms["add-cat"]["cat_name"].value;
  // check if already there
  if (CATS.includes(cat)) {
    alert("Catagory already added!");
    return;
  }
  // check if legal category
  if (typeof(allCatsArray[cat]) === "undefined") {
    alert("Unknown category");
    return;
  }
  $(".btn-save").removeClass("disabled");
  addCat(document.forms["add-cat"]["cat_name"].value);
  document.forms["add-cat"]["cat_name"].value = "";
  // add to array
  CATS.push(cat);
});

$(".btn-cancel").click(() => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    location.reload();
  }
});

// ****************** TAGS *****************************************************
$("#show-rules").click(() => {
  if ($("#tag-help").css("display") === "block") {
    $("#tag-help").css("display", "none");
  } else {
    $("#tag-help").css("display", "block");
  }
});

// TODO consider how to get rid of it
var newTag = true;
var editTagId = -1;

$("#tag-list").click((event) => {
  // consider only tag labels click
  if (typeof($(event.target).attr("class")) === "undefined" ||
      !$(event.target).attr("class").includes("tag-label")) {
    return;
  }

  // check if settings were modified
  if (tagEdited) {
    event.preventDefault();
    return;
  }

  // reset the highlignt of all other tags
  let tagCol = document.getElementsByClassName("tag-label");
  for (let id = 0; id < tagCol.length; id++) {
    // existing tags
    $("#tag-label-"+parseInt(id, 10)).css("border-color", "transparent");
    // new tag box
    if ($(tagCol[parseInt(id, 10)]).attr("id") === "add-tag") {
      $("#add-tag").css("border-style", "dashed");
      $("#add-tag").css("border-width", "2px");
    }
  }

  // highlight the editable tag
  $(event.target).css("border-color", "#000");

  if ($(event.target).attr("id") === "add-tag") {
    // TODO consider how to get rif of it
    newTag = true;

    $("#btn-reset").click();
    $("#add-tag").css("border-style", "solid");
    $("#add-tag").css("border-width", "4px");
    document.forms["add-tag"]["tag_name"].value = "";
    document.forms["add-tag"]["tag_rule"].value = "";
    document.forms["add-tag"]["tag_color"].value = "";
  } else {
    // TODO consider how to get rif of it
    newTag = false;

    let editTagName = $(event.target).attr("id").split("-").slice(2);
    editTagName = editTagName.join("-");
    editTagId = findTagIdByName(editTagName);
    let tag = TAGS[parseInt(editTagId, 10)];


    $("#tag-fields").prop("disabled", false);
    document.forms["add-tag"]["tag_name"].value = tag.name;
    document.forms["add-tag"]["tag_rule"].value = tag.rule;
    document.forms["add-tag"]["tag_color"].value = tag.color;
    $("#tag-color").css("background-color", $("#tag-color").val());

    // make delete possible
    $("#btn-del").removeClass("disabled");
  }
  $("#tag-fields").prop("disabled", false);
});

function makeTagEdited() {
  $(".btn-save").removeClass("disabled");
  tagEdited = true;
  var doms = document.getElementsByClassName("tag-label");
  for(let i = 0; i < doms.length; i++) {
    doms[parseInt(i, 10)].style.cursor = "not-allowed";
  }
}

$(".tag-field").on("input", function() {
  makeTagEdited();
});

// TODO should I delete onimput listener?!
$(".tag-field").on("change", function() {
  makeTagEdited();
});

$("#tag-color").on("change", function() {
  $("#tag-color").css("background-color", $("#tag-color").val());
  $(".btn-save").removeClass("disabled");
});

function submitTag() {
  let url = "mod_tag";
  $.post(url, JSON.stringify(TAGS))
  .done(function() {
    reloadSettings();
    $(".btn-save").addClass("disabled");
    $("#btn-del").addClass("disabled");
    tagEdited = false;
    raiseAlert("Settings are saved", "success");
    return true;
  }).fail(function(){
    raiseAlert("Settings are not saved. Please try later", "danger");
    return false;
  });
}

function checkTag() {
  $(".cat-alert").empty();
  // in case of simple replacement no check required
  if (!tagEdited) {
    submitTag();
    return true;
  }

  // check all fields are filled
  if (document.forms["add-tag"]["tag_name"].value === "" ||
      document.forms["add-tag"]["tag_rule"].value === "" ||
      document.forms["add-tag"]["tag_color"].value === "") {
    $(".cat-alert").html("Fill all the fields in the form!");
    return false;
  }

  if (findTagIdByName(document.forms["add-tag"]["tag_name"]) !== -1) {
    $(".cat-alert").html("Tag with this name already exists. Consider a unique name!");
    return false;
  }

  // check rule
  let rule = document.forms["add-tag"]["tag_rule"].value;
  if (!/^(ti|au|abs){.*?}((\||\&)(\(|)((ti|au|abs){.*?})(\)|))*$/i.test(rule)) {
    $(".cat-alert").html("Check the rule syntax!");
    return false;
  }

  // check color
  if (!/^#[0-9A-F]{6}$/i.test(document.forms["add-tag"]["tag_color"].value)) {
    $(".cat-alert").html("Color should be in hex format: e.g. #aaaaaa");
    return false;
  }

  // tag rules are checked
  let TagDict = {"name": document.forms["add-tag"]["tag_name"].value,
                 "rule": document.forms["add-tag"]["tag_rule"].value,
                 "color": document.forms["add-tag"]["tag_color"].value
               };
  if (!newTag) {
    TAGS[parseInt(editTagId, 10)]["name"] = TagDict["name"];
    TAGS[parseInt(editTagId, 10)]["rule"] = TagDict["rule"];
    TAGS[parseInt(editTagId, 10)]["color"] = TagDict["color"];
  } else {
    TAGS.push(TagDict);
  }

  submitTag();
}

function fillTagForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  checkTag();
  return false;
}

$("#btn-del").click((event) => {
  if (newTag || $("#btn-del").hasClass("disabled")) {
    event.preventDefault();
    return;
  }
  if (confirm("Are you sure you want to delete " + TAGS[parseInt(editTagId, 10)].name + "?")) {
    TAGS.splice(editTagId, 1);
    submitTag();
    event.preventDefault();
  } else {
    event.preventDefault();
    return;
  }
});

// ***************** PREFERENCES ***********************************************
$(".form-check-input").change(() => {
  $(".btn-save").removeClass("disabled");
});

function fillSetForm() {
  let url = "mod_pref";
  let dataSet = {"tex": document.getElementById("tex-check").checked
                  // "easy_and": document.getElementById("and-check").checked
                };
  $.post(url, JSON.stringify(dataSet))
  .done(function(data) {
    reloadSettings();
    $(".btn-save").addClass("disabled");
    raiseAlert("Settings are saved", "success");
    return false;
  }).fail(function(jqXHR){
    raiseAlert("Settings are not saved. Please try later", "danger");
    return false;
  });

  return false;
}

function changePasw() {
  return true;
}

function delAcc() {
  if (confirm("Do you want to delete account completely? This action could not be undone!")) {
    return true;
  } else {
    return false;
  }
}

// ************** NAVIGATION ***************************************************
$(".nav-link").click((event) => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    if (confirm("Settings will not be saved. Continue?")) {
      return;
    } else {
      event.preventDefault();
      return;
    }
  }
});

// ask fo settings save on leave
// BUG seems to be useless
// window.onbeforeunload = function(event) {
//   if (!$(".btn-cancel").hasClass("disabled")) {
//     if (confirm("Settings will not be saved. Continue?")) {
//       return true;
//     } else {
//       event.preventDefault();
//       return true;
//     }
//   }
// };
