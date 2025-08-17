import requests
from collections import defaultdict

# Reuse a single HTTP session for all downloads to avoid repeated TCP
# handshakes and keep the code easier to test.
session = requests.Session()


def addPretext(lines, sectionName, subURL):
    modified_lines = []
    currSubCat = ""
    currSubSubCat = ""

    #Remove from the lines any line that isnt a heading and doesnt contain the character `⭐`
    #lines = [line for line in lines if line.startswith("#") or '⭐' in line]

    #Parse headings
    for line in lines:
        if line.startswith("#"): #Title Lines
            if subURL != "storage":
                if line.startswith("# ►"):
                    currSubCat = line.replace("# ►", "").strip()
                    currSubSubCat = "/"
                elif line.startswith("## ▷"):
                    currSubSubCat = line.replace("## ▷", "").strip()
            else:  # storage
                if line.startswith("## "):
                    currSubCat = line.replace("## ", "").strip()
                    currSubSubCat = "/"
                elif line.startswith("### "):
                    currSubSubCat = line.replace("### ", "").strip()

            # Remove links from subcategory titles (because they screw the format)
            if 'http' in currSubCat:
                currSubCat = ''
            if 'http' in currSubSubCat:
                currSubSubCat = ''

        elif any(char.isalpha() for char in line): #If line has content
            # Build a JSON-like prefix that encodes the current section and
            # category hierarchy. Using single quotes for the outer string keeps
            # the expression easy to read and avoids excessive escaping.
            preText = (
                f'{{"{sectionName.replace(".md", "")}", '
                f'"{currSubCat}", "{currSubSubCat}"}}'
            )
            if line.startswith("* "): line = line[2:]
            modified_lines.append(preText + line)

    return modified_lines


#----------------base64 page processing------------
import base64
import re

doBase64Decoding = True

def fix_base64_string(encoded_string):
    missing_padding = len(encoded_string) % 4
    if missing_padding != 0:
        encoded_string += '=' * (4 - missing_padding)
    return encoded_string

def decode_base64_in_backticks(input_string):
    def base64_decode(match):
        encoded_data = match.group(0)[1:-1]  # Extract content within backticks
        decoded_bytes = base64.b64decode( fix_base64_string(encoded_data) )
        return decoded_bytes.decode()

    pattern = r"`[^`]+`"  # Regex pattern to find substrings within backticks
    decoded_string = re.sub(pattern, base64_decode, input_string)
    return decoded_string

def remove_empty_lines(text):
    lines = text.split('\n')  # Split the text into lines
    non_empty_lines = [line for line in lines if line.strip()]  # Filter out empty lines
    return '\n'.join(non_empty_lines)  # Join non-empty lines back together

def extract_base64_sections(base64_page):
    sections = base64_page.split("***")  # Split the input string by "***" to get sections
    formatted_sections = []
    for section in sections:
        formatted_section = remove_empty_lines( section.strip().replace("#### ", "").replace("\n\n", " - ").replace("\n", ", ") )
        if doBase64Decoding: formatted_section = decode_base64_in_backticks(formatted_section)
        formatted_section = '[🔑Base64](https://rentry.co/FMHYBase64) ► ' + formatted_section
        formatted_sections.append(formatted_section)
    lines = formatted_sections
    return lines
#----------------</end>base64 page processing------------



def dlWikiChunk(fileName):

    # first, try to get the chunk locally
    try:
        print("Loading " + fileName + " from local file...")
        with open(fileName.lower(), 'r') as f:
            page = f.read()
        print("Loaded.\n")
    # if not available locally, download the chunk
    except FileNotFoundError:
        if fileName != 'base64.md':
            print("Local file not found. Downloading " + fileName + " from Github...")
            page = session.get(
                "https://raw.githubusercontent.com/fmhy/FMHYedit/main/docs/" + fileName.lower(),
                timeout=10,
            ).text
        else:
            print("Local file not found. Downloading rentry.co/FMHYBase64...")
            page = session.get("https://rentry.co/FMHYBase64/raw", timeout=10).text.replace("\r", "")
        print("Downloaded")

    if fileName != 'base64.md':
        subURL = fileName.replace(".md", "").lower()
        lines = addPretext(page.split('\n'), fileName, subURL)
    else:
        lines = extract_base64_sections(page)

    return lines

def cleanLineForSearchMatchChecks(line):
    siteBaseURL = "https://fmhy.net/"
    redditBaseURL = "https://www.reddit.com/r/FREEMEDIAHECKYEAH/wiki/"
    return line.replace(redditBaseURL, '/').replace(siteBaseURL, '/')

WIKI_FILES = [
    "VideoPiracyGuide.md",
    "AI.md",
    "Android-iOSGuide.md",
    "AudioPiracyGuide.md",
    "DownloadPiracyGuide.md",
    "EDUPiracyGuide.md",
    "GamingPiracyGuide.md",
    "AdblockVPNGuide.md",
    "System-Tools.md",
    "File-Tools.md",
    "Internet-Tools.md",
    "Social-Media-Tools.md",
    "Text-Tools.md",
    "Video-Tools.md",
    "MISCGuide.md",
    "ReadingPiracyGuide.md",
    "TorrentPiracyGuide.md",
    "img-tools.md",
    "gaming-tools.md",
    "LinuxGuide.md",
    "DEVTools.md",
    "Non-English.md",
    "STORAGE.md",
    # "base64.md",
    "NSFWPiracy.md",
]


def alternativeWikiIndexing():
    wikiChunks = [dlWikiChunk(name) for name in WIKI_FILES]
    return [item for sublist in wikiChunks for item in sublist]  # Flatten
#--------------------------------


# Save the result of alternativeWikiIndexing to a .md file
# with open('wiki_adapted.md', 'w') as f:
#     for line in alternativeWikiIndexing():
#         f.write(line + '\n')

# Instead of saving it to a file, save it into a string variable when run
# as a script to avoid heavy work during import.


def markdown_to_html_bookmarks(input_md_text, output_file, starred_only=False):
    # Predefined folder name
    folder_name = "FMHY"

    # Read the input markdown file
    #with open(input_file, 'r', encoding='utf-8') as f:
    #    markdown_content = f.read()

    # Instead of reading from a file, read from a string variable
    markdown_content = input_md_text

    # Regex pattern to extract URLs and titles from markdown
    url_pattern = re.compile(r'\[([^\]]+)\]\((https?://[^\)]+)\)')
    # Regex pattern to extract hierarchy levels
    hierarchy_pattern = re.compile(r'^\{"([^"]+)", "([^"]+)", "([^"]+)"\}')

    # Dictionary to hold bookmarks by hierarchy
    bookmarks = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))

    # Split the content by lines
    lines = markdown_content.split('\n')

    # Parse each line
    for line in lines:
        # Find hierarchy levels
        hierarchy_match = hierarchy_pattern.match(line)
        if not hierarchy_match:
            continue

        level1, level2, level3 = hierarchy_match.groups()

        # Find all matches in the line for URLs
        matches = url_pattern.findall(line)

        # When generating the "starred only" export, only use the first match
        if starred_only:
            matches = matches[:1]

        # Extract the description (text after the last match)
        last_match_end = line.rfind(')')
        description = line[last_match_end+1:].replace('**', '').strip() if last_match_end != -1 else ''

        # When the description is empty, use as description the lowest hierachy level that is not empty
        if not description:
            description = '- ' + (level3 if level3 != '/' else level2 if level2 else level1)

        # Add matches to the appropriate hierarchy
        for title, url in matches:
            full_title = f"{title} {description}" if description else title
            bookmarks[level1][level2][level3].append((full_title, url))

    # Function to generate HTML from nested dictionary
    def generate_html(bookmarks_dict, indent=1):
        html = ''
        for key, value in bookmarks_dict.items():
            # Some sections don't have a sub-sub category.  In those cases a
            # placeholder value of '/' is used during parsing so the hierarchy
            # always has three levels.  We don't actually want a folder named
            # '/' in the exported bookmarks, so when this placeholder is
            # encountered we simply render its children directly without
            # wrapping them in an extra <H3>/<DL> pair.
            if key == '/':
                if isinstance(value, dict):
                    html += generate_html(value, indent)
                else:
                    for full_title, url in value:
                        html += '    ' * indent + f'<DT><A HREF="{url}" ADD_DATE="0">{full_title}</A>\n'
                continue

            html += '    ' * indent + f'<DT><H3>{key}</H3>\n'
            html += '    ' * indent + '<DL><p>\n'
            if isinstance(value, dict):
                html += generate_html(value, indent + 1)
            else:
                for full_title, url in value:
                    html += '    ' * (indent + 1) + f'<DT><A HREF="{url}" ADD_DATE="0">{full_title}</A>\n'
            html += '    ' * indent + '</DL><p>\n'
        return html

    # HTML structure
    html_content = '''<!DOCTYPE NETSCAPE-Bookmark-file-1>
<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">
<TITLE>Bookmarks</TITLE>
<H1>Bookmarks</H1>
<DL><p>
'''
    # Add the main folder
    html_content += f'    <DT><H3>{folder_name}</H3>\n'
    html_content += '    <DL><p>\n'

    # Add bookmarks to HTML content
    html_content += generate_html(bookmarks)

    html_content += '    </DL><p>\n'
    html_content += '</DL><p>\n'

    # Write the HTML content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)

    # Print success message
    #print(f'Successfully created bookmarks in {output_file}')

# Example usage:
if __name__ == "__main__":
    wiki_adapted_md = '\n'.join(alternativeWikiIndexing())
    wiki_adapted_starred_only_md = '\n'.join(
        line for line in wiki_adapted_md.split('\n') if '⭐' in line or '🌟' in line
    )
    markdown_to_html_bookmarks(wiki_adapted_md, 'fmhy_in_bookmarks.html')
    markdown_to_html_bookmarks(
        wiki_adapted_starred_only_md,
        'fmhy_in_bookmarks_starred_only.html',
        starred_only=True,
    )
