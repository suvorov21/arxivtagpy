/*global MathJax, parseTex, DATA, LISTS, raiseAlert, renderPapersBase, displayList, page, paperPage, cssVar */
/*eslint no-undef: "error"*/

var unseenCurrentList = 0;

function renderLists() {
  // WARNING very inacurate parsing
  // TODO replace with regex
  let hrefBase = document.location.href.split("=")[0];
  LISTS.forEach((listName) => {
    let listItem = document.createElement("li");
    listItem.className = "nav-item";
    let link = document.createElement("a");
    link.href = hrefBase + "=" + listName.id;
    link.className = "nav-link";
    if (listName.id === displayList) {
      link.className += " active";
      unseenCurrentList = listName.not_seen;
    }
    link.textContent = listName.name;
    if (listName.not_seen !== 0) {
      link.textContent += " ";
      let badge = document.createElement("span");
      badge.className = "badge badge-light";
      badge.textContent = listName.not_seen;
      link.appendChild(badge);
    }
    listItem.appendChild(link);

    document.getElementById("menu-list").append(listItem);
    let clone = listItem.cloneNode(true);
    document.getElementById("menu-list-mob").append(clone);
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
  let paper = DATA.papers[parseInt(num, 10) - (page - 1) * paperPage];
  $.post(url, {
               "paper_id": paper.id.split("v")[0],
               "list_id": displayList
               })
  .done(function(data, textStatus, jqXHR) {
    let status = jqXHR.status;
    if (status === 201) {
      raiseAlert("Paper has been deleted", "success");
    }
    $("#paper-"+num).css("display", "none");
    DATA.papers.splice(num, 1);
    DATA.papers.forEach((paper, iter) => {
      console.log(iter, num)
      let numEl = document.getElementById("paper-num-" + parseInt(paper.num, 10));
      console.log(numEl.textContent, iter, num);
      numEl.textContent = String(iter + 1);
    });
  }).fail(function(){
    raiseAlert("Paper is not deleted due to server error", "danger");
  });
}

function renderPapers() {
  DATA.papers.forEach((paper, num) => {
    num += paperPage * (page - 1);
    let paperBase = renderPapersBase(paper, num);

    // highlight new papers
    let paperElement = paperBase[0];
    if (num < unseenCurrentList) {
      paperElement.style.backgroundColor = cssVar("--unseen-paper-bg");
    }

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