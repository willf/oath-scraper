import re
import json
from bs4 import BeautifulSoup
import time
from playwright.sync_api import sync_playwright
import os
import csv

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
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


def extract_sw_features(text):
    # Friend John (male, adolescent, free, Athenian)
    # returns ("Friend John", "male", "adolescent", "free", "Athenian")
    # Chorus (male) (n/a, mature, free, n/a)
    # returns ("Chorus (male)", "n/a", "mature", "free", "n/a")
    number_of_left_parens = text.count("(")
    number_of_right_parens = text.count(")")
    if number_of_left_parens != number_of_right_parens and number_of_left_parens != 1:

    first_div = "(".join(text.split("(")[0:1]).strip()
    second_div = text.split("(")[-1].strip()[0:-1]
    second_div_parts = second_div.split(",")
    if len(second_div_parts) != 4:
        print(
            "Problem with second_div_parts (should be four)",
            second_div,
            second_div_parts,
        )
        return (first_div, "", "", "", "")
    return (
        first_div,
        second_div_parts[0].strip(),
        second_div_parts[1].strip(),
        second_div_parts[2].strip(),
        second_div_parts[3].strip(),
    )


def extract_features(html):
    soup = BeautifulSoup(html, "html.parser")
    # get id from title <title> Oath 2595 results - Oaths in Archaic and Classical Greece </title> -> 2595
    title = soup.find("title").get_text(strip=True)
    oath_id = int(title.split()[1])
    yield ("oath_id", oath_id)
    # get h2 element inside #content from <div id="content" class="feature"><br><h2><strong>Oath ID 2: Aristophanes, <em>Clouds</em>, 82-83,</strong> (literary, Comic., )</h2><br>
    h2 = soup.select_one("#content h2")
    if h2:
        strong_text = h2.find("strong").get_text(strip=True)
        em_text = h2.find("em").get_text(strip=True)
        all_text = h2.get_text(strip=True)
        rev_text = all_text[::-1]
        tgd_text = re.search(r"\)([^)]+)\(", rev_text).group(1)[::-1]
        post_colon_text = ":".join(strong_text.split(":")[1:])
        post_colon_text_parts = post_colon_text.split(",")
        if len(post_colon_text_parts) < 4:
            print(
                "Problem with post_colon_text_parts (should be at least four)",
                post_colon_text,
                "$".join(post_colon_text_parts),
            )
        author = post_colon_text_parts[0].strip()
        work = em_text.strip()
        reference = ",".join(post_colon_text_parts[2:]).strip()[
            :-1
        ]  # drop last character which is a comma
        tgd_parts = tgd_text.split(",")
        if len(tgd_parts) != 3:
            print(
                "Problem with tgd_parts (should be three)",
                tgd_text,
                "$".join(tgd_parts),
            )
        work_type = tgd_parts[0].strip()
        genre = tgd_parts[1].strip()
        work_date = tgd_parts[2].strip()
        yield ("author", author)
        yield ("work", work)
        yield ("reference", reference)
        yield ("work_type", work_type)
        yield ("genre", genre)
        yield ("work_date", work_date)

    rows = soup.find_all("tr")
    for row in rows:
        tds = row.find_all("td")
        if len(tds) >= 2:
            feature_name = tds[1].get_text(strip=True)
            if feature_name.endswith(":"):
                feature_value = tds[2].get_text(strip=True)
                if feature_name == "Swearer:":
                    swearer, gender, age, status, origin = extract_sw_features(
                        feature_value
                    )
                    yield ("swearer", swearer)
                    yield ("swearer-gender", gender)
                    yield ("swearer-age", age)
                    yield ("swearer-status", status)
                    yield ("swearer-origin", origin)
                elif feature_name == "Swearee:":
                    swearee, gender, age, status, origin = extract_sw_features(
                        feature_value
                    )
                    yield ("swearee", swearee)
                    yield ("swearee-gender", gender)
                    yield ("swearee-age", age)
                    yield ("swearee-status", status)
                    yield ("swearee-origin", origin)
                else:
                    yield (feature_name[:-1], feature_value)


def get_features_for_range(start, end):
    with sync_playwright() as p:
        print("Launching browser")
        browser = p.webkit.launch(headless=True)
        all_features = []
        for number in range(start, end + 1):
            url = page(number)
            html = get_page_content(url, browser)
            if page_is_invalid(html):
                print(f"Invalid page for oath {number}")
                time.sleep(60)
                continue
            tuples = list(extract_features(html))
            features = dict(tuples)
            print(f"Extracted features for oath {number}: {features}")
            all_features.append(features)
            if number != end:
                time.sleep(10)
    return json.dumps(all_features)


def get_page_content(n, browser):
    page = browser.new_page()
    page.goto("https://www.nottingham.ac.uk/~brzoaths/database/")
    page.locator("#oathReferenceID").click()
    page.locator("#oathReferenceID").fill(f"{n}")
    page.get_by_role("button", name="Search").first.click()
    page.wait_for_load_state("load")
    return page.content()


def get_files_for_range(start, end):
    with sync_playwright() as p:
        print("Launching browser")
        browser = p.webkit.launch(headless=True)
        for number in range(start, end + 1):
            # check if oath is already downloaded
            if os.path.exists(f"oaths/{number}.html"):
                print(f"Oath {number} already downloaded")
                continue
            html = get_page_content(number, browser)
            with open(f"oaths/{number}.html", "w") as f:
                f.write(html)
            print(f"Downloaded oath {number}")


def get_features_from_files(directory):
    # grab all *.html file in this directory and extract features
    all_features = []
    for file in os.listdir(directory):
        if file.endswith(".html"):
            with open(directory + "/" + file, "r", errors="ignore") as f:
                print("Extracting features from", file)
                html = f.read()
                try:
                    tuples = list(extract_features(html))
                except Exception as e:
                    print("Error extracting features from", file)
                    print(e)
                    continue
                features = dict(tuples)
                all_features.append(features)
    return json.dumps(all_features)


def convert_json_to_csv(json_data, csv_file_path):
    data = json.loads(json_data)
    if not data:
        return

    # Extract headers from the first dictionary
    headers = data[0].keys()

    with open(csv_file_path, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=headers)
        writer.writeheader()
        for row in data:
            writer.writerow(row)


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
    features_json = get_features_from_files("oaths")
    # print(features_json)
    convert_json_to_csv(features_json, "all_features.csv")
    # get_files_for_range(2, 3885)
