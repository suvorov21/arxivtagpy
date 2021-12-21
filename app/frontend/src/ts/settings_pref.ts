/* eslint no-console: ["error", { allow: ["warn", "error"] }] */
import {setDefaultListeners, raiseModal} from "./settings";
import {raiseAlert} from "./layout";

declare const __PREF__;
declare const __EMAIL__;
declare const __VERIF__;
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

const confirmEditEmail = (event): void => {
    const newEmailText = (document.getElementById("emailInput") as HTMLInputElement).value;
    // check if the input is valid
    if (!/^\w+([.-]?\w+)*@\w+([.-]?\w+)*(\.\w{2,3})+$/.test(newEmailText)) {
        raiseAlert("Check your email to match format name@domain.zone!");
        return;
    }
    let optional = "";
    if (__EMAIL__ !== "None" && __VERIF__) {
        optional = "<br>Confirmation email will be sent to the old email " + __EMAIL__;
    }
    const form = document.getElementById("form-confirm");

    const probe = form.querySelector("input[name='newEmail']");
    if (probe) {
        (probe as HTMLInputElement).value = newEmailText;
    } else {
        const newEmail = document.createElement("input");
        newEmail.hidden = true;
        newEmail.type = "text";
        newEmail.name = "newEmail";
        newEmail.value = newEmailText;
        form.appendChild(newEmail);
    }

    raiseModal(event,
        "Are you sure to change email to <b>" + newEmailText + "</b>?" + optional,
        "btn btn-warning",
        "",
        "/email_change"
    );
}

document.getElementById("emailChange").onclick = () : void => {
    /**
     * Edit email
     */

    const confirmBtn = document.createElement("i");
    confirmBtn.className = "ps-2 fa fa-check btn-confirm";
    confirmBtn.id = "confirm-btn";
    confirmBtn.addEventListener("click", confirmEditEmail);

    const field = document.createElement("input");
    field.className = "ms-2";
    field.type = "email";
    field.id = "emailInput";
    field.autocomplete = "email";
    const email = document.getElementById("email").textContent;
    if (email !== "no one") {
        field.value = email;
    } else {
        field.value = "";
    }

    const parentEle = document.getElementById("email");
    parentEle.innerHTML = "";
    document.getElementById("emailChange").style.display = "none";
    document.getElementById("verification").style.display = "none";
    parentEle.appendChild(field);
    parentEle.appendChild(confirmBtn);
    field.focus();
}

window.onload = () => {
    renderPref();
    setDefaultListeners();
    (document.getElementById("del-acc") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        raiseModal(event,
            "Do you want to delete account completely? <br> This action could not be undone!",
            "btn btn-danger",
            "",
            "/delAcc"
        )
    });
    (document.getElementById("email-cancel") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        raiseModal(event,
            "Do you want to unsubscribe from all your tag email feeds?",
            "btn btn-warning",
            "",
            "/noEmail"
        )
    });
    (document.getElementById("mod-set") as HTMLFormElement).addEventListener("submit",  (event: Event) => {
        event.preventDefault();
        if ($(".btn-cancel").hasClass("disabled")) {
            return false;
        }
        fillSetForm();
    });
};