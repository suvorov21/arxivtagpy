function renderCats() {
  CATS.forEach((cat, num) => {
    let parent = document.createElement("div");
    parent.setAttribute("class", "d-flex");

    let close = document.createElement("button");
    close.setAttribute("id", "close-"+cat);
    close.setAttribute("class", "close close-btn");
    close.innerHTML = "&times"

    let catElement = document.createElement("div");
    catElement.setAttribute("id", "cat-label-"+num);
    catElement.setAttribute("class", "pl-2");
    catElement.textContent = allCatsArray[cat];

    document.getElementById("cats-list").appendChild(parent);
    parent.appendChild(close);
    parent.appendChild(catElement);
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
  alert("Ha")
});