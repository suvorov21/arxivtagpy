/*global TAGS*/
/*eslint no-undef: "error"*/

function renderOcoins(paper) {
  let ocoins = {
    "ctx_ver": "Z39.88-2004",
    "rft_val_fmt": encodeURIComponent("info:ofi/fmt:kev:mtx:journal"),
    "rft_id": encodeURIComponent(paper.ref_web),
    "rft_id": encodeURIComponent(paper.ref_doi),
    "rft.atitle": encodeURIComponent(paper.title),
    "rft.jtitle": encodeURIComponent("arXiv:" + paper.id + " [" + paper.cats[0] + "]"),
    "rft.date": encodeURIComponent(paper.date_up),
    "rft.artnum": encodeURIComponent(paper.id),
    "rft.genre": encodeURIComponent("preprint"),
    "rft.description": encodeURIComponent(paper.abstract),
  };

  ocoins = JSON.stringify(ocoins);
  ocoins = ocoins.replace(/\"/g, "");
  ocoins = ocoins.replace(/,/g, "&");
  ocoins = ocoins.replace(/:/g, "=");
  ocoins = ocoins.slice(1, ocoins.length - 1);

  ocoins += paper.author.map((au) => {return "&rft.au=" + encodeURIComponent(au);}).join();

  return ocoins;
}

function renderAuthors(authors) {
  let au = document.createElement("div");
  au.className = "paper-au";
  if (authors.length > 4){
    authors = authors.slice(0, 5);
    authors.push("et al");
  }
  au.textContent = authors.join(", ");
  return au;
}

function rebderButtonsBase(content, pId) {
  let btnPanel = document.createElement("div");
  btnPanel.className = "btn-toolbar";
  btnPanel.id = "btn-toolbar-"+pId;

  let btnGroup1 = document.createElement("div");
  btnGroup1.className = "btn-group mr-2";
  btnGroup1.role = "group";
  btnPanel.appendChild(btnGroup1);

  let btnAbs = document.createElement("button");
  btnAbs.className = "btn btn-primary";
  btnAbs.setAttribute("data-toggle", "collapse");
  btnAbs.setAttribute("data-target", "#abs-"+pId);
  btnAbs.id = "btn-abs-"+pId;
  btnAbs.textContent = "Abstract";
  btnGroup1.appendChild(btnAbs);

  let btnPdf = document.createElement("a");
  btnPdf.className = "btn btn-primary";
  btnPdf.id = "btn-pdf-"+pId;
  btnPdf.href = content.ref_pdf;
  btnPdf.target = "_blank";
  btnPdf.innerHTML = "<i class='fa fa-file-pdf-o' aria-hidden='true' style='font-weight:600'></i>&nbsp; PDF";

  let btnGroup2 = document.createElement("div");
  btnGroup2.className = "btn-group mr-2";
  btnGroup2.role = "group";
  btnPanel.appendChild(btnGroup2);
  btnGroup2.appendChild(btnPdf);

  let btnArxiv = document.createElement("a");
  btnArxiv.className = "btn btn-primary";
  btnArxiv.id = "btn-arxiv-"+pId;
  btnArxiv.href = content.ref_web;
  btnArxiv.target = "_blank";
  btnArxiv.textContent = "arXiv";

  let btnGroup3 = document.createElement("div");
  btnGroup3.className = "btn-group mr-2";
  btnGroup3.relo = "group";
  btnPanel.appendChild(btnGroup3);
  btnGroup3.appendChild(btnArxiv);

  return btnPanel;
}

function renderPapersBase(content, pId) {
  let paper = document.createElement("div");
  paper.className = "paper";
  paper.id = "paper-"+pId;
  document.getElementById("paper-list-content").appendChild(paper);

  let ocoinsSpan = document.createElement("span");
  ocoinsSpan.className = "Z3988";
  ocoinsSpan.title = renderOcoins(content);
  paper.appendChild(ocoinsSpan);

  let title = document.createElement("div");
  title.className = "paper-title";
  title.id = "paper-title-"+pId;

  paper.appendChild(title);

  let number = document.createElement("span");
  number.id = "paper-num-"+pId;
  number.textContent = String(pId+1);

  let titleText = document.createElement("span");
  titleText.textContent = ". " + content.title;
  title.appendChild(number);
  title.appendChild(titleText);

  var tagPanel = document.createElement("div");
  tagPanel.className = "tag-panel";
  tagPanel.id = "tag-panel-"+pId;
  paper.appendChild(tagPanel);

  if ("tags" in content && content.tags.length > 0) {
    content.tags.forEach(function(tag) {
      var tagDiv = document.createElement("div");
      tagDiv.className = "tag-panel-item";
      tagDiv.style = "background-color:" + TAGS[parseInt(tag, 10)].color;
      tagDiv.textContent = TAGS[parseInt(tag, 10)].name;
      tagPanel.appendChild(tagDiv);
    });
  } else {
    tagPanel.style = "display: none";
  }

  let au = renderAuthors(content.author);
  paper.appendChild(au);

  let date = document.createElement("div");
  date.id = "paper-date-"+pId;
  date.className = "paper-date";
  date.textContent = content.date_up;

  if (content.date_sub !== content.date_up) {
    date.textContent += " (v1: " + content.date_sub + ")";
  }
  paper.appendChild(date);

  if (content.ref_doi) {
    let ref = document.createElement("div");
    ref.className = "ref";

    let dark = document.createElement("span");
    dark.className = "dark paper-doi";
    dark.textContent = " doi:";

    let light = document.createElement("span");
    light.className = "light paper-doi";

    let link = document.createElement("a");
    link.href = content.ref_doi;
    link.target = "_blank";
    link.textContent = content.ref_doi.split(".org/")[1];

    paper.appendChild(ref);
    ref.appendChild(dark);
    ref.appendChild(light);
    light.appendChild(link);
  }

  let cat = document.createElement("div");
  cat.className = "paper-cat";
  cat.innerHTML = "[<strong>" + content.cats[0] + "</strong>";
  if (content.cats.length > 1) {
    cat.innerHTML += ", ";
  }
  cat.innerHTML += content.cats.slice(1).join(", ");
  cat.innerHTML += "]";
  paper.appendChild(cat);

  let btnPanel = rebderButtonsBase(content, pId);
  paper.appendChild(btnPanel);

  let abs = document.createElement("div");
  abs.className = "collapse paper-abs";
  abs.id = "abs-"+pId;
  abs.textContent = content.abstract;
  paper.appendChild(abs);

  return [paper, btnPanel];
}