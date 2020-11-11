var catNew = [];

function addCat(cat) {
  // Dots replace with 111 to be a legal
  // name for JS elements
  // TODO proper escape dot with \\.
  let parent = document.createElement("div");
  parent.setAttribute("class", "d-flex");
  parent.setAttribute("id", "par-cat-"+cat.replaceAll(".", "111"))

  let close = document.createElement("button");
  close.setAttribute("id", "close_"+cat.replaceAll(".", "111"));
  close.setAttribute("class", "close close-btn");
  close.innerHTML = "&times"

  close.onclick = function(event) {
    let name = event.target.getAttribute("id").split("_")[1]
    $("#par-cat-" + name).removeClass("d-flex");
    $("#par-cat-" + name).fadeOut();
    $(".btn").removeClass("disabled");
    const catId = catNew.indexOf(name.replace("111", "."));
    if (catId > -1) {
      catNew.splice(catId, 1);
    }
  }

  let catElement = document.createElement("div");
  catElement.setAttribute("class", "pl-2");
  catElement.textContent = allCatsArray[cat];

  document.getElementById("cats-list").appendChild(parent);
  parent.appendChild(close);
  parent.appendChild(catElement);
}

function renderCats() {
  $("#cats-list").empty();
  catNew = [];
  CATS.forEach((cat, num) => {
    // TODO consider moving function inline?
    addCat(cat);
    catNew.push(cat);
  });
}

function renderTags() {
  TAGS.forEach((tag, num) => {
    let tagElement = document.createElement("div");
    tagElement.setAttribute("class", "tag-label");
    tagElement.setAttribute("id", "tag-label-"+num);
    tagElement.setAttribute("style", "background-color: " + tag.color);
    tagElement.textContent = tag.name;
    document.getElementById("tag-list").appendChild(tagElement);
  });
  if (parseTex) {
    MathJax.typesetPromise();
  }
}

function renderPref() {

}

function reloadSettings() {
  if (CATS !== catNew) {
    renderCats();
  }
  renderTags();
  renderPref();
}

window.onload = function(event) {
  $.each(allCatsArray, function(val, text) {
    $("#catsDataList").append($("<option>").attr("value", val).text(text));
  });

  reloadSettings()
}

function fillCatForm() {
  if ($(".btn-cancel").hasClass("disabled")) {
    return false;
  }
  let hiddenText = document.createElement("input");
  hiddenText.setAttribute("type", "text");
  hiddenText.setAttribute("name", "catNew");
  hiddenText.setAttribute("style", "display: none;");
  hiddenText.value = catNew.toString();

  document.forms["mod-cat"].appendChild(hiddenText);
  return true;
}

$("#add-cat-btn").click((event) => {
  cat = document.forms["add-cat"]["cat_name"].value;
  // check if already there
  if (catNew.includes(cat)) {
    alert("Catagory already added!");
    return;
  }
  // check if legal category
  if (allCatsArray[cat] === undefined) {
    alert("Unknown category");
    return;
  }
  $(".btn-save").removeClass("disabled");
  addCat(document.forms["add-cat"]["cat_name"].value);
  document.forms["add-cat"]["cat_name"].value = "";
  // add to array
  catNew.push(cat);
});

$(".btn-cancel").click((event) => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    location.reload();
  }
});

$(".nav-link").click((event) => {
  if (!$(".btn-cancel").hasClass("disabled")) {
    if (confirm("Settings will not be saved. Continue?")) {
      $(".btn-save").addClass("disabled");
      reloadSettings();
      event.preventDefault();
    } else {
      event.preventDefault();
      return;
    }
  }
  $("#cats-set").css("display", "none");
  $("#tags-set").css("display", "none");
  $("#pref-set").css("display", "none");

  $("#cats-link").removeClass("active");
  $("#tags-link").removeClass("active");
  $("#pref-link").removeClass("active");

  $("#" + event.target.getAttribute("id").split("-")[0] + "-set").css("display", "block");
  $(event.target).addClass("active");
});