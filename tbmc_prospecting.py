import requests
from bs4 import BeautifulSoup
import csv
import datetime
import re
import os

def read_competition_csv(file_path):
    """Read the CSV file containing competition URLs"""
    competitions = []
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            competitions.append(row)
    return competitions

def check_competition_website(url):
    """Check a competition website for winner announcements"""
    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            return response.text
        else:
            print(f"Failed to access {url}, status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error accessing {url}: {e}")
        return None

def extract_basic_info(html_content, competition_name):
    """
    Extract only basic information about potential TBMC applicants:
    - Student/Team Name
    - School/University
    - Year (if available)
    - Major (if available)
    """
    if not html_content:
        return []
    
    soup = BeautifulSoup(html_content, 'html.parser')
    prospects = []
    
    # This is a simplified extraction that will need customization for each competition website
    # Look for common patterns in winner announcements
    winner_sections = soup.find_all(['div', 'section', 'article'], class_=re.compile(r'winner|award|prize', re.I))
    
    if not winner_sections:
        # Try looking for headings that might indicate winners
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4'], string=re.compile(r'winner|award|prize', re.I))
        for heading in headings:
            section = heading.find_parent(['div', 'section', 'article'])
            if section:
                winner_sections.append(section)
    
    for section in winner_sections:
        # Look for names, which are often in headings or strong/bold text
        names = section.find_all(['h3', 'h4', 'strong', 'b'], limit=5)
        
        for name_elem in names:
            name = name_elem.get_text().strip()
            
            # Skip if it's not likely a name
            if len(name) < 3 or re.search(r'winner|award|prize|about', name, re.I):
                continue
                
            # Look for school information near the name
            school = ""
            year = ""
            major = ""
            
            # Check siblings and parent elements for school info
            for elem in name_elem.next_siblings:
                text = elem.get_text().strip() if hasattr(elem, 'get_text') else str(elem).strip()
                
                # Look for university/college mentions
                if re.search(r'university|college|school', text, re.I) and not school:
                    school = text
                
                # Look for year information
                year_match = re.search(r'(freshman|sophomore|junior|senior|\b\d{4}\b)', text, re.I)
                if year_match and not year:
                    year = year_match.group(0)
                
                # Look for major information
                major_match = re.search(r'major(ing)? in (\w+)|(\w+) major', text, re.I)
                if major_match and not major:
                    major = major_match.group(2) if major_match.group(2) else major_match.group(3)
            
            # Add to prospects if we have at least a name
            if name:
                prospects.append({
                    'Student/Team Name': name,
                    'School': school,
                    'Year': year,
                    'Major': major,
                    'Competition': competition_name,
                    'Venture Name': '',  # To be filled manually
                    'Email': ''  # To be filled manually
                })
    
    return prospects

def save_prospects_to_csv(prospects, output_file='tbmc_prospects.csv'):
    """Save the extracted prospect information to a CSV file"""
    if not prospects:
        print("No prospects found to save.")
        return
    
    file_exists = os.path.isfile(output_file)
    
    with open(output_file, 'a', newline='', encoding='utf-8') as file:
        fieldnames = ['Student/Team Name', 'School', 'Year', 'Major', 'Competition', 'Venture Name', 'Email']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        
        if not file_exists:
            writer.writeheader()
        
        for prospect in prospects:
            writer.writerow(prospect)
    
    print(f"Saved {len(prospects)} prospects to {output_file}")

def main():
    """Main function to process all competitions"""
    # Create competitions.csv if it doesn't exist
    if not os.path.isfile('competitions.csv'):
        with open('competitions.csv', 'w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(['competition_name', 'url', 'last_checked'])
            # Add some example competitions
            writer.writerow(['Rice Business Plan Competition', 'https://rbpc.rice.edu/winners', ''])
            writer.writerow(['MIT $100K', 'https://www.mit100k.org/winners', ''])
        print("Created competitions.csv with example competitions")
    
    competitions = read_competition_csv('competitions.csv')
    
    for competition in competitions:
        print(f"Checking {competition['competition_name']}...")
        html_content = check_competition_website(competition['url'])
        
        if html_content:
            prospects = extract_basic_info(html_content, competition['competition_name'])
            if prospects:
                save_prospects_to_csv(prospects)
                print(f"Found {len(prospects)} potential prospects from {competition['competition_name']}")
            else:
                print(f"No prospects found from {competition['competition_name']}")
            
            # Update last checked date
            competition['last_checked'] = datetime.datetime.now().strftime('%Y-%m-%d')
    
    # Update the competitions.csv with new last_checked dates
    with open('competitions.csv', 'w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=['competition_name', 'url', 'last_checked'])
        writer.writeheader()
        writer.writerows(competitions)

if __name__ == "__main__":
    main()
