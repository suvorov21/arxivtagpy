/* eslint no-console: ["error", { allow: ["warn", "error"] }] */

import {Tag} from "./layout"

export interface List {
    /**
     * Paper list information served to front-end
     */
    id: number;
    name: string;
    not_seen: number;
}

export interface Paper {
    /**
     * Paper information served to front-end
     */
    id: string;
    title: string;
    author: string;
    abstract: string;
    date_up: string;
    date_sub: string;
    tags: Array<number>;
    cats: Array<string>;
    nov: number;
    ref_pdf: string;
    ref_web: string;
    ref_doi: string;
    hide?: boolean;
}

export interface Data {
    /** Interface between backend and front-end.
     * Contains the papers and the information about paper counters
     */
    // precisely specified page title
    title?: string;
    // all the papers received from server
    papers: Array<Paper>;
    lists: Array<List>;
    // counters --> number of papers in category / tag
    nnov: Array<number>;
    ncat: Array<number>;
    ntag: Array<number>;
    // visible papers that are selected according to checkbox set
    papersVis?: Array<Paper>
}

declare const __TAGS__: Array<Tag>;

const renderOcoins = (paper) => {
    const ocoins = {
        "ctx_ver": "Z39.88-2004",
        "rft_val_fmt": encodeURIComponent("info:ofi/fmt:kev:mtx:journal"),
        "rft.atitle": encodeURIComponent(paper["title"]),
        "rft.jtitle": encodeURIComponent("arXiv:" + paper.id + " [" + paper["cats"][0] + "]"),
        "rft.date": encodeURIComponent(paper["date_up"]),
        "rft.artnum": encodeURIComponent(paper["id"]),
        "rft.genre": encodeURIComponent("preprint"),
        "rft.description": encodeURIComponent(paper["abstract"]),
    };

    ocoins["aulast"] = encodeURIComponent(paper.author);
    ocoins["rft_id"] = typeof paper["ref_doi"] === "undefined" ? encodeURIComponent(paper["ref_web"]): encodeURIComponent(paper["ref_doi"]);

    let ocoinsStr = JSON.stringify(ocoins);
    ocoinsStr = ocoinsStr.replace(/"/g, "");
    ocoinsStr = ocoinsStr.replace(/,/g, "&");
    ocoinsStr = ocoinsStr.replace(/:/g, "=");
    ocoinsStr = ocoinsStr.slice(1, ocoinsStr.length - 1);

    return ocoinsStr;
};

const renderButtonsBase = (content: Paper, pId: number): HTMLElement => {
    const btnPanel = document.createElement("div");
    btnPanel.className = "btn-toolbar";
    btnPanel.id = "btn-toolbar-"+pId;

    const btnGroup1 = document.createElement("div");
    btnGroup1.className = "btn-group me-2";
    btnPanel.appendChild(btnGroup1);

    const btnAbs = document.createElement("button");
    btnAbs.className = "btn btn-primary";
    btnAbs.setAttribute("data-bs-toggle", "collapse");
    btnAbs.setAttribute("data-bs-target", "#abs-"+pId);
    btnAbs.id = "btn-abs-"+pId;
    btnAbs.textContent = "Abstract";
    btnGroup1.appendChild(btnAbs);

    const btnPdf = document.createElement("a");
    btnPdf.className = "btn btn-primary";
    btnPdf.id = "btn-pdf-"+pId;
    btnPdf.href = content.ref_pdf;
    btnPdf.target = "_blank";
    btnPdf.innerHTML = "<i class='fa fa-file-pdf-o' aria-hidden='true' style='font-weight:600'></i>&nbsp; PDF";

    const btnGroup2 = document.createElement("div");
    btnGroup2.className = "btn-group me-2";
    btnPanel.appendChild(btnGroup2);
    btnGroup2.appendChild(btnPdf);

    const btnArxiv = document.createElement("a");
    btnArxiv.className = "btn btn-primary";
    btnArxiv.id = "btn-arxiv-"+pId;
    btnArxiv.href = content.ref_web;
    btnArxiv.target = "_blank";
    btnArxiv.textContent = "arXiv";

    const btnGroup3 = document.createElement("div");
    btnGroup3.className = "btn-group me-2";
    btnPanel.appendChild(btnGroup3);
    btnGroup3.appendChild(btnArxiv);

    return btnPanel;
};

export const renderPapersBase = (content: Paper, pId: number): Array<HTMLElement> => {
    const paper = document.createElement("div");
    paper.className = "paper";
    paper.id = "paper-"+pId;
    document.getElementById("paper-list-content").appendChild(paper);

    const ocoinsSpan = document.createElement("span");
    ocoinsSpan.className = "Z3988";
    ocoinsSpan.title = renderOcoins(content);
    paper.appendChild(ocoinsSpan);

    const title = document.createElement("div");
    title.className = "paper-title";
    title.id = "paper-title-"+pId;

    paper.appendChild(title);

    const number = document.createElement("span");
    number.id = "paper-num-"+pId;
    number.textContent = String(pId+1);

    const titleText = document.createElement("span");
    titleText.textContent = ". " + content.title;
    title.appendChild(number);
    title.appendChild(titleText);

    const tagPanel = document.createElement("div");
    tagPanel.className = "tag-panel";
    tagPanel.id = "tag-panel-"+pId;
    paper.appendChild(tagPanel);

    if ("tags" in content && content.tags.length > 0) {
        content.tags.forEach((tag: number) => {
            const tagDiv = document.createElement("div");
            tagDiv.className = "tag-panel-item";
            tagDiv.style.backgroundColor = __TAGS__[tag].color;
            tagDiv.textContent = __TAGS__[tag].name;
            tagPanel.appendChild(tagDiv);
        });
    } else {
        tagPanel.style.display = "none";
    }

    const au = document.createElement("div");
    au.className = "paper-au";
    // unsafe but required to parse unicode accents
    au.innerHTML = content.author;
    paper.appendChild(au);

    const date = document.createElement("div");
    date.id = "paper-date-"+pId;
    date.className = "paper-date";
    date.textContent = content.date_up;

    if ("date_sub" in content && content.date_sub !== content.date_up) {
        date.textContent += " (v1: " + content.date_sub + ")";
    }
    paper.appendChild(date);

    if (content.ref_doi) {
        const ref = document.createElement("div");
        ref.className = "ref";

        const dark = document.createElement("span");
        dark.className = "dark paper-doi";
        dark.textContent = " doi:";

        const light = document.createElement("span");
        light.className = "light paper-doi";

        const link = document.createElement("a");
        link.href = content.ref_doi;
        link.target = "_blank";
        link.textContent = content.ref_doi.split(".org/")[1];

        paper.appendChild(ref);
        ref.appendChild(dark);
        ref.appendChild(light);
        light.appendChild(link);
    }

    const cat = document.createElement("div");
    cat.className = "paper-cat";
    cat.innerHTML = "[<strong>" + content.cats[0] + "</strong>";
    if (content.cats.length > 1) {
        cat.innerHTML += ", ";
    }
    cat.innerHTML += content.cats.slice(1).join(", ");
    cat.innerHTML += "]";
    paper.appendChild(cat);

    const btnPanel = renderButtonsBase(content, pId);
    paper.appendChild(btnPanel);

    const abs = document.createElement("div");
    abs.className = "collapse paper-abs";
    abs.id = "abs-"+pId;
    abs.textContent = content.abstract;
    paper.appendChild(abs);

    return [paper, btnPanel];
};