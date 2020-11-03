function addCat(cat) {
  let parent = document.createElement("div");
  parent.setAttribute("class", "d-flex");
  parent.setAttribute("id", "par-cat-"+cat.replaceAll(".", "-"))

  let close = document.createElement("button");
  close.setAttribute("id", "close_"+cat.replaceAll(".", "-"));
  close.setAttribute("class", "close close-btn");
  close.innerHTML = "&times"

  close.onclick = function(event) {
    $("#par-cat-"+event.target.getAttribute("id").split("_")[1]).removeClass("d-flex");
    $("#par-cat-"+event.target.getAttribute("id").split("_")[1]).fadeOut();
    $(".btn").removeClass("disabled");
    // TODO remove from array
  }

  let catElement = document.createElement("div");
  catElement.setAttribute("class", "pl-2");
  catElement.textContent = allCatsArray[cat];

  document.getElementById("cats-list").appendChild(parent);
  parent.appendChild(close);
  parent.appendChild(catElement);
}

function renderCats() {
  CATS.forEach((cat, num) => {
    addCat(cat);
  });
}

window.onload = function(event) {
  $.each(allCatsArray, function(val, text) {
    $("#catsDataList").append($("<option>").attr("value", val).text(text));
  });

  renderCats();
}

function validateCat() {
  if (document.forms["add-cat"]["cat-add-input"].value === "") {
    return false;
  }

  return true;
}

$("#add-cat-btn").click((event) => {
  cat = document.forms["add-cat"]["cat_name"].value;
  // TODO add check if not already
  if (allCatsArray[cat] !== undefined) {
    $(".btn").removeClass("disabled");
    addCat(document.forms["add-cat"]["cat_name"].value);
    document.forms["add-cat"]["cat_name"].value = "";
    // TODO add to array

  }
});

$("#btn-cancel").click((event) => {
  location.reload();
});