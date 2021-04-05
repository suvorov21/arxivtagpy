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

function renderPapersBase(content, pId) {
  let paper = document.createElement("div");
  paper.setAttribute("class", "paper");
  paper.setAttribute("id", "paper-"+pId);
  document.getElementById("paper-list-content").appendChild(paper);

  let ocoinsSpan = document.createElement("span");
  ocoinsSpan.setAttribute("class", "Z3988");
  ocoinsSpan.setAttribute("title", renderOcoins(content));
  paper.appendChild(ocoinsSpan);

  let title = document.createElement("div");
  title.setAttribute("class", "paper-title");
  title.setAttribute("id", "paper-title-"+pId);

  paper.appendChild(title);

  let number = document.createElement("span");
  number.setAttribute("id", "paper-num-"+pId);
  number.textContent = String(pId+1);

  let titleText = document.createElement("span");
  titleText.textContent = ". " + content.title;
  title.appendChild(number);
  title.appendChild(titleText);

  var tagPanel = document.createElement("div");
  tagPanel.setAttribute("class", "tag-panel");
  tagPanel.setAttribute("id", "tag-panel-"+pId);
  paper.appendChild(tagPanel);

  if (content.tags !== undefined) {
    content.tags.forEach(function(tag) {
      var tagDiv = document.createElement("div");
      tagDiv.setAttribute("class", "tag-panel-item");
      tagDiv.setAttribute("style", "background-color:" + TAGS[parseInt(tag, 10)].color);
      tagDiv.textContent = TAGS[parseInt(tag, 10)].name;
      tagPanel.appendChild(tagDiv);
    });

    if (content.tags.length === 0) {
      tagPanel.setAttribute("style", "display: none");
    }
  }

  let au = document.createElement("div");
  au.setAttribute("class", "paper-au");
  let authors = content.author;
  if (authors.length > 4){
    authors = authors.slice(0, 5);
    authors.push('et al');
  }
  au.textContent = authors.join(", ");
  paper.appendChild(au);

  let date = document.createElement("div");
  date.setAttribute("id", "paper-date-"+pId);
  date.setAttribute("class", "paper-date");
  date.textContent = content.date_up;

  if (content.date_sub !== content.date_up) {
    date.textContent += " (v1: " + content.date_sub + ")";
  }
  paper.appendChild(date);

  if (content.ref_doi) {
    let ref = document.createElement("div");
    ref.setAttribute("class", "ref");

    let dark = document.createElement("span");
    dark.setAttribute("class", "dark paper-doi");
    dark.textContent = " doi:";

    let light = document.createElement("span");
    light.setAttribute("class", "light paper-doi");

    let link = document.createElement("a");
    link.setAttribute("href", content.ref_doi);
    link.setAttribute("target", "_blank");
    link.textContent = content.ref_doi.split(".org/")[1];

    paper.appendChild(ref);
    ref.appendChild(dark);
    ref.appendChild(light);
    light.appendChild(link);
  }

  let cat = document.createElement("div");
  cat.setAttribute("class", "paper-cat");
  cat.innerHTML = "[<strong>" + content.cats[0] + "</strong>";
  if (content.cats.length > 1) {
    cat.innerHTML += ", ";
  }
  cat.innerHTML += content.cats.slice(1).join(", ");
  cat.innerHTML += "]";
  paper.appendChild(cat);

  let btnPanel = document.createElement("div");
  btnPanel.setAttribute("class", "btn-toolbar");
  btnPanel.setAttribute("id", "btn-toolbar-"+pId);

  let btnGroup1 = document.createElement("div");
  btnGroup1.setAttribute("class", "btn-group mr-2");
  btnGroup1.setAttribute("role", "group");

  paper.appendChild(btnPanel);
  btnPanel.appendChild(btnGroup1);

  let btnAbs = document.createElement("button");
  btnAbs.setAttribute("class", "btn btn-primary");
  btnAbs.setAttribute("data-toggle", "collapse");
  btnAbs.setAttribute("data-target", "#abs-"+pId);
  btnAbs.setAttribute("id", "btn-abs-"+pId);
  btnAbs.textContent = "Abstract";
  btnGroup1.appendChild(btnAbs);

  let btnPdf = document.createElement("a");
  btnPdf.setAttribute("class", "btn btn-primary");
  btnPdf.setAttribute("id", "btn-pdf-"+pId);
  btnPdf.setAttribute("href", content.ref_pdf);
  btnPdf.setAttribute("target", "_blank");
  btnPdf.innerHTML = "<i class='fa fa-file-pdf-o' aria-hidden='true' style='font-weight:600'></i>&nbsp; PDF";

  let btnGroup2 = document.createElement("div");
  btnGroup2.setAttribute("class", "btn-group mr-2");
  btnGroup2.setAttribute("role", "group");
  btnPanel.appendChild(btnGroup2);
  btnGroup2.appendChild(btnPdf);

  let btnArxiv = document.createElement("a");
  btnArxiv.setAttribute("class", "btn btn-primary");
  btnArxiv.setAttribute("id", "btn-arxiv-"+pId);
  btnArxiv.setAttribute("href", content.ref_web);
  btnArxiv.setAttribute("target", "_blank");
  btnArxiv.textContent = "arXiv";

  let btnGroup3 = document.createElement("div");
  btnGroup3.setAttribute("class", "btn-group mr-2");
  btnGroup3.setAttribute("role", "group");
  btnPanel.appendChild(btnGroup3);
  btnGroup3.appendChild(btnArxiv);

  let abs = document.createElement("div");
  abs.setAttribute("class", "collapse paper-abs");
  abs.setAttribute("id", "abs-"+pId);
  abs.textContent = content.abstract;
  paper.appendChild(abs);

  return [paper, btnPanel];
}