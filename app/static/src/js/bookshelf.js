/*global MathJax, parseTex, DATA, LISTS, raiseAlert, renderPapers*/
/*eslint no-undef: "error"*/

function renderLists() {
  LISTS.forEach((listName, num) => {
    let list = document.createElement("div");
    list.textContent = listName;
    document.getElementById("menu-main").append(list);
  });
}

function renderPapers() {
  document.getElementById("paper-list-title").textContent = DATA.list
  DATA.papers.forEach((paper, num) => {
    let paperBase = renderPapersBase(paper, num+1);
  });

  if (parseTex) {
    MathJax.typesetPromise();
  }
  $("#loading-papers").css("display", "none");
}

window.onload = function() {
  renderLists();
  renderPapers();
}