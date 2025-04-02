# LogoSimilarity
## Context
The goal of this project is to develop an algorithm that analyzes thousands of websites and groups them based on the visual similarity of their logos, without relying on machine learning models. The focus is on implementing a custom, interpretable solution that works at scale.

## Algorithm Steps
### 1. Converting domains into valid URLs
We transform simple domain names into valid web URLs, e.g., **domain.com** → **https://domain.com/**.
### 2. Reading domains from input files
The input domains are extracted from a **Parquet** file. We ensure uniqueness by removing duplicate entries.
### 3. Extracting the logo URL
In this step, we use Selenium for automated browser interaction to extract the logo image from each webpage. Many modern websites load their content asynchronously using JavaScript, which makes traditional HTML parsers like **requests + BeautifulSoup** insufficient. By using Selenium, we emulate a real browser session that fully renders JavaScript content, ensuring access to dynamically loaded logos, such as inline SVGs or lazy-loaded **<img>** elements.
Once the page is rendered, we programmatically inspect the DOM for common logo patterns. These include:
- **<img>** tags that contain the word **logo** in their **alt, class, or src** attributes   
- **<meta property='og:image'>** tags which often point to branding assets  
- **<link rel='icon'>** or similar **favicon** references   
### 4. Downloading and saving the logo image
Once the logo URL is extracted, we download and save it locally as a **.png** file in the **logos/** directory.
### 5. Generating visual hashes for logos
We convert each image into a perceptual**hash** (phash), which captures the visual structure of the image in a numeric form. This allows us to compute the **Hamming distance** between two logos and determine how visually similar they are.
### 6. Building the similarity graph and grouping websites
We create a graph where each node is a website and edges connect logos that are visually similar (based on hash distance). The connected components in this graph form clusters of sites with similar branding.

## Technologies and libraries
- **Python 3**  
- **Selenium (scraping )**  
- **BeautifulSoup (parsing HTML)**  
- **Requests (download images)**  
- **Pillow + ImageHash (generate hash)**  
- **NetworkX (graph)**  
- **Parquet + pandas (Data processing)**  
