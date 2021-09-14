/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {setDefaultListeners} from "./settings";
import {raiseAlert} from "./layout";

const renderPref = (): void => {
    if (window["PREF"]["tex"]) {
        (document.getElementById("tex-check") as HTMLInputElement).checked = true;
    }

    if (window["PREF"]["theme"] === "dark") {
        (document.getElementById("radio-dark") as HTMLInputElement).checked = true;
    } else {
        (document.getElementById("radio-light") as HTMLInputElement).checked = true;
    }
};

const fillSetForm = (): boolean => {
    if ($(".btn-cancel").hasClass("disabled")) {
        return false;
    }
    const url = "mod_pref";
    let themeName = "light";
    if ((document.getElementById("radio-dark") as HTMLInputElement).checked) {
        themeName = "dark";
    }
    const dataSet = {"tex": (document.getElementById("tex-check") as HTMLInputElement).checked,
        "theme": themeName
    };
    $.post(url, JSON.stringify(dataSet))
        .done(function() {
            renderPref();
            const btnCollection = document.getElementsByClassName("btn-save");
            for (let i = 0; i < btnCollection.length; i++) {
                btnCollection[`${i}`].classList.add("disabled");
            }
            raiseAlert("Settings are saved", "success");
            // update the stylesheets. Just in case theme was changed
            const links = document.getElementsByTagName("link");
            for (let i = 0; i < links.length; i++) {
                const link = links[`${i}`];
                if (link.rel === "stylesheet") {
                    link.href += "?";
                }}
            localStorage.clear();
            window.location.reload();
            return false;
        }).fail(function(){
        raiseAlert("Settings were not saved. Please try later", "danger");
        return false;
    });

    return false;
};

const noEmail = (): boolean => {
    if (confirm("Do you want to unsubscribe from all your tag email feeds?")) {
        $.post("noEmail")
            .done(function() {
                raiseAlert("Successfully unsubscribed from all tag emails.", "success");
                return false;
            }).fail(function() {
            raiseAlert("Settings were not saved. Please try later", "danger");
            return false;
        });
        return false;
    } else {
        return false;
    }
};

window.onload = () => {
    renderPref();
    setDefaultListeners();
    (document.getElementById("del-acc") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        if (confirm("Do you want to delete account completely? This action could not be undone!")) {
            $.post("delAcc");
        }
    });
    (document.getElementById("email-cancel") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        noEmail();
    });
    (document.getElementById("mod-set") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        if ($(".btn-cancel").hasClass("disabled")) {
            return false;
        }
        fillSetForm();
    });
};