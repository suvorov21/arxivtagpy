/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {setDefaultListeners} from "./settings";
import {raiseAlert} from "./layout";

declare const __PREF__;
declare const bootstrap;

const renderPref = (): void => {
    if (__PREF__["tex"]) {
        (document.getElementById("tex-check") as HTMLInputElement).checked = true;
    }

    if (__PREF__["theme"] === "dark") {
        (document.getElementById("radio-dark") as HTMLInputElement).checked = true;
    } else {
        (document.getElementById("radio-light") as HTMLInputElement).checked = true;
    }
};

const fillSetForm = (): void => {
    if ($(".btn-cancel").hasClass("disabled")) {
        return;
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
        }).fail(function(){
        raiseAlert("Settings were not saved. Please try later", "danger");
    });
};

window.onload = () => {
    renderPref();
    setDefaultListeners();
    (document.getElementById("del-acc") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        document.getElementById("modal-text").innerHTML = "Do you want to delete account completely? <br> This action could not be undone!";
        const btn = document.getElementById("btn-confirm") as HTMLLinkElement;
        btn.className = "btn btn-danger";
        btn.type = "submit";
        const form =  document.getElementById("form-confirm") as HTMLFormElement;
        form.action = "/delAcc";
        const modal = new bootstrap.Modal(document.getElementById("confirmModal"));
        modal.show();
    });
    (document.getElementById("email-cancel") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        document.getElementById("modal-text").textContent = "Do you want to unsubscribe from all your tag email feeds?";
        const btn = document.getElementById("btn-confirm") as HTMLLinkElement;
        btn.className = "btn btn-warning";
        btn.type = "submit";
        const form =  document.getElementById("form-confirm") as HTMLFormElement;
        form.action =  "/noEmail";
        const modal = new bootstrap.Modal(document.getElementById("confirmModal"));
        modal.show();
    });
    (document.getElementById("mod-set") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        if ($(".btn-cancel").hasClass("disabled")) {
            return false;
        }
        fillSetForm();
    });
};