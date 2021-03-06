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
    nvlog.debug("Starting requests session...")
    session = requests_html.HTMLSession()
    nvlog.info(f"Making GET request: url={url}")
    response = session.get(url)
    nvlog.info(f"Response received ({response.status_code})")
    nvlog.debug("Rendering dynamic content...")
    response.html.render()
    nvlog.debug("Rendered dynamic content")
    session.close()
    nvlog.debug("Session closed")
    return response.html.raw_html


def parse(responseStr: str, parser: str = 'lxml') -> BeautifulSoup:
    nvlog.info(f"Parsing response: parser={parser}")
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
        nvlog.debug("Attempting to parse div text as JSON...")
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


def saveJson(filename: str, jsonDict: dict):
    with open(filename, 'w') as f:
        json.dump(jsonDict, f, indent=4)


def isMatch(filename: str, jsonDict: dict):
    with open(filename, 'r') as f:
        fileDict = json.load(f)
    if jsonDict == fileDict:
        return True
    return False

filename = "data.json"
classname = "NVGFT070" #"DUAL-RTX3070-8G" 

mainlog.info("nvscrape starting...")
r = htmlRequest("https://www.nvidia.com/en-gb/shop/geforce/gpu/?page=1" +
                "&limit=9&locale=en-gb&category=GPU&gpu=RTX%203070")
soup = parse(r)
rtx3070info = itemJson(getDiv(soup, classname)) # "NVGFT070"))

if not os.path.isfile(filename):
    saveJson(filename, rtx3070info)
    mainlog.info("Creating json file for reference")
mainlog.info(f"Length of item(s) JSON: {len(rtx3070info)}")

if not isMatch(filename, rtx3070info) and rtx3070info:
    mainlog.info("Change detected")
    if not isinstance(rtx3070info, list):
        rtx3070info = [rtx3070info]
    links = []
    for dic in rtx3070info:
        links.extend(getValues(dic, "directPurchaseLink", "purchaseLink"))
    linksStr = ", ".join([link for link in links if link])
    sl = SlackNotification(os.environ["SLACK_API_TOKEN"])
    sl.setBody(f"Change detected!\nTry these links: {linksStr}\nBonus: " +
               "https://secure.scan.co.uk/web/basket/addproduct/3236417")
    sl.send()
    saveJson(filename, rtx3070info)
