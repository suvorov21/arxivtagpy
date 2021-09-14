/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {allCatsArray} from "./allCatsArray";
import {setDefaultListeners, submitSetting, dropElement} from "./settings";
import {raiseAlert} from "./layout";

let dragTarget;

const delCatClick = (event) => {
    const name = event.target.getAttribute("id").split("_")[1];
    const element = $("#par-cat-" + name);
    element.removeClass("d-flex");
    element.fadeOut();
    $(".btn").removeClass("disabled");
    const catId = window["CATS"].indexOf(name.replace("111", "."));
    if (catId > -1) {
        window["CATS"].splice(catId, 1);
    }
};

const addCat = (cat) => {
    // Dots replace with 111 to be a legal
    // name for JS elements
    // TODO proper escape dot with \\.
    const parent = document.createElement("div");
    parent.className = "d-flex cat-parent";
    parent.id = "par-cat-"+cat.replaceAll(".", "111");
    parent.draggable = true;

    parent.ondragstart = function(event) {
        const movedArr = (event.target as HTMLElement).id.split("-").slice(2);
        let moved = movedArr.join("-").split("111").join(".");
        moved = window["CATS"].indexOf(moved);
        event.dataTransfer.setData("Text", moved);
    };

    parent.ondragover = (event: DragEvent) => {
        const targetArr = (event.target as HTMLElement).id.split("-").slice(2);
        const target = targetArr.join("-").split("111").join(".");
        dragTarget = window["CATS"].indexOf(target);
    };

    const close = document.createElement("button");
    close.id = "close_" + cat.replaceAll(".", "111");
    close.className = "close close-btn";
    close.innerHTML = "&times";

    close.addEventListener("click", delCatClick);

    const catElement = document.createElement("div");
    catElement.className = "pl-2";
    catElement.id = "cat-name-" + cat.replaceAll(".", "111");
    catElement.textContent = allCatsArray[`${cat}`];

    document.getElementById("cats-list").appendChild(parent);
    parent.appendChild(close);
    parent.appendChild(catElement);
};

const dropCat = (event: DragEvent): void => {
    dropElement(event, window["CATS"], dragTarget);
    renderCats();
};

const renderCats = () => {
    $("#cats-list").empty();
    window["CATS"].forEach((cat) => {
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
    if (window["CATS"].includes(cat)) {
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
    window["CATS"].push(cat);
};

window.onload = () => {
    $.each(allCatsArray, function(val, text) {
        $("#catsDataList").append($("<option>").attr("value", val).text(text));
    });
    (document.getElementById("mod-cat") as HTMLFormElement).addEventListener("submit", (event) => {
        event.preventDefault();
        if ($(".btn-cancel").hasClass("disabled")) {
            return false;
        }
        submitSetting("mod_cat", window["CATS"]).then(() => {
            $(".btn-save").addClass("disabled");
        });
        return false;
    });

    renderCats();
    setDefaultListeners();
};