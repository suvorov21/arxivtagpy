import {Data, Paper} from "./paper_basic";

declare const __CATS__: Array<string>;

const sortFunction = (a:number, b:number,
                      aDate:number, bDate:number,
                      order = true,
                      ): number => {
    if (a !== b) {
        return order? a - b : b - a;
    }
    // secondary sort always for date_up
    return bDate - aDate;
};

const sortTags = (DATA: Data, sortMethod: string) => {
    DATA.papersVis.sort((a: Paper, b: Paper) => {
        if (b.tags.length === 0 && a.tags.length !== 0) {
            return sortMethod === "tag-as" ? -1 : 1;
        }
        if (b.tags.length !== 0 && a.tags.length === 0) {
            return sortMethod === "tag-as" ? 1 : -1;
        }
        if (b.tags.length === 0 && a.tags.length === 0) {
            return -1;
        }
        return sortFunction(a.tags[0], b.tags[0],
            (new Date(a.date_up).getTime()),
            (new Date(b.date_up).getTime()),
            sortMethod.includes("as")
        );
    });
};

const sortCats = (DATA: Data, sortMethod: string) => {
    DATA.papersVis.sort((a: Paper, b: Paper) => {
        let catA = "";
        let catB = "";
        for (let id = 0; id < a["cats"].length; id++) {
            if (__CATS__.includes(a["cats"][`${id}`])) {
                catA = a["cats"][`${id}`];
                break;
            }
        }
        for (let id = 0; id < b["cats"].length; id++) {
            if (__CATS__.includes(b["cats"][`${id}`])) {
                catB = b["cats"][`${id}`];
                break;
            }
        }
        return sortFunction(__CATS__.indexOf(catA), __CATS__.indexOf(catB),
                            new Date(a.date_up).getTime(),
                            new Date(b.date_up).getTime(),
                            sortMethod === "cat-as"
                            );
    });
}

const sortDate  = (DATA: Data, sortMethod: string, date: string) => {
    DATA.papersVis.sort((a: Paper, b: Paper) => {
        const aDate = new Date(a[date]);
        const bDate = new Date(b[date]);
        return sortFunction(aDate.getTime(), bDate.getTime(),
                            aDate.getTime(), bDate.getTime(),
                            sortMethod.includes("des")
                            );
    });
}

export const sortPapers = (DATA: Data) => {
    /** Sort the papers.
     * Only papers marked as visible will be sorted.
     */
    const sortMethod = String((document.getElementById("sort-sel") as HTMLInputElement).value);
    // tags
    if (sortMethod.includes("tag")) {
        sortTags(DATA, sortMethod);
    }
    // dates
    if (sortMethod.includes("date-up")) {
        sortDate(DATA, sortMethod, "date_up");
    }

    if (sortMethod.includes("date-sub")) {
        sortDate(DATA, sortMethod, "date_sub");
    }

    // categories
    if (sortMethod.includes("cat")) {
        sortCats(DATA, sortMethod);
    }
};