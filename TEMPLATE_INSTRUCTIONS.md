# Website Template Instructions
## How to Add New Races and Race Albums

---

## Quick Start Checklist

When you want to add a new race event:
1. Add race card to `albums.html`
2. Create race years page (copy from `race-iceman.html`)
3. Generate race gallery for each year using the Python scripts
4. Upload everything to GitHub

---

## Part 1: Adding a New Race to the Albums Page

### Step 1: Open `albums.html`

Find the section with race cards (around line 180):

```html
<div class="races-grid">
    <!-- Iceman Cometh card is here -->
    
    <!-- ADD YOUR NEW RACE CARD HERE -->
    
</div>
```

### Step 2: Copy This Template

```html
<!-- [Race Name] -->
<div class="race-card" onclick="window.location.href='race-[shortname].html'">
    <div class="race-header">
        <div class="race-name">[Full Race Name]</div>
        <div class="race-location">[City, State]</div>
    </div>
    <div class="race-info">
        <div class="race-details">
            [Brief description of the race]
        </div>
        <a href="race-[shortname].html" class="view-button">View Years</a>
    </div>
</div>
```

### Step 3: Fill in the Details

**Example: Adding "Barry-Roubaix"**

```html
<!-- Barry-Roubaix -->
<div class="race-card" onclick="window.location.href='race-barryroubaix.html'">
    <div class="race-header">
        <div class="race-name">Barry-Roubaix</div>
        <div class="race-location">Hastings, MI</div>
    </div>
    <div class="race-info">
        <div class="race-details">
            Michigan's largest gravel grinder through scenic Barry County
        </div>
        <a href="race-barryroubaix.html" class="view-button">View Years</a>
    </div>
</div>
```

**Important:** 
- Replace `[shortname]` with a simple, lowercase, no-spaces version
- Example: "Barry-Roubaix" → `barryroubaix`
- Example: "Iceman Cometh" → `iceman`

---

## Part 2: Creating a Race Years Page

### Step 1: Copy the Template

1. Make a copy of `race-iceman.html`
2. Rename it to `race-[shortname].html`
   - Example: `race-barryroubaix.html`

### Step 2: Update the Page Title

Find this line (near the top):
```html
<title>Iceman Cometh | Adam Watson Photo</title>
```

Change to:
```html
<title>Barry-Roubaix | Adam Watson Photo</title>
```

### Step 3: Update the Breadcrumb

Find this section:
```html
<div class="breadcrumb">
    <a href="albums.html">Albums</a>
    <span>›</span>
    <span>Iceman Cometh</span>
</div>
```

Change to:
```html
<div class="breadcrumb">
    <a href="albums.html">Albums</a>
    <span>›</span>
    <span>Barry-Roubaix</span>
</div>
```

### Step 4: Update the Header

Find this section:
```html
<div class="years-header">
    <h1>Iceman Cometh</h1>
    <p>Select a year to view photos</p>
</div>
```

Change to:
```html
<div class="years-header">
    <h1>Barry-Roubaix</h1>
    <p>Select a year to view photos</p>
</div>
```

### Step 5: Add Year Cards

Find the years grid:
```html
<div class="years-grid">
    <!-- 2025 -->
    <div class="year-card" onclick="window.location.href='iceman-2025.html'">
        <div class="year-number">2025</div>
        <div class="year-info">Pro Category</div>
        <div class="year-stats">
            <div class="stat">500+ Photos</div>
            <div class="stat">200 Racers</div>
        </div>
    </div>
</div>
```

**Template for adding years:**
```html
<div class="year-card" onclick="window.location.href='[shortname]-[year].html'">
    <div class="year-number">[YEAR]</div>
    <div class="year-info">[Category/Description]</div>
    <div class="year-stats">
        <div class="stat">[XXX] Photos</div>
        <div class="stat">[XXX] Racers</div>
    </div>
</div>
```

**Example: Adding 2024 and 2025 for Barry-Roubaix**

```html
<div class="years-grid">
    <!-- 2025 -->
    <div class="year-card" onclick="window.location.href='barryroubaix-2025.html'">
        <div class="year-number">2025</div>
        <div class="year-info">All Categories</div>
        <div class="year-stats">
            <div class="stat">800+ Photos</div>
            <div class="stat">350 Racers</div>
        </div>
    </div>
    
    <!-- 2024 -->
    <div class="year-card" onclick="window.location.href='barryroubaix-2024.html'">
        <div class="year-number">2024</div>
        <div class="year-info">All Categories</div>
        <div class="year-stats">
            <div class="stat">600+ Photos</div>
            <div class="stat">300 Racers</div>
        </div>
    </div>
</div>
```

---

## Part 3: Creating Race Photo Galleries

### Overview

There are TWO types of race galleries depending on whether the race uses bib numbers:

**TYPE 1: Races WITH Race Numbers** (Iceman Pro, Barry-Roubaix, etc.)
- Uses: `race_photo_gallery.html` template
- Script: `flickr_api_gallery.py`
- Features: Search/filter by race number
- Workflow: Tag → Rename → Upload → Generate

**TYPE 2: Races WITHOUT Race Numbers** (Group rides, Gran Fondos, Social events)
- Uses: `race_photo_gallery_no_numbers.html` template
- Script: `flickr_api_no_numbers.py`
- Features: Just browse all photos
- Workflow: Upload → Generate (much simpler!)

---

### Workflow A: Races WITH Race Numbers

For each year of each race, you need to:
1. Tag photos with race numbers (CSV workflow)
2. Upload to Flickr
3. Generate the searchable gallery HTML

### Step 1: Tag Your Photos

**From your race photo folder:**

```cmd
cd D:\Pictures\RaceNumber
python create_csv.py "D:\Pictures\2025_BarryRoubaix\JPG"
```

This creates `race_numbers.csv` in your JPG folder.

**Fill in the CSV:**
1. Open `race_numbers.csv` in Excel
2. Open the JPG folder in Windows Explorer (side-by-side)
3. Type race numbers in Column B as you scroll through photos
4. Save the CSV

### Step 2: Rename Photos with Race Numbers

```cmd
python apply_race_numbers.py "D:\Pictures\2025_BarryRoubaix\JPG"
```

This creates a `Renamed` folder with files like: `IMG_1234_#4280.jpg`

### Step 3: Upload to Flickr

1. Go to Flickr.com
2. Upload all photos from the `Renamed` folder
3. Create a new album (e.g., "2025 Barry-Roubaix")
4. Make the album **Public**
5. Copy the album URL

### Step 4: Generate the Gallery (Once API Approved)

```cmd
python flickr_api_gallery.py "YOUR_API_KEY" "FLICKR_ALBUM_URL" "D:\Pictures\2025_BarryRoubaix\JPG\race_numbers.csv" barryroubaix-2025.html
```

**Before API approval**, use the manual method:
```cmd
python simple_flickr_gallery.py step1 "D:\Pictures\2025_BarryRoubaix\JPG\race_numbers.csv"
```
Then fill in Flickr URLs in Excel, then:
```cmd
python simple_flickr_gallery.py step2 flickr_urls.csv barryroubaix-2025.html
```

### Step 5: Customize the Gallery HTML

Open your generated `barryroubaix-2025.html` and update:

**Page title:**
```html
<title>2025 Barry-Roubaix Race Photos | Adam Watson Photo</title>
```

**Breadcrumb:**
```html
<div class="breadcrumb">
    <a href="albums.html">Albums</a>
    <span>›</span>
    <a href="race-barryroubaix.html">Barry-Roubaix</a>
    <span>›</span>
    <span>2025</span>
</div>
```

**Header:**
```html
<header>
    <h1>2025 Barry-Roubaix Race Photos</h1>
    <p class="subtitle">Find your photos by race number</p>
</header>
```

---

### Workflow B: Races WITHOUT Race Numbers

**Much simpler process - no tagging required!**

### Step 1: Upload Photos to Flickr

1. Go to Flickr.com
2. Upload ALL your race photos (no renaming needed!)
3. Create a new album (e.g., "2025 Grinduro")
4. Make the album **Public**
5. Copy the album URL

### Step 2: Generate the Gallery

```cmd
cd D:\Pictures\RaceNumber
python flickr_api_no_numbers.py "YOUR_API_KEY" "FLICKR_ALBUM_URL" "Grinduro" "2025"
```

**Or specify output filename:**
```cmd
python flickr_api_no_numbers.py "YOUR_API_KEY" "FLICKR_ALBUM_URL" "Grinduro" "2025" grinduro-2025.html
```

**That's it!** The script will:
- Fetch all photos from the Flickr album
- Generate `grinduro-2025.html` (or your specified filename)
- Include all thumbnails and links
- No race number search (just browse mode)

### Step 3: Done!

The gallery is ready to upload to GitHub. No customization needed - the script already updated:
- Page title
- Breadcrumb
- Header

**Perfect for:** Group rides, gran fondos, social events, any race without bib numbers

---

## Part 4: File Organization

### Recommended Folder Structure

```
D:\Documents\Adam_Watson_Photo\Website\Adam-Watson-Photo\
├── index.html
├── about.html
├── albums.html
│
├── race-iceman.html
├── iceman-2025.html              (with race numbers)
├── iceman-2024.html              (with race numbers)
│
├── race-barryroubaix.html
├── barryroubaix-2025.html        (with race numbers)
├── barryroubaix-2024.html        (with race numbers)
│
├── race-grinduro.html
├── grinduro-2025.html            (NO race numbers)
│
├── images/
│   ├── instagram-icon.png
│   └── adam-profile.jpg
│
└── portfolio/
    ├── image1.jpg
    ├── image2.jpg
    └── ...
```

### Naming Convention

**Always use this pattern:**
- Race years page: `race-[shortname].html`
- Individual year gallery: `[shortname]-[year].html`

**Examples:**
- Iceman: `race-iceman.html` → `iceman-2025.html`, `iceman-2024.html`
- Barry-Roubaix: `race-barryroubaix.html` → `barryroubaix-2025.html`
- Chequamegon: `race-cheq.html` → `cheq-2025.html`
- Grinduro (no numbers): `race-grinduro.html` → `grinduro-2025.html`

---

## Part 5: Template Files Reference

### Templates You Have:

| Template File | Used For | Generated By |
|--------------|----------|--------------|
| `race_photo_gallery.html` | Races WITH bib numbers | `flickr_api_gallery.py` |
| `race_photo_gallery_no_numbers.html` | Races WITHOUT bib numbers | `flickr_api_no_numbers.py` |

### Scripts You Have:

| Script | Input Required | Output |
|--------|----------------|--------|
| `create_csv.py` | Photo directory | CSV template for tagging |
| `apply_race_numbers.py` | CSV with race numbers | Renamed photos |
| `flickr_api_gallery.py` | API key, album URL, CSV | Gallery with search |
| `flickr_api_no_numbers.py` | API key, album URL, race name, year | Gallery without search |
| `simple_flickr_gallery.py` | Manual Flickr URLs | Gallery (before API approved) |

---

## Part 6: Uploading to GitHub

### First Time Setup

1. Go to your GitHub repository
2. Click "Add file" → "Upload files"
3. Upload ALL your HTML files
4. Upload the `images/` folder
5. Upload the `portfolio/` folder
6. Commit changes

### Adding New Races

When you add a new race:

1. Upload the new files:
   - `race-[shortname].html` (years page)
   - `[shortname]-[year].html` (photo gallery)
   - Update `albums.html` (with new race card)

2. Commit with a message like:
   ```
   Add Barry-Roubaix 2025 race photos
   ```

3. Changes go live automatically (GitHub Pages updates in 1-2 minutes)

---

## Quick Reference: Complete Workflow

### Adding a Race WITH Race Numbers (e.g., Barry-Roubaix 2025)

```
1. Add race card to albums.html
2. Copy race-iceman.html → race-barryroubaix.html
3. Update race-barryroubaix.html (title, breadcrumb, header)
4. Tag photos using create_csv.py + Excel
5. Rename photos using apply_race_numbers.py
6. Upload renamed photos to Flickr
7. Generate gallery using flickr_api_gallery.py
8. Customize barryroubaix-2025.html (if needed)
9. Upload to GitHub:
   - albums.html (updated)
   - race-barryroubaix.html (new)
   - barryroubaix-2025.html (new)
```

### Adding a Race WITHOUT Race Numbers (e.g., Grinduro 2025)

```
1. Add race card to albums.html
2. Copy race-iceman.html → race-grinduro.html
3. Update race-grinduro.html (title, breadcrumb, header)
4. Upload ALL photos to Flickr (no tagging/renaming!)
5. Generate gallery using flickr_api_no_numbers.py
6. Upload to GitHub:
   - albums.html (updated)
   - race-grinduro.html (new)
   - grinduro-2025.html (new)
```

**Much faster for non-numbered races!**

---

## Troubleshooting

### "My gallery shows no photos"
- Check that `photoData = [...]` has content in the HTML
- Make sure Flickr album is Public
- Verify photo data was generated correctly

### "Year card doesn't link to gallery"
- Check the onclick URL matches the actual filename
- Example: `onclick="window.location.href='iceman-2025.html'"`
- Make sure `iceman-2025.html` exists

### "Breadcrumb links are broken"
- Verify all referenced files exist
- Check spelling matches exactly (case-sensitive)

### "Photos not showing thumbnails"
- Without API: This is normal, shows race number cards
- With API: Check that thumbnailUrl was included in photo data

---

## Tips for Efficiency

**Process Multiple Years at Once:**
1. Tag all years' photos → separate CSVs
2. Upload all to Flickr → separate albums
3. Generate all galleries at once
4. Upload everything to GitHub together

**Reuse Template Files:**
- Keep a `_TEMPLATE_race.html` file
- Copy and find/replace race names
- Faster than editing from scratch

**Batch Rename for Speed:**
- Use Excel formulas to generate year cards
- Copy-paste into HTML
- Much faster for races with 5+ years

---

## Need Help?

If something isn't working:
1. Check file names match exactly (case-sensitive!)
2. Verify all links use the correct filename
3. Make sure files are in the root directory (not in subfolders)
4. Test locally by opening HTML files in your browser before uploading

---

**You're all set!** This template system makes it easy to add dozens of races over time. Just follow the pattern and everything will be consistent and professional. 📸
