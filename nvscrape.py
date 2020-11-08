#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import requests_html
from bs4 import BeautifulSoup
from bs4.element import Tag as bs4Tag
import json
import logging
from logging import config as logconfig
import yaml
from notify import SlackNotification
import os


with open('nvlogger.yaml', 'r') as f:
    config = yaml.safe_load(f.read())
    logconfig.dictConfig(config)

nvlog = logging.getLogger("nv")
mainlog = logging.getLogger("main")


def htmlRequest(url: str) -> requests_html.HTMLResponse:
    nvlog.debug("Starting session...")
    session = requests_html.HTMLSession()
    nvlog.info(f"Making GET request: url={url}")
    response = session.get(url)
    nvlog.info(f"Response received ({response.status_code})")
    nvlog.debug("Rendering dynamic content...")
    response.html.render()
    nvlog.info("Rendered dynamic content")
    nvlog.debug("Closing session...")
    session.close()
    return response.html.raw_html


def parse(responseStr: str, parser: str = 'lxml') -> BeautifulSoup:
    nvlog.info(f"Parsing response: parser: {parser}")
    return BeautifulSoup(responseStr, parser)


def getDiv(parsedResponse: BeautifulSoup, className: str = None):
    nvlog.info(f"getDiv called: className={className}")
    if className is not None:
        div = parsedResponse.find("div", {"class": className})
    else:
        div = parsedResponse.find("div")
    nvlog.debug(f"div: {div}")
    return div


def getDivs(parsedResponse: BeautifulSoup, className: str = None) -> list:
    nvlog.info(f"getDivs called: className={className}")
    if className is not None:
        divs = parsedResponse.find_all("div", {"class": className})
    else:
        divs = parsedResponse.find_all("div")
    nvlog.debug(f"divs: {divs}")
    return divs


def itemJson(div: bs4Tag):
    try:
        nvlog.info("Attempting to parse div text as JSON...")
        return json.loads(div.text)
    except json.JSONDecodeError as e:
        nvlog.exception(e)

def getValues(dictionary: dict, *args) -> list:
    res = []
    for k in args:
        try:
            res.append(dictionary[k])
        except KeyError as e:
            nvlog.warning(f"key '{k}' not in {dictionary.keys()}")
            nvlog.exception(e)
            continue
    return res


r = htmlRequest("https://www.nvidia.com/en-gb/shop/geforce/gpu/?page=1" +
                "&limit=9&locale=en-gb&category=GPU&gpu=RTX%203070")
soup = parse(r)
rtx3070info = itemJson(getDiv(soup, "NVGFT070"))
if rtx3070info is not None:
    mainlog.info("Field no longer empty")
    if not isinstance(rtx3070info, list):
        rtx3070info = [rtx3070info]
    links = []
    for dic in rtx3070info:
        print(dic)
        links.extend(getValues(dic, "directPurchaseLink", "purchaseLink"))
    linksStr = ", ".join([link for link in links if link])
    sl = SlackNotification(os.environ["SLACK_API_TOKEN"])
    sl.setBody(f"Change detected!\nTry these links: {linksStr}\nBonus: " +
               "https://secure.scan.co.uk/web/basket/addproduct/3236417")
    sl.send()
