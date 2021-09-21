/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import "../css/wheelcolorpicker.css";
import "../js/jquery.wheelcolorpicker";
import {submitSetting, setDefaultListeners, dropElement} from "./settings";
import {cssVar, raiseAlert, Tag} from "./layout";

let tagEdited = false;
let editTagId = -2;
let tableFilled = false;

let loadingTags = false;

let dragTarget;

declare const __TAGS__: Array<Tag>;
declare const MathJax;
declare const __parseTex__: boolean;

export const findTagId = (param: string, paramName: string): string => {
    if (__TAGS__.length > 0 && !Object.prototype.hasOwnProperty.call(__TAGS__[0], paramName)) {
        console.error("Wrong tag param request " + paramName);
        return "-2";
    }
    for (let tagId = 0; tagId < __TAGS__.length; tagId++) {
        if (String(__TAGS__[`${tagId}`][`${paramName}`]) === param) {
            return String(tagId);
        }
    }
    return "-1";
};

const dropTag = (event: DragEvent): void => {
    dropElement(event, __TAGS__, dragTarget);
    renderTags();
};

function renderTags() {
    $("#tag-list").empty();
    __TAGS__.forEach((tag: Tag) => {
        const tagElement = document.createElement("div");
        tagElement.className = "tag-label";
        tagElement.id = "tag-label-" + tag.id;
        tagElement.setAttribute("style", "background-color: " + tag.color);
        tagElement.draggable = true;
        tagElement.textContent = tag.name;
        document.getElementById("tag-list").appendChild(tagElement);

        tagElement.ondragstart = (event: DragEvent) => {
            if (tagEdited) {
                event.preventDefault();
                return;
            }
            const target = event.target  as HTMLElement;
            let moved = target.id.split("-")[2];
            moved = findTagId(moved, "id");
            event.dataTransfer.setData("Text", moved);
        };

        tagElement.ondragover = (event: DragEvent) => {
            let target = event.target  as HTMLElement;
            // happens if drag over MATHJAX
            while (target.id === null) {
                target = target.parentElement;
            }
            const targetStr = target.id.split("-")[2];
            dragTarget = findTagId(targetStr, "id");
        };
    });
        document.getElementById("tag-list").ondragover = (event: DragEvent) => {
        event.preventDefault();
    };

    // tag reordering
    document.getElementById("tag-list").removeEventListener("drop", dropTag);
    document.getElementById("tag-list").addEventListener("drop", dropTag);

    if (__parseTex__) {
        MathJax.typesetPromise();
    }
    // new tag button
    const tagElement = document.createElement("div");
    tagElement.setAttribute("class", "add-set tag-label");
    tagElement.setAttribute("id", "add-tag");
    tagElement.textContent = "+New";

    document.getElementById("tag-list").appendChild(tagElement);
}

const updateColorField = () => {
    const colorEl = document.getElementById("tag-color") as HTMLInputElement;
    colorEl.style.backgroundColor =  colorEl.value;
};

const clearTagField = (): void => {
    document.forms["add-tag"]["tag_name"].value = "";
    document.forms["add-tag"]["tag_rule"].value = "";
    document.forms["add-tag2"]["tag_color"].value = "";
    document.forms["add-tag2"]["book-check"].checked = false;
    document.getElementById("btn-book").classList.add("disabled");
    document.forms["add-tag2"]["email-check"].checked = false;
    document.forms["add-tag2"]["public-check"].checked = false;
    updateColorField();
};

const reloadTags = (hardReload = false): void => {
    if (hardReload) {
        window.location.reload();
    } else {
        renderTags();
        editTagId = -2;
        $("#tag-fields").prop("disabled", true);
        $("#tag-fields2").prop("disabled", true);
        clearTagField();
        $(".btn-save").addClass("disabled");
        $("#btn-del").addClass("disabled");
    }
};

const checkMath = (a, b, rule: string): boolean => {
    const openMatch = (rule.match(a) || []).length;
    const closeMatch = (rule.match(b) || []).length;

    return openMatch === closeMatch;
};

const checkTagRule = (rule: string): boolean => {
    const openP = /\(/g;
    const closeP = /\)/g;

    const openC = /{/g;
    const closeC = /}/g;

    if (!checkMath(openP, closeP, rule) || !checkMath(openC, closeC, rule)) {
        return false;
    }

    // https://regex101.com/r/BbdDgl/1
    const generalCheck = /^(\(|)(ti|au|abs)({.+})(([|&])(\(|)((ti|au|abs){.+})(\)|))*$/i;

    return generalCheck.test(rule);
};

// check if tag info is filled properly
// if yes, do API call
const checkTag = (): boolean => {
    document.getElementsByClassName(("sub-alert"))[0].innerHTML = "";
    // in case of simple replacement no check required
    if (!tagEdited) {
        submitSetting("mod_tag", __TAGS__).then(() => {
            reloadTags(false);
        });
        return true;
    }

    // check all fields are filled
    if (document.forms["add-tag"]["tag_name"].value === "" ||
        document.forms["add-tag"]["tag_rule"].value === "" ||
        document.forms["add-tag2"]["tag_color"].value === "") {
        document.getElementsByClassName("sub-alert")[0].textContent = "Fill all the fields in the form!";
        return false;
    }

    const tagWithSameNameId = parseInt(findTagId(document.forms["add-tag"]["tag_name"].value,
        "name"
    ), 10);
    if (tagWithSameNameId !== -1 && tagWithSameNameId !== editTagId) {
        document.getElementsByClassName("sub-alert")[0].textContent = "Tag with this name already exists. Consider a unique name!";
        return false;
    }

    // check rule
    const rule = document.forms["add-tag"]["tag_rule"].value;
    if (!checkTagRule(rule)) {
        document.getElementsByClassName("sub-alert")[0].textContent = "Check the rule syntax!";
        return false;
    }

    // check color
    if (!/^#[0-9A-F]{6}$/i.test(document.forms["add-tag2"]["tag_color"].value)) {
        $(".sub-alert").html("Color should be in hex format: e.g. #aaaaaa");
        return false;
    }

    // tag rules are checked
    const TagDict = {"name": document.forms["add-tag"]["tag_name"].value,
        "rule": document.forms["add-tag"]["tag_rule"].value,
        "color": document.forms["add-tag2"]["tag_color"].value,
        "bookmark": document.forms["add-tag2"]["book-check"].checked,
        "email": document.forms["add-tag2"]["email-check"].checked,
        "public": document.forms["add-tag2"]["public-check"].checked
    };
    if (editTagId > -1 && editTagId < __TAGS__.length) {
        __TAGS__[`${editTagId}`]["name"] = TagDict["name"];
        __TAGS__[`${editTagId}`]["rule"] = TagDict["rule"];
        __TAGS__[`${editTagId}`]["color"] = TagDict["color"];
        __TAGS__[`${editTagId}`]["bookmark"] = TagDict["bookmark"];
        __TAGS__[`${editTagId}`]["email"] = TagDict["email"];
        __TAGS__[`${editTagId}`]["public"] = TagDict["public"];
    } else {
        // new tag no id
        TagDict["id"] = -1;
        __TAGS__.push(TagDict);
    }

    submitSetting("mod_tag", __TAGS__).then(() => {
        // reload the page in case of new tag in order to grab the tag id from backend
        reloadTags(editTagId === -1);
    });
    tagEdited = false;
    return false;
};

// delete tag
document.getElementById("btn-del").onclick = (event: MouseEvent) => {
    event.preventDefault();
    if (editTagId < 0 || $("#btn-del").hasClass("disabled")) {
        event.preventDefault();
        return;
    }
    if (editTagId > __TAGS__.length) {
        console.error("Tag edit id larger then the tag list " + editTagId + " " + __TAGS__.length);
        return;
    }
    $("#tag-label-" + __TAGS__[`${editTagId}`]["id"]).fadeOut();
    __TAGS__.splice(editTagId, 1);
    $(".btn-save").removeClass("disabled");
};

document.getElementById("test-rule").onclick = () => {
    const element = document.getElementById("tag-test");
    if (element.style.display === "block") {
        element.style.display = "none";
    } else {
        element.style.display = "block";
    }
};

document.getElementById("test-btn").onclick = (event: MouseEvent) => {
    event.preventDefault();

    const rule = document.forms["add-tag"]["tag_rule"].value;

    if (rule === "") {
        document.getElementById("test-result").textContent = "Rule is empty! Click on tag you want to test";
        return;
    }

    if (!checkTagRule(rule)) {
        document.getElementById("test-result").textContent = "Check rule syntax!";
        return;
    }

    const data = {"title": document.forms["tag-test-form"]["paper_title"].value,
        "author": document.forms["tag-test-form"]["paper_author"].value,
        "abs": document.forms["tag-test-form"]["paper_abs"].value,
        "rule": rule
    };
    const url = "/test_tag";
    $.get(url, data)
        .done(function(data) {
            if (data.includes("true")) {
                // not a good practice, but ok for the time being
                document.getElementById("test-result").innerHTML = "<i class='fa fa-check' aria-hidden='true' style='color: #1a941a'></i>&nbsp;Paper suits the tag!";
            } else {
                document.getElementById("test-result").innerHTML = "<i class='fa fa-times' aria-hidden='true' style='color: #941a1a'></i>&nbsp;Paper does NOT suit the tag!";
            }
        }).fail(function() {
        raiseAlert("Server expirienced an internal error. We are working on that.", "danger");
    });
};

document.getElementById("show-rules").onclick = () => {
    const elHelp = document.getElementById("tag-help");
    const elRules = document.getElementById("show-rules");
    if (elHelp.style.display === "block") {
        elHelp.style.display = "none";
        elRules.textContent = "Show rules hints";
    } else {
        elHelp.style.display = "block";
        elRules.textContent = "Hide rules hints";
    }
};

const changeBookBtnStatus = (val:boolean): void => {
    if (val) {
        document.getElementById("btn-book").classList.remove("disabled");
    } else {
        document.getElementById("btn-book").classList.add("disabled");
    }
};

const makeTagEdited = () => {
    $(".btn-save").removeClass("disabled");
    tagEdited = true;
    const doms = document.getElementsByClassName("tag-label");
    for(let i = 0; i < doms.length; i++) {
        (doms[`${i}`] as HTMLElement).style.cursor = "not-allowed";
    }
};

const tableRowClick = (event: MouseEvent) => {
    // do nothing if tag is not edited
    let message = "Use this name and rule?";
    let newTag = false;
    if (document.getElementsByClassName("btn-save")[0].classList.contains("disabled") && editTagId < -1) {
        message = "Use this rule for a new tag?";
        newTag = true;
    }
    if (confirm(message)) {
        // assume click is done on a cell, thus the row is a parent element
        const row = (event.target as HTMLElement).parentElement;
        for (let childId = 0; childId < row.childNodes.length; childId++) {
            if (newTag) {
                document.getElementById("add-tag").click();
            }
            if (!row.childNodes[`${childId}`].className) {
                continue;
            }
            if (row.childNodes[`${childId}`].className.includes("name")) {
                document.forms["add-tag"]["tag_name"].value = row.childNodes[`${childId}`].textContent;
            }
            if (row.childNodes[`${childId}`].className.includes("rule")) {
                document.forms["add-tag"]["tag_rule"].value = row.childNodes[`${childId}`].textContent;
            }
        }
        makeTagEdited();
    }
};

document.getElementById("show-pubtags").onclick = (event: MouseEvent) => {
    if (loadingTags) {
        event.preventDefault();
        return;
    }
    const wrapper = document.getElementById("table-wrapper");
    const show = document.getElementById("show-pubtags");
    const loading = document.getElementById("loading-tags");
    if (wrapper.style.display === "block") {
        wrapper.style.display =  "none";
        loading.style.display = "none";
        show.textContent = "Show users rules examples";
    } else {
        wrapper.style.display = "block";
        show.textContent = "Hide users rules examples";
    }
    if (tableFilled) {
        event.preventDefault();
        return;
    }

    loadingTags = true;

    loading.style.display = "block";
    $.ajax({
        url: "/public_tags",
        type: "get",
        success(data) {
            data.forEach((tag, num) => {
                const row = document.createElement("tr");
                const inner = document.createElement("th");
                inner.scope = "row";
                inner.textContent = num + 1;
                row.addEventListener("click", tableRowClick);

                const name = document.createElement("td");
                name.className = "name";
                name.textContent = tag.name;

                const rule = document.createElement("td");
                rule.className = "rule";
                rule.style.letterSpacing = "2px";
                rule.textContent = tag.rule;

                document.getElementById("table-body").appendChild(row);
                row.appendChild(inner);
                row.appendChild(name);
                row.appendChild(rule);
            });
            tableFilled = true;
            loadingTags = false;
            $("#loading-tags").css("display", "none");
        }
    });
};

// click on tag label
document.getElementById("tag-list").onclick = (event: MouseEvent) => {
    // consider only tag labels click
    let target = event.target as HTMLElement;
    while(!target.classList.contains("tag-label") && target.id !== "tags-list") {
        target = target.parentElement;
    }

    // check if settings were modified
    if (tagEdited) {
        event.preventDefault();
        return;
    }

    // reset the highlight of all other tags
    const tagCol = document.getElementsByClassName("tag-label");
    for (let id = 0; id < tagCol.length; id++) {
        // new tag box
        if (tagCol[id].id === "add-tag") {
            document.getElementById("add-tag").style.borderStyle = "dashed";
            document.getElementById("add-tag").style.borderWidth = "2px";
        } else {
            // existing tags
            (tagCol[id] as HTMLElement).style.borderColor =  "transparent";
        }
    }

    // highlight the editable tag
    $(target).css("border-color", cssVar("--tag_border_color"));

    if (target.id === "add-tag") {
        // -1 corresponds to new tag
        editTagId = -1;

        document.getElementById("add-tag").style.borderStyle = "solid";
        document.getElementById("add-tag").style.borderWidth = "4px";
        clearTagField();
        // make delete NOT possible
        document.getElementById("btn-del").classList.add("disabled");
    } else {
        const editTagName = target.id.split("-")[2];
        editTagId = parseInt(findTagId(editTagName, "id"), 10);
        const tag = __TAGS__[`${editTagId}`];

        document.forms["add-tag"]["tag_name"].value = tag.name;
        document.forms["add-tag"]["tag_rule"].value = tag.rule;
        document.forms["add-tag2"]["tag_color"].value = tag.color;
        document.forms["add-tag2"]["book-check"].checked = tag.bookmark;
        changeBookBtnStatus(tag.bookmark);
        document.forms["add-tag2"]["email-check"].checked = tag.email;
        document.forms["add-tag2"]["public-check"].checked = tag.public;
        updateColorField();

        // make delete possible
        document.getElementById("btn-del").classList.remove("disabled");
    }
    (document.getElementById("tag-fields") as HTMLFieldSetElement).disabled = false;
    (document.getElementById("tag-fields2") as HTMLFieldSetElement).disabled = false;
};

$(".tag-field").on("input", function() {
    makeTagEdited();
});

// TODO should I delete oninput listener?!
$(".tag-field").on("change", function() {
    makeTagEdited();
});

document.getElementById("tag-color").onchange = () => {
    updateColorField();
    $(".btn-save").removeClass("disabled");
};

document.getElementById("book-check").onchange = () => {
    changeBookBtnStatus(document.forms["add-tag2"]["book-check"].checked);
};

document.getElementById("btn-book").onclick = (event: MouseEvent) => {
    event.preventDefault();
    const rule = document.forms["add-tag"]["tag_rule"].value;
    const name = document.forms["add-tag"]["tag_name"].value;

    if (name === "") {
        raiseAlert("Enter a name for a tag", "danger");
        return;
    }
    if (!checkTagRule(rule)) {
        raiseAlert("Check the rule syntax", "danger");
        return;
    }
    const url = "/bookmark_papers_user";
    const data = {"name": name,
        "rule": rule,
    };
    raiseAlert("Requeest is submitted. Your bookshelf will be updated soon.",
        "success"
    );
    $.post(url, data)
        .done(function() {
            raiseAlert("Successfully updated bookshelf.", "success");
            return false;
        }).fail(function() {
        raiseAlert("Bookmarking failed. Please try later", "danger");
        return false;
    });
};

// on page load
window.onload = () => {
    reloadTags();
    setDefaultListeners();
    (document.getElementById("mod-tag") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        if ($(".btn-cancel").hasClass("disabled")) {
            // TODO remove return?
            return false;
        }
        checkTag();
        return false;
    });
};