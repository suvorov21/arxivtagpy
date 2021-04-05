/*global MathJax, parseTex, DATA, LISTS, raiseAlert, renderPapers*/
/*eslint no-undef: "error"*/

function renderLists() {
  LISTS.forEach((listName, num) => {
    let list_item = document.createElement("div");
    list_item.setAttribute("class", "menu-item");
    let link = document.createElement("a");
    link.setAttribute("href", "/");
    link.textContent = listName;
    document.getElementById("menu-main").append(list_item);
    list_item.appendChild(link);
  });
}

function renderPapers() {
  document.getElementById("paper-list-title").textContent = DATA.list
  DATA.papers.forEach((paper, num) => {
    let paperBase = renderPapersBase(paper, num);

    // removal button
    let btnPanel = paperBase[1];

    let btnDel = document.createElement("button");
    btnDel.setAttribute("class", "btn btn-danger");
    btnDel.setAttribute("id", "btn-del-"+num);
    btnDel.innerHTML = "<i class='fa fa-trash-o' aria-hidden='true' id='a-icon-" + num + "'></i>";
    btnDel.onclick = function(event) {
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
      }).fail(function(){
        raiseAlert("Paper is not deleted due to server error", "danger");
      });
    };

    let btnGroup4 = document.createElement("div");
    btnGroup4.setAttribute("class", "btn-group mr-2");
    btnGroup4.setAttribute("role", "group");
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
}