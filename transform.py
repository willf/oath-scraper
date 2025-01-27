import re
import json
from bs4 import BeautifulSoup
import os
import sys


def err_print(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)


def strip_commas(text):
    """
    strip commas if on ends of the text
    """
    return text.strip().strip(",").strip()


def handle_element_default(name, element):
    # convert br to p
    for br in element.find_all("br"):
        br.replace_with("\n")
    yield name, element.get_text().strip()


def handle_title(name, element):
    # Implement handling of title
    yield from handle_element_default(name, element)


def handle_h2(name, element):
    "<h2><strong>Oath ID 3885: Euripides, <em>Iphigenia Aulidensis</em>, 1006-7,</strong> (literary, Trag., 405)</h2>"
    text = str(element)
    match = re.search(r"<h2><strong>Oath ID \d+: (.*?)<em>", text)
    if not match:
        err_print("Problem with match finding author", text)
    else:
        author = match.group(1).strip()
        yield "author", strip_commas(author)
    work_title = element.find("em").get_text(strip=True)
    if work_title:
        yield "title", strip_commas(work_title)
    match = re.search(r"</em>(.*?),</strong>", text)
    if not match:
        err_print("Problem with match finding reference", text)
    else:
        reference = match.group(1).strip()
        yield "reference", strip_commas(reference)
    match = re.search(r"</strong>\s*(.*?)\s*</h2>", text)
    if not match:
        err_print("Problem with finding meta text", text)
        return
    parts3 = match.group(1)[1:-1].split(",")
    if len(parts3) != 3:
        err_print("Problem with parts3 (should be three)", parts3)
    else:
        work_type = parts3[0].strip()
        genre = parts3[1].strip()
        work_date = parts3[2].strip()
        yield "work_type", strip_commas(work_type)
        yield "genre", strip_commas(genre)
        yield "work_date", strip_commas(work_date)


def handle_date(name, element):
    # Implement handling of date
    yield from handle_element_default(name, element)


def handle_reference_type(name, element):
    # Implement handling of reference type
    yield from handle_element_default(name, element)


def handle_state(name, element):
    # Implement handling of state
    yield from handle_element_default(name, element)


def handle_sw_row(stype, element):
    text = element.get_text(strip=True)
    match = re.search(r"^(.*?)(\((?:male|female|n/a).*)", text)
    if not match:
        err_print(f"Problem with match finding {stype}", text)
    else:
        part_before = match.group(1).strip()
        part_after = match.group(2).strip()
        # remove parens
        part_after = part_after[1:-1]
        parts = part_after.split(",")
        if len(parts) != 4:
            err_print("Problem with parts (should be four)", parts)
        else:
            gender = parts[0].strip()
            age = parts[1].strip()
            status = parts[2].strip()
            origin = parts[3].strip()
            if gender == "n/a":
                if "(female)" in part_before:
                    gender = "female"
                elif "(male)" in part_before:
                    gender = "male"
            agent = part_before
            dict = {
                "agent": agent,
                "gender": gender,
                "age": age,
                "status": status,
                "origin": origin,
            }
            yield stype, dict
    # yield from handle_element_default(stype, element)


def handle_swearer(name, element):
    # Implement handling of swearer
    l = []
    for row in element.find_all("tr"):
        _, b = handle_sw_row("swearer", row).__next__()
        l.append(b)
    yield "swearer", l


def handle_swearee(name, element):
    # Implement handling of swearee
    l = []
    for row in element.find_all("tr"):
        _, b = handle_sw_row("swearee", row).__next__()
        l.append(b)
    yield "swearee", l


def handle_proposed_by(name, element):
    l = []
    for row in element.find_all("tr"):
        text = row.get_text(strip=True)
        l.append(text)
    yield name, l


def handle_if_taken(name, element):
    # Implement handling of if taken
    yield from handle_element_default(name, element)


def handle_if_refused(name, element):
    # Implement handling of if refused
    yield from handle_element_default(name, element)


def handle_if_kept(name, element):
    # Implement handling of if kept
    yield from handle_element_default(name, element)


def handle_if_broken(name, element):
    # Implement handling of if broken
    yield from handle_element_default(name, element)


def handle_taken(name, element):
    # Implement handling of taken
    yield from handle_element_default(name, element)


def handle_impact(name, element):
    # Implement handling of impact
    yield from handle_element_default(name, element)


def handle_consequences_of_breach(name, element):
    # Implement handling of consequences of breach
    yield from handle_element_default(name, element)


def handle_statement(name, element):
    # Implement handling of statement
    yield from handle_element_default(name, element)


def handle_linguistic(name, element):
    # Implement handling of linguistic
    yield from handle_element_default(name, element)


def handle_gods_invoked(name, element):
    l = []
    for row in element.find_all("tr"):
        god = row.get_text(strip=True)
        l.append(god)
    yield name, l


def handle_remarks(name, element):
    # Implement handling of remarks
    yield from handle_element_default(name, element)


class Scraper:
    def __init__(self):
        self.soup = None
        self.current_file = None
        self.handlers = {
            "title": handle_title,
            "date": handle_date,
            "reference_type": handle_reference_type,
            "state": handle_state,
            "swearer": handle_swearer,
            "swearee": handle_swearee,
            "proposed_by": handle_proposed_by,
            "if_taken": handle_if_taken,
            "if_refused": handle_if_refused,
            "if_kept": handle_if_kept,
            "if_broken": handle_if_broken,
            "taken": handle_taken,
            "impact": handle_impact,
            "consequences_of_breach": handle_consequences_of_breach,
            "statement": handle_statement,
            "linguistic": handle_linguistic,
            "gods_invoked": handle_gods_invoked,
            "remarks": handle_remarks,
        }

    def soupify(self, text):
        self.soup = BeautifulSoup(text, "html.parser")

    def extract_features(self):
        title = self.soup.find("title")
        if title:
            # get id from title <title> Oath 2595 results - Oaths in Archaic and Classical Greece </title> -> 2595
            title = str(title.get_text(strip=True))
            try:
                oath_id = int(title.split()[1])
            except ValueError:
                err_print(
                    f"Problem with oath_id in {self.current_file}; title: {title}"
                )
                return
            yield "oath_id", oath_id
        h2 = self.soup.select_one("#content h2")
        if h2:
            yield from handle_h2("title", h2)
        rows = table_rows(self.soup)
        filtered_rows = filter_to_features(rows)
        for td, value in filtered_rows:
            feature_name = feature_name_from_td(td)
            handler = self.handlers.get(feature_name)
            if handler:
                yield from handler(feature_name, value)
            else:
                err_print("No handler for", feature_name)
                yield from handle_element_default(feature_name, value)

    def extact_features_to_dict(self):
        return dict(self.extract_features())


# headers = {
#     "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/104.0.5112.79 Safari/537.36",
# }


# def page(number):
#     return f"https://www.nottingham.ac.uk/~brzoaths/database/oath_reference_details.php?oathID={number}&referenceTypeID=&authorIDName=&workID=0&workCategory=&workGenre=&takenStateID=0&Fictional=U&markerID=&sanctifyingCircumstances=N&oathDate=&invokedGodID=0&swearerID=0&sweareeID=0&swearerStateID=0&sweareeStateID=0&swearerStatus=&sweareeStatus=&swearerAgeClass=&sweareeAgeClass=&swearerGenderID=&sweareeGenderID=&centuryID=0&Taken=U&Fulfilled=U"


# def page_is_invalid(html):
#     return (
#         "Error - unable to retrieve work" in html or "You have been timed out" in html
#     )


# def get_page_content(url: str, browser):
#     page = browser.new_page()
#     page.goto(url)
#     return page.content()


# def extract_sw_features(text):
#     # Friend John (male, adolescent, free, Athenian)
#     # returns ("Friend John", "male", "adolescent", "free", "Athenian")
#     # Chorus (male) (n/a, mature, free, n/a)
#     # returns ("Chorus (male)", "n/a", "mature", "free", "n/a")
#     number_of_left_parens = text.count("(")
#     number_of_right_parens = text.count(")")
#     if (number_of_left_parens != number_of_right_parens) or (
#         number_of_left_parens != 1
#     ):
#         err_print(
#             "Problem with number of parens (should be one of each)",
#             number_of_left_parens,
#             number_of_right_parens,
#         )
#         return (text, "", "", "", "")
#     first_div = "(".join(text.split("(")[0:1]).strip()
#     second_div = text.split("(")[-1].strip()[0:-1]
#     second_div_parts = second_div.split(",")
#     if len(second_div_parts) != 4:
#         err_print(
#             "Problem with second_div_parts (should be four)",
#             second_div,
#             second_div_parts,
#         )
#         return (first_div, "", "", "", "")
#     return (
#         first_div,
#         second_div_parts[0].strip(),
#         second_div_parts[1].strip(),
#         second_div_parts[2].strip(),
#         second_div_parts[3].strip(),
#     )


def table_rows(soup):
    """
    Get a list of the table rows for the first table under the div with id 'content'
    """
    div = soup.find(id="content")
    if not div:
        return []
    table = div.find("table")
    if not table:
        return []
    return div.find_all("tr")


def filter_to_features(rows):
    """
    Filter out rows that are not features
    """
    for row in rows:
        tds = row.find_all("td")
        if len(tds) >= 2:
            feature_name = tds[1].get_text(strip=True)
            if feature_name.endswith(":"):
                yield tds[1], tds[2]


def feature_name_from_td(td):
    """
    Convert to feature name from td
    """
    text = td.get_text(strip=True)[:-1].lower()
    text = text.replace("(", "")
    text = text.replace(")", "")
    return text.replace(" ", "_")


# def feature_value_from_td(td):
#     """
#     Convert to feature value from td. if td contains a table,
#     return a list of the tds from the table, otherwise return the td
#     """
#     table = td.find("table")
#     if table:
#         return table.find_all("td")
#     return td.get_text(strip=True)


# def list_all_feature_names(html):
#     soup = BeautifulSoup(html, "html.parser")
#     rows = table_rows(soup)
#     return [feature_name_from_td(td) for td, _ in filter_to_features(rows)]


# def extract_features(html):
#     soup = BeautifulSoup(html, "html.parser")
#     # get id from title <title> Oath 2595 results - Oaths in Archaic and Classical Greece </title> -> 2595
#     title = soup.find("title").get_text(strip=True)
#     oath_id = int(title.split()[1])
#     yield ("oath_id", oath_id)
#     # get h2 element inside #content from <div id="content" class="feature"><br><h2><strong>Oath ID 2: Aristophanes, <em>Clouds</em>, 82-83,</strong> (literary, Comic., )</h2><br>
#     h2 = soup.select_one("#content h2")
#     if h2:
#         strong_text = h2.find("strong").get_text(strip=True)
#         em_text = h2.find("em").get_text(strip=True)
#         all_text = h2.get_text(strip=True)
#         rev_text = all_text[::-1]
#         tgd_text = re.search(r"\)([^)]+)\(", rev_text).group(1)[::-1]
#         post_colon_text = ":".join(strong_text.split(":")[1:])
#         post_colon_text_parts = post_colon_text.split(",")
#         if len(post_colon_text_parts) < 4:
#             err_print(
#                 "Problem with post_colon_text_parts (should be at least four)",
#                 post_colon_text,
#                 "$".join(post_colon_text_parts),
#             )
#         author = post_colon_text_parts[0].strip()
#         work = em_text.strip()
#         reference = ",".join(post_colon_text_parts[2:]).strip()[
#             :-1
#         ]  # drop last character which is a comma
#         tgd_parts = tgd_text[1:-1].split(",")
#         if len(tgd_parts) != 3:
#             err_print(
#                 "Problem with tgd_parts (should be three)",
#                 tgd_text,
#                 "$".join(tgd_parts),
#             )
#         work_type = tgd_parts[0].strip()
#         genre = tgd_parts[1].strip()
#         work_date = tgd_parts[2].strip()
#         yield ("author", author)
#         yield ("work", work)
#         yield ("reference", reference)
#         yield ("work_type", work_type)
#         yield ("genre", genre)
#         yield ("work_date", work_date)

#     rows = soup.find_all("tr")
#     for row in rows:
#         tds = row.find_all("td")
#         if len(tds) >= 2:
#             feature_name = tds[1].get_text(strip=True)
#             if feature_name.endswith(":"):
#                 feature_value = tds[2].get_text(strip=True)
#                 yield (feature_name[:-1], feature_value)


# def get_features_for_range(start, end):
#     with sync_playwright() as p:
#         err_print("Launching browser")
#         browser = p.webkit.launch(headless=True)
#         all_features = []
#         for number in range(start, end + 1):
#             url = page(number)
#             html = get_page_content(url, browser)
#             if page_is_invalid(html):
#                 err_print(f"Invalid page for oath {number}")
#                 time.sleep(60)
#                 continue
#             tuples = list(extract_features(html))
#             features = dict(tuples)
#             err_print(f"Extracted features for oath {number}: {features}")
#             all_features.append(features)
#             if number != end:
#                 time.sleep(10)
#     return json.dumps(all_features)


# def get_page_content(n, browser):
#     page = browser.new_page()
#     page.goto("https://www.nottingham.ac.uk/~brzoaths/database/")
#     page.locator("#oathReferenceID").click()
#     page.locator("#oathReferenceID").fill(f"{n}")
#     page.get_by_role("button", name="Search").first.click()
#     page.wait_for_load_state("load")
#     return page.content()


# def get_files_for_range(start, end):
#     with sync_playwright() as p:
#         err_print("Launching browser")
#         browser = p.webkit.launch(headless=True)
#         for number in range(start, end + 1):
#             # check if oath is already downloaded
#             if os.path.exists(f"oaths/{number}.html"):
#                 err_print(f"Oath {number} already downloaded")
#                 continue
#             html = get_page_content(number, browser)
#             with open(f"oaths/{number}.html", "w") as f:
#                 f.write(html)
#             err_print(f"Downloaded oath {number}")


# def get_features_from_files(directory):
#     # grab all *.html file in this directory and extract features
#     all_features = []
#     for file in os.listdir(directory):
#         if file.endswith(".html"):
#             with open(directory + "/" + file, "r", errors="ignore") as f:
#                 err_print("Extracting features from", file)
#                 html = f.read()
#                 try:
#                     tuples = list(extract_features(html))
#                 except Exception as e:
#                     err_print("Error extracting features from", file)
#                     err_print(e)
#                     continue
#                 features = dict(tuples)
#                 all_features.append(features)
#     return json.dumps(all_features)


# def convert_json_to_csv(json_data, csv_file_path):
#     data = json.loads(json_data)
#     if not data:
#         return

#     # Extract headers from the first dictionary
#     headers = data[0].keys()

#     with open(csv_file_path, "w", newline="") as csvfile:
#         writer = csv.DictWriter(csvfile, fieldnames=headers)
#         writer.writeheader()
#         for row in data:
#             writer.writerow(row)


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
    # features_json = get_features_from_files("oaths")
    # err_print(features_json)
    # convert_json_to_csv(features_json, "all_features.csv")
    # get_files_for_range(2, 3885)
    scraper = Scraper()
    html = example_html
    args = sys.argv[1:]
    if args:
        # is it a directory?
        if os.path.isdir(args[0]):
            for file in os.listdir(args[0]):
                scraper.current_file = file
                if file.endswith(".html"):
                    with open(args[0] + "/" + file, "r", errors="ignore") as f:
                        html = f.read()
                        scraper.soupify(html)
                        features = scraper.extact_features_to_dict()
                        features_json = json.dumps(features)
                        print(features_json)
        else:
            with open(args[0], "r") as f:
                scraper.current_file = args[0]
                html = f.read()
                scraper.soupify(html)
                features = scraper.extact_features_to_dict()
                features_json = json.dumps(features)
                print(features_json)
    else:
        scraper.soupify(html)
        features = scraper.extact_features_to_dict()
        features_json = json.dumps(features)
        print(features_json)
