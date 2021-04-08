/*global MathJax, parseTex, DATA, LISTS, raiseAlert, renderPapersBase*/
/*eslint no-undef: "error"*/

function renderLists() {
  LISTS.forEach((listName, num) => {
    let listItem = document.createElement("div");
    listItem.className = "menu-item-bm";
    let link = document.createElement("a");
    // TODO
    link.href = "/";
    link.textContent = listName;
    document.getElementById("menu-main").append(listItem);
    listItem.appendChild(link);
  });
}

function deleteBookmark(event) {
  // WARNING
  // UB addBookmark listener is added to all the buttons, not the bookmark only one
  // prevent the bookmark addinf for other buttons
  if (!event.target.id.includes("btn-del") &&
      !event.target.id.includes("a-icon")) {
    return;
  }
  let url = "del_bm";
  let num = event.target.getAttribute("id").split("-")[2];
  let paper = DATA.papers[parseInt(num, 10)];
  $.post(url, {
               "paper_id": paper.id.split("v")[0],
               })
  .done(function(data, textStatus, jqXHR) {
    let status = jqXHR.status;
    if (status === 201) {
      raiseAlert("Paper has been deleted", "success");
    }
    $("#paper-"+num).css("display", "none");
  }).fail(function(){
    raiseAlert("Paper is not deleted due to server error", "danger");
  });
}

function renderPapers() {
  document.getElementById("paper-list-title").textContent = DATA.list;
  DATA.papers.forEach((paper, num) => {
    let paperBase = renderPapersBase(paper, num);

    // removal button
    let btnPanel = paperBase[1];

    let btnDel = document.createElement("button");
    btnDel.className = "btn btn-danger";
    btnDel.id = "btn-del-"+num;
    btnDel.innerHTML = "<i class='fa fa-trash-o' aria-hidden='true' id='a-icon-" + num + "'></i>";
    btnDel.addEventListener("click", deleteBookmark);


    let btnGroup4 = document.createElement("div");
    btnGroup4.className = "btn-group mr-2";
    btnGroup4.role = "group";
    btnPanel.appendChild(btnGroup4);
    btnGroup4.appendChild(btnDel);

  });

  if (parseTex) {
    MathJax.typesetPromise();
  }
  $("#loading-papers").css("display", "none");
}

window.onload = function() {
  renderLists();
  renderPapers();
};