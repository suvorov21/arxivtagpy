/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {allCatsArray} from "./allCatsArray";
import {setDefaultListeners, submitSetting, dropElement} from "./settings";
import {raiseAlert} from "./layout";

declare const __CATS__: Array<string>

let dragTarget;

const delCatClick = (event) => {
    const name = event.target.getAttribute("id").split("_")[1];
    const element = $("#par-cat-" + name);
    element.fadeOut();
    $(".btn").removeClass("disabled");
    const catId = __CATS__.indexOf(name.replace("111", "."));
    if (catId > -1) {
        __CATS__.splice(catId, 1);
    }
};

const addCat = (cat) => {
    // Dots replace with 111 to be a legal
    // name for JS elements
    // TODO proper escape dot with \\.
    const parent = document.createElement("div");
    parent.className = "cat-parent";
    parent.id = "par-cat-"+cat.replaceAll(".", "111");
    parent.draggable = true;

    parent.ondragstart = function(event: DragEvent) {
        const movedArr = (event.target as HTMLElement).id.split("-").slice(2);
        let moved = movedArr.join("-").split("111").join(".");
        moved = String(__CATS__.indexOf(moved));
        event.dataTransfer.setData("Text", moved);
    };

    parent.ondragover = (event: DragEvent) => {
        const targetArr = (event.target as HTMLElement).id.split("-").slice(2);
        const target = targetArr.join("-").split("111").join(".");
        dragTarget = __CATS__.indexOf(target);
    };

    const close = document.createElement("div");
    close.id = "close_" + cat.replaceAll(".", "111");
    close.className = "close-btn align-middle";
    close.innerHTML = "&times";

    close.addEventListener("click", delCatClick);

    const catElement = document.createElement("div");
    catElement.className = "ps-2 align-middle";
    catElement.style.display = "inline";
    catElement.id = "cat-name-" + cat.replaceAll(".", "111");
    catElement.textContent = allCatsArray[`${cat}`];

    document.getElementById("cats-list").appendChild(parent);
    parent.appendChild(close);
    parent.appendChild(catElement);
};

const dropCat = (event: DragEvent): void => {
    dropElement(event, __CATS__, dragTarget);
    renderCats();
};

const renderCats = () => {
    $("#cats-list").empty();
    __CATS__.forEach((cat: string) => {
        addCat(cat);
    });

    document.getElementById("cats-list").ondragover = (event: DragEvent) => {
        event.preventDefault();
    };
    document.getElementById("cats-list").removeEventListener("drop", dropCat);
    document.getElementById("cats-list").addEventListener("drop", dropCat);
};

document.getElementById("add-cat-btn").onclick = () => {
    const cat = document.forms["add-cat"]["cat_name"].value;
    // check if already there
    if (__CATS__.includes(cat)) {
        raiseAlert("Category already added!", "danger");
        return;
    }
    // check if legal category
    if (typeof(allCatsArray[`${cat}`]) === "undefined") {
        raiseAlert("Unknown category", "danger");
        return;
    }
    $(".btn-save").removeClass("disabled");
    addCat(document.forms["add-cat"]["cat_name"].value);
    document.forms["add-cat"]["cat_name"].value = "";
    // add to array
    __CATS__.push(cat);
};

const submitCat = (event: Event): void => {
    event.preventDefault();
    if ($(".btn-cancel").hasClass("disabled")) {
        return;
    }
    submitSetting("mod_cat", __CATS__).then(() => {
        $(".btn-save").addClass("disabled");
    });
};


window.onload = () => {
    $.each(allCatsArray, (val: string, text: string) => {
        $("#catsDataList").append($("<option>").attr("value", val).text(text));
    });
    (document.getElementById("mod-cat") as HTMLFormElement).addEventListener("submit", submitCat);
    renderCats();
    setDefaultListeners();
};