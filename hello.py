import requests
import json
from bs4 import BeautifulSoup
import time
from playwright.sync_api import sync_playwright

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/132.0.0.0 Safari/537.36",
}


def page(number):
    return f"https://www.nottingham.ac.uk/~brzoaths/database/oath_reference_details.php?oathID={number}&referenceTypeID=&authorIDName=&workID=0&workCategory=&workGenre=&takenStateID=0&Fictional=U&markerID=&sanctifyingCircumstances=N&oathDate=&invokedGodID=0&swearerID=0&sweareeID=0&swearerStateID=0&sweareeStateID=0&swearerStatus=&sweareeStatus=&swearerAgeClass=&sweareeAgeClass=&swearerGenderID=&sweareeGenderID=&centuryID=0&Taken=U&Fulfilled=U"


def page_is_invalid(html):
    return (
        "Error - unable to retrieve work" in html or "You have been timed out" in html
    )


def get_page_content(url: str, browser):
    page = browser.new_page()
    page.goto(url)
    return page.content()


def extract_features(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = soup.find_all("tr")
    for row in rows:
        tds = row.find_all("td")
        if len(tds) >= 2:
            feature_name = tds[1].get_text(strip=True)
            if feature_name.endswith(":"):
                feature_value = tds[2].get_text(strip=True)
                yield (feature_name[:-1], feature_value)


def get_features_for_range(start, end):
    with sync_playwright() as p:
        print("Launching browser")
        browser = p.chromium.launch(headless=True)
        all_features = []
        for number in range(start, end + 1):
            url = page(number)
            html = get_page_content(url, browser)
            if page_is_invalid(html):
                print(f"Invalid page for oath {number}")
                continue
            tuples = list(extract_features(html))
            features = dict(tuples)
            print(f"Extracted features for oath {number}: {features}")
            all_features.append(features)
            if number != end:
                time.sleep(10)
    return json.dumps(all_features)


example_html = """

<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Transitional//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-transitional.dtd">
<html>
<head>
  <link href="../oaths.css" rel="stylesheet" type="text/css" />
  <title> Oath 3885 results - Oaths in Archaic and Classical Greece </title>
<script language="JavaScript" type="text/javascript">
<!--
function openwin ( url, wintype )
{
  window.name="mainwin"
  if ( wintype=="littlewin" )
    window.open ( url, wintype, 'toolbar=1,location=1,directories=0,menubar=1,scrollbars=1,resizeable=1,width=700,height=350' );
  else
  if ( wintype=="helpwin" )
    window.open ( url, wintype, 'toolbar=0,location=0,directories=0,menubar=0,scrollbars=1,resizeable=0,width=600,height=300' );
  else
  if ( wintype=="bigwin" )
    window.open ( url, wintype, 'toolbar=0,location=0,directories=0,menubar=1,scrollbars=1,resizeable=1,width=700,height=450' );
} /* openwin */

//-->
</script>
</head>

<body>

<img src="../images/unilogo.gif" alt="University Logo" width="180" height="54" class="left" />
<div id="toparealogo" class="right"></div>
<div id="masthead">
<p>&nbsp;</p><h1>THE OATH IN ARCHAIC AND CLASSICAL GREECE </h1>
  <h2 id="pageName">Database</h2>
<div id="breadCrumb"> <a href="#"></a></div>
</div>
<div id="navBar"><div id="sectionLinks"><h3> Links</h3>
    <ul>
      <li><a href="../index.php" title="Home Page">Home Page </a></li>
      <li><a href="../oath.php" title="What is an Oath?">What is an Oath? </a></li>
               <li><a href="../team.php" title="The Project Team">Project Team </a></li>
      <li><a href="../publications.php" title="Publications">Publications </a></li>
           <li><a href="../database.php" title="Project Database">Database</a></li>
      <li><a href="../Canon-Literary.xls" title=" Canon-Literary - Excel Spreadsheet">Canon (Literary)</a></li>
      <li><a href="#">  </a></li>
      <li><a href="mailto:Alan.Sommerstein@nottingham.ac.uk" title="Email the Project Director">Contact</a><a href="#"></a></li>
    </ul>
</div>
</div>
<div id="content" class="feature"><br /><h2><strong>Oath ID 3885: Euripides, <em>Iphigenia Aulidensis</em>, 1006-7,</strong> (literary, Trag., 405)</h2><br />
  <table width="100%">
    <tr>
      <td>
        &nbsp;
      </td>
      <td>
        Date:
      </td>
      <td colspan="4">
        <strong>mythical time</strong>
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td>
        Reference type:
      </td>
      <td colspan="4">
        <strong>Oath</strong>
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td>
        State:
      </td>
      <td>
        <strong>Aulis (in Boeotia)</strong>
      </td>
      <td width="10">
        &nbsp;
      </td>
      <td>
        Location:
      </td>
      <td>
        <strong>Outside Agamemnon's tent</strong>
      </td>
    </tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Swearer:
      </td>
      <td colspan="4">
        <table><tr><td><strong>Achilles (male, adolescent, power-holder, Phthian)</strong></td></tr></table>
      <td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Swearee:
      </td>
      <td colspan="4">
        <table><tr><td><strong>Clytemnestra (female, mature, power-holder, Argive)</strong></td></tr><tr><td><strong>Female chorus (n/a, adolescent, free, Chalcidician)</strong></td></tr></table>
      <td>
    </tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Proposed by:
      </td>
      <td colspan="4">
        <table><tr><td><strong>n/a</strong></td></tr></table>
      <td>
    </tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        If taken:
      </td>
      <td colspan="4">
        <strong>n/a</strong>
      <td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        If refused:
      </td>
      <td colspan="4">
        <strong>n/a</strong>
      <td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        If kept:
      </td>
      <td colspan="4">
        <strong>unknown</strong>
      <td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        If broken:
      </td>
      <td colspan="4">
        <strong>May he die</strong>
      <td>
    </tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td>
        Taken:
      </td>
      <td>
        <strong>yes</strong>
      </td>
      <td>
        &nbsp;
      </td>
      <td>
        True:
      </td>
      <td>
        <strong>yes</strong>
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Impact:
      </td>
      <td colspan="4">
        <strong>Clytemnestra is grateful for Achilles' support</strong>
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td colspan="2">
        Consequences of breach:
      </td>
      <td colspan="2">
        <strong>n/a</strong>
      </td>
    </tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Sanctifying features
      </td>
      <td colspan="4">
        <strong>none</strong>
      <td>
    </tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Statement:
      </td>
      <td colspan="4">
        <strong>[That he will never lie or deceive anyone] &psi;&epsilon;&upsilon;&delta;&#8134; &lambda;&#8051;&gamma;&omega;&nu; &delta;&#8050; &kappa;&alpha;&#8054; &mu;&#8049;&tau;&eta;&nu; &#7952;&gamma;&kappa;&epsilon;&rho;&tau;&omicron;&mu;&#8182;&nu;, &theta;&#8049;&nu;&omicron;&iota;&mu;&iota;</strong>
      <td>
    </tr>
    <tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td>
        Linguistic:
       </td>
      <td colspan="4">
        <strong>self-curse</strong>
      <td>
    </tr>
    <tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        God(s) invoked:
      </td>
      <td colspan="4">
        <table width="100%">
      <tr>
        <td><strong>n/a</strong></td>
        <td>&nbsp;</td>
        <td>&nbsp;</td>
      </tr>
</table>
      <td>
    </tr>
    <tr>
    <tr>
      <td colspan="6">
        &nbsp;
      </td>
    </tr>
    <tr>
      <td>
        &nbsp;
      </td>
      <td valign="top">
        Remarks:
      </td>
      <td colspan="4">
        <strong>This serves to reinforce Achilles' previous sworn promise not to allow Iphigeneia to be sacrificed (see oath id 188).</strong>
      <td>
    </tr>
  </table>

<br /><p><a href="./reference_list.php?referenceTypeID=&authorIDName=&workID=&workCategory=&workGenre=&takenStateID=&Fictional=&markerID=&sanctifyingCircumstances=&oathDate=&invokedGodID=&swearerID=&sweareeID=&swearerStateID=&sweareeStateID=&swearerStatus=&sweareeStatus=&swearerAgeClass=&sweareeAgeClass=&swearerGenderID=&sweareeGenderID=&centuryID=&Taken=&Fulfilled=">Back to list</a>
<br /><p><a href="./index.php?referenceTypeID=&authorID=&workID=&workCategory=&workGenre=&takenStateID=&Fictional=&markerID=&sanctifyingCircumstances=&oathDate=&invokedGodID=&swearerID=&sweareeID=&swearerStateID=&sweareeStateID=&swearerStatus=&sweareeStatus=&swearerAgeClass=&sweareeAgeClass=&swearerGenderID=&sweareeGenderID=&centuryID=&Taken=&Fulfilled=">Search again?</a>
 </div> </body>
</html>
"""

if __name__ == "__main__":
    # Example usage:
    features_json = get_features_for_range(3885, 3887)
    print(features_json)
