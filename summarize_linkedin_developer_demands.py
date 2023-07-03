#!/usr/bin/env python3

import os
import re
import time
import argparse
import datetime
import matplotlib.pyplot as plt #type: ignore

from tqdm import tqdm
from typing import Sequence

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as EC


class LinkedInOffers:
    def __init__(
        self,
        headless: bool,
        offer_num_to_load: int,
        search_term: str = "",
        location: str = "",
    ):
        self.headless: bool = headless
        self.search_term: str = search_term
        self.location: str = location
        self.offer_num_to_load: int = offer_num_to_load
        self.__language_synonyms: dict[str, list[str]] = {
            "C": ["C"],
            "C++": ["C++", "CPlusPlus", "CPP"],
            "Java": ["Java"],
            "Python": ["Python"],
            "JavaScript": ["JavaScript", "JS"],
            "Ruby": ["Ruby"],
            "PHP": ["PHP"],
            "Swift": ["Swift"],
            "Kotlin": ["Kotlin"],
            "Go": ["Go", "Golang"],
            "Rust": ["Rust"],
            "TypeScript": ["TypeScript", "TS"],
            "Perl": ["Perl"],
            "Haskell": ["Haskell"],
            "Scala": ["Scala"],
            "Groovy": ["Groovy"],
            "Lua": ["Lua"],
            "R": ["R"],
            "Julia": ["Julia"],
            "MATLAB": ["MATLAB"],
            "Shell": ["Shell", "Bash"],
            "HTML": ["HTML"],
            "CSS": ["CSS"],
            "SQL": ["SQL"],
            "Assembly": ["Assembly"],
            "Objective-C": ["Objective-C"],
            "VB.NET": ["VB.NET"],
            "F#": ["F#"],
            "Dart": ["Dart"],
            "Delphi": ["Delphi"],
            "COBOL": ["COBOL"],
            "Fortran": ["Fortran"],
            "Ada": ["Ada"],
            "Lisp": ["Lisp"],
            "Prolog": ["Prolog"],
            "Erlang": ["Erlang"],
            "Scheme": ["Scheme"],
            "Smalltalk": ["Smalltalk"],
            "Logo": ["Logo"],
            "PL/SQL": ["PL/SQL"],
            "ActionScript": ["ActionScript"],
            "ABAP": ["ABAP"],
            "VBScript": ["VBScript"],
            "PowerShell": ["PowerShell"],
            "Objective-C++": ["Objective-C++"],
        }

        self.language_counter = {key: 0 for key in self.__language_synonyms}

        self.framework_counter: dict[str, int] = {
            "Node.js": 0,
            "React": 0,
            "jQuery": 0,
            "Express": 0,
            "Angular": 0,
            "Next.js": 0,
            "ASP.NET": 0,
            "Vue.js": 0,
            "WordPress": 0,
            "ASP.NET": 0,
            "Flask": 0,
            "Spring": 0,
            "Django": 0,
            "Laravel": 0,
            "FastAPI": 0,
            "AngularJS": 0,
            "Svelte": 0,
            "Ruby": 0,
            "NestJS": 0,
            "Blazor": 0,
            "Nuxt.js": 0,
            "Symfony": 0,
            "Deno": 0,
            "Gatsby": 0,
            "Fastify": 0,
            "Phoenix": 0,
            "Drupal": 0,
            "CodeIgniter": 0,
            "Solid.js": 0,
            "Remix": 0,
            "Elm": 0,
            "Play": 0,
            "Lit": 0,
            "Qwik": 0,
        }

        self.__firefox_options: webdriver.FirefoxOptions | None = (
            webdriver.FirefoxOptions()
        )

        if self.headless:
            self.__firefox_options.add_argument("-headless")

        self.__browser: webdriver.Firefox = webdriver.Firefox(
            options=self.__firefox_options
        )

        self.__element_waiter: WebDriverWait = WebDriverWait(self.__browser, 3)
        self.__browser.get(
            "https://www.linkedin.com/jobs/search?trk=guest_homepage-basic_guest_nav_menu_jobs&position=1&pageNum=0"
        )
        self.__search_offers()

        self.__load_n_offers(self.offer_num_to_load)

        self.offer_elements: list[WebElement] = self.__get_sidebar_offers()
        self.__iterate_offers()
        self.__browser.close()

    def __search_offers(self) -> None:
        term_search = self.__browser.find_element(
            By.CSS_SELECTOR, '[id="job-search-bar-keywords"]'
        )
        location_search = self.__browser.find_element(
            By.CSS_SELECTOR, '[id="job-search-bar-location"]'
        )
        search_button = self.__browser.find_element(
            By.CSS_SELECTOR,
            '[data-tracking-control-name="public_jobs_jobs-search-bar_base-search-bar-search-submit"]',
        )

        term_search.clear()
        location_search.clear()

        term_search.send_keys(self.search_term)
        location_search.send_keys(self.location)

        search_button.click()

    def __get_sidebar_offers(self) -> list[WebElement]:
        job_offer_sidebar_ul = self.__browser.find_element(
            By.CSS_SELECTOR, "ul.jobs-search__results-list"
        )

        return job_offer_sidebar_ul.find_elements(By.TAG_NAME, "li")

    def __load_n_offers(self, number_to_load: int) -> None:
        print(f"Scrolling down the window to load minimum {number_to_load} offers ..")
        offer_num: int = len(self.__get_sidebar_offers())

        while offer_num < number_to_load:
            self.__browser.execute_script("window.scroll(0, 0)")

            self.__browser.execute_script(
                "window.scroll({left:0, top: document.body.scrollHeight, behavior: 'smooth'})"
            )
            time.sleep(3)
            offer_num = len(self.__get_sidebar_offers())

            more_jobs_btn = self.__browser.find_element(
                By.CSS_SELECTOR,
                '[data-tracking-control-name="infinite-scroller_show-more"]',
            )
            offset_parent = self.__browser.execute_script(
                "return arguments[0].offsetParent;", more_jobs_btn
            )

            # If the "show more jobs" button appears in the DOM,
            # then break out of the loop regardless of the number of loaded offers.
            if offset_parent:
                if offer_num < number_to_load:
                    print(
                        f"Could not load the given minimum {number_to_load} number of offers."
                    )
                print(f"{offer_num} offers are loaded in total to be parsed.")
                break

        self.__browser.execute_script("window.scroll(0, 0)")

    def __fetch_language_counter(self, offer_html: str) -> None:
        offer_html = offer_html.lower()

        for lang, lang_keywords in self.__language_synonyms.items():
            has_keyword = False
            for keyword in lang_keywords:
                if f" {keyword.lower()} " in offer_html:
                    has_keyword = True

            if has_keyword:
                self.language_counter[lang] += 1

    def __fetch_framework_counter(self, offer_html: str) -> None:
        offer_html = offer_html.lower()

        for framework in self.framework_counter.keys():
            if f" {framework.lower()} " in offer_html:
                self.framework_counter[framework] += 1

    def __iterate_offers(self) -> None:
        print("Starting to parse the offers ..")
        for offer_index in tqdm(range(0, len(self.offer_elements))):
            offer = self.offer_elements[offer_index]

            offer.click()
            trying_to_expand = True

            while trying_to_expand:
                try:
                    time.sleep(1)
                    expand_button = self.__browser.find_element(
                        By.CSS_SELECTOR,
                        '[data-tracking-control-name="public_jobs_show-more-html-btn"]',
                    )
                    expand_button.click()
                    trying_to_expand = False
                except Exception:
                    # If the offer is not loaded for the first time.
                    # Click to the previous one and retry.
                    # It can be probably, because of the robot.
                    if offer_index > 0:
                        self.offer_elements[offer_index - 1].click()
                    else:
                        self.offer_elements[0].click()

                    time.sleep(2)

                    expand_button = self.__browser.find_element(
                        By.CSS_SELECTOR,
                        '[data-tracking-control-name="public_jobs_show-more-html-btn"]',
                    )
                    offer.click()

            self.__element_waiter.until(
                EC.visibility_of_element_located(
                    (By.CSS_SELECTOR, "div.show-more-less-html__markup")
                )
            )

            job_offer_text_div = self.__browser.find_element(
                By.CSS_SELECTOR, "div.show-more-less-html__markup"
            )
            offer_html = job_offer_text_div.get_attribute("innerHTML")

            if offer_html:
                self.__fetch_language_counter(offer_html)
                self.__fetch_framework_counter(offer_html)

            time.sleep(1)


def generate_languages_plot(
    language_counter: dict[str, int], output_dir: str, search_term: str, location: str
) -> None:
    language_counter = dict(
        sorted(language_counter.items(), key=lambda x: x[1], reverse=True)
    )
    languages: list[str] = list(language_counter.keys())
    summary: list[int] = list(language_counter.values())
    plt.figure(figsize=(10, 6))
    plt.bar(languages, summary)
    plt.xticks(rotation=90)
    plt.xlabel("Programming languages")
    plt.ylabel("Summary")
    plt.title(
        f"Summary of found programming languages  [{str(datetime.datetime.now())}] {location} {search_term}"
    )
    plt.tight_layout()
    plt.savefig(f"{output_dir}/languages-counter.png")


def generate_frameworks_plot(
    framework_counter, output_dir: str, search_term: str, location: str
) -> None:
    framework_counter = dict(
        sorted(framework_counter.items(), key=lambda x: x[1], reverse=True)
    )
    languages: list[str] = list(framework_counter.keys())
    summary: list[int] = list(framework_counter.values())

    plt.figure(figsize=(10, 6))
    plt.bar(languages, summary)
    plt.xticks(rotation=90)
    plt.xlabel("Programming frameworks")
    plt.ylabel("Summary")
    plt.title(
        f"Summary of found programming frameworks [{str(datetime.datetime.now())}] {location} {search_term}"
    )
    plt.tight_layout()
    plt.savefig(f"{output_dir}/frameworks-counter.png")


def __main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Parse LinkedIn offers for languages, frameworks, etc..",
        formatter_class=argparse.RawTextHelpFormatter,
    )
    parser.add_argument(
        "-s",
        "--search-term",
        dest="search_term",
        action="store",
        type=str,
        default="",
        help='Search term, like "backend" or "frontend".',
    )

    parser.add_argument(
        "-l",
        "--location",
        dest="location",
        action="store",
        type=str,
        default="",
        help="Location of the offers.",
    )

    parser.add_argument(
        "-n",
        "--offer-num",
        dest="offer_num",
        action="store",
        type=int,
        default=25,
        help="Minimum number of offers to be parsed to get the plots.",
    )

    parser.add_argument(
        "--headless",
        dest="headless",
        action="store_true",
        help="Run the parsing in the background, without opening up the robot browser.",
    )

    parser.add_argument(
        "--as-plots",
        dest="as_plots",
        action="store_true",
        help="Save results as plots instead of tsv .",
    )

    parser.add_argument(
        "--plot-output",
        dest="plot_output",
        action="store",
        type=str,
        default="./plot-output",
        help=(
            "Output directory of the plots. If directory doesn't exist, it's created auto."
            'The default outputs can be found in the script\'s directory ".plot-output"'
        ),
    )
    args = parser.parse_args(argv)

    print("Connecting to LinkedIn")
    linkedin_offers = LinkedInOffers(
        search_term=args.search_term,
        location=args.location,
        offer_num_to_load=args.offer_num,
        headless=args.headless,
    )

    if args.plot_output != "./plot-output" and not args.as_plots:
        raise ValueError("--plot_output only can be used with --as-plots")

    if args.as_plots:
        print("Saving output plots ...")
        now: str = str(datetime.datetime.now())
        curr_output_dir: str = (
            f"{args.plot_output}/{re.sub(r':| ', '-', now).split('.')[0]}"
        )
        os.makedirs(curr_output_dir, exist_ok=True)
        generate_languages_plot(
            linkedin_offers.language_counter,
            curr_output_dir,
            args.search_term,
            args.location,
        )
        generate_frameworks_plot(
            linkedin_offers.framework_counter,
            curr_output_dir,
            args.search_term,
            args.location,
        )
        print(f'Result plots can be found in "{curr_output_dir}"')
    else:
        print("Language \t Counter")
        for key, value in linkedin_offers.language_counter.items():
            print(f"{key} \t {value}")

        print("\n", "=" * 10, "\n")

        print("Framework \t Counter")
        for key, value in linkedin_offers.framework_counter.items():
            print(f"{key} \t {value}")

        pass

    return 0


if __name__ == "__main__":
    raise SystemExit(__main())
