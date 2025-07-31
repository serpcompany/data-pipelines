#!/usr/bin/env tsx

import * as cheerio from 'cheerio';
import * as fs from 'fs/promises';
import * as path from 'path';

interface BoxerData {
  // IDs and URLs
  boxrecId: string;
  boxrecUrl: string;
  
  // Basic Info
  fullName: string;
  birthName?: string;
  nickname?: string;
  gender?: string;
  
  // Physical
  height?: string;
  reach?: string;
  stance?: string;
  
  // Birth/Location
  dateOfBirth?: string;
  age?: string;
  birthPlace?: string;
  residence?: string;
  nationality?: string;
  
  // Career
  division?: string;
  status?: string;
  debut?: string;
  bouts?: number;
  rounds?: number;
  KOs?: string;
  career?: string;
  
  // Professional Record
  proWins?: number;
  proWinsKO?: number;
  proLosses?: number;
  proLossesKO?: number;
  proDraws?: number;
  proNoContests?: number;
  
  // Team
  promoter?: string;
  manager?: string;
  trainer?: string;
  
  // Media
  avatarImage?: string;
  bio?: string;
  
  // Titles
  titles?: string[];
  
  // Raw data for debugging
  rawLabels?: Record<string, string>;
}

class BoxRecCompleteParser {
  private $: cheerio.CheerioAPI;

  constructor(html: string) {
    this.$ = cheerio.load(html);
  }

  parse(boxrecId: string): BoxerData {
    const $ = this.$;
    const data: BoxerData = {
      boxrecId,
      boxrecUrl: `https://boxrec.com/en/box-pro/${boxrecId}`,
      fullName: this.extractName(),
      rawLabels: {}
    };

    // Extract all data
    this.extractMetaData(data);
    this.extractProfileTableData(data);
    this.extractRecord(data);
    this.extractBio(data);
    this.extractTitles(data);
    
    return data;
  }

  private extractName(): string {
    const $ = this.$;
    
    // Try title first
    const titleText = $('title').text().trim();
    let name = titleText.replace('BoxRec:', '').replace('- BoxRec', '').trim();
    
    // Try h1 as fallback
    if (!name || name === 'Unknown') {
      name = $('h1').first().text().trim() || 'Unknown';
    }
    
    return name;
  }

  private extractMetaData(data: BoxerData) {
    const $ = this.$;
    
    // Extract from meta tags
    $('meta').each((_, elem) => {
      const $meta = $(elem);
      const property = $meta.attr('property');
      const content = $meta.attr('content');
      
      if (property === 'og:image' && content) {
        data.avatarImage = content;
      }
    });
    
    // Extract image from profile photo
    const profileImg = $('.profileTablePhoto img, .photoBorder').first().attr('src');
    if (profileImg && !data.avatarImage) {
      data.avatarImage = profileImg;
    }
  }

  private extractProfileTableData(data: BoxerData) {
    const $ = this.$;
    
    // Extract from rowLabel/value pairs
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      let labelText = $label.find('b').text().trim() || $label.text().trim();
      labelText = labelText.replace(':', '').toLowerCase();
      
      const $valueTd = $label.next('td');
      let value = $valueTd.text().trim();
      
      // Clean up value
      value = value.replace(/\s+/g, ' ').trim();
      
      if (labelText && value) {
        data.rawLabels![labelText] = value;
        
        // Map to fields
        switch(labelText) {
          case 'division':
            data.division = value;
            break;
          case 'status':
            data.status = value.toLowerCase();
            break;
          case 'bouts':
            data.bouts = parseInt(value) || 0;
            break;
          case 'rounds':
            data.rounds = parseInt(value) || 0;
            break;
          case 'kos':
            data.KOs = value;
            break;
          case 'career':
            data.career = value;
            break;
          case 'debut':
            data.debut = value;
            break;
          case 'born':
          case 'date of birth':
            data.dateOfBirth = value;
            break;
          case 'birth name':
          case 'real name':
            data.birthName = value;
            break;
          case 'nickname':
          case 'alias':
            data.nickname = value;
            break;
          case 'birth place':
          case 'birthplace':
            data.birthPlace = value;
            break;
          case 'residence':
            data.residence = value;
            break;
          case 'nationality':
            data.nationality = value;
            break;
          case 'height':
            data.height = value;
            break;
          case 'reach':
            data.reach = value;
            break;
          case 'stance':
            data.stance = value.toLowerCase();
            break;
          case 'sex':
          case 'gender':
            data.gender = value.toLowerCase();
            break;
          case 'age':
            data.age = value;
            break;
          case 'promoter':
            data.promoter = value;
            break;
          case 'manager':
            data.manager = value;
            break;
          case 'trainer':
            data.trainer = value;
            break;
        }
      }
    });
    
    // Handle special case where stance is its own cell
    $('td:contains("orthodox"), td:contains("southpaw")').each((_, elem) => {
      const text = $(elem).text().trim().toLowerCase();
      if (text === 'orthodox' || text === 'southpaw') {
        data.stance = text;
      }
    });
  }

  private extractRecord(data: BoxerData) {
    const $ = this.$;
    
    // Extract from WLD table
    const $wldTable = $('.profileWLD');
    if ($wldTable.length) {
      // Find the row with W-L-D data
      const $row = $wldTable.find('tr').first();
      const cells = $row.find('td');
      
      // First cell: Wins
      const $winsCell = cells.eq(0);
      if ($winsCell.length) {
        const winsText = $winsCell.text().trim();
        const winsMatch = winsText.match(/(\d+)/);
        if (winsMatch) data.proWins = parseInt(winsMatch[1]);
      }
      
      // Second cell: Losses
      const $lossesCell = cells.eq(1);
      if ($lossesCell.length) {
        const lossesText = $lossesCell.text().trim();
        const lossesMatch = lossesText.match(/(\d+)/);
        if (lossesMatch) data.proLosses = parseInt(lossesMatch[1]);
      }
      
      // Third cell: Draws
      const $drawsCell = cells.eq(2);
      if ($drawsCell.length) {
        const drawsText = $drawsCell.text().trim();
        const drawsMatch = drawsText.match(/(\d+)/);
        if (drawsMatch) data.proDraws = parseInt(drawsMatch[1]);
      }
      
      // Look for KO information in the second row
      const $koRow = $wldTable.find('tr').eq(1);
      if ($koRow.length) {
        const koText = $koRow.text();
        
        // Extract KO wins (usually first number followed by KO)
        const winsKOMatch = koText.match(/(\d+)\s*KOs?/);
        if (winsKOMatch) data.proWinsKO = parseInt(winsKOMatch[1]);
        
        // Extract KO losses (usually second number followed by KO)
        const allKOs = koText.match(/(\d+)\s*KOs?/g);
        if (allKOs && allKOs.length > 1) {
          const lossesKOMatch = allKOs[1].match(/(\d+)/);
          if (lossesKOMatch) data.proLossesKO = parseInt(lossesKOMatch[1]);
        }
      }
    }
    
    // Another approach: look for the specific KO counts in tables
    $('table').each((_, table) => {
      const $table = $(table);
      const text = $table.text();
      
      // Look for patterns like "70 KOs" near wins section
      if (text.includes('KOs') && !data.proWinsKO) {
        const koMatches = text.match(/(\d+)\s*KOs/g);
        if (koMatches && koMatches.length > 0) {
          // First KO number is usually wins by KO
          const firstKO = koMatches[0].match(/(\d+)/);
          if (firstKO) data.proWinsKO = parseInt(firstKO[1]);
          
          // Second KO number is usually losses by KO
          if (koMatches.length > 1) {
            const secondKO = koMatches[1].match(/(\d+)/);
            if (secondKO) data.proLossesKO = parseInt(secondKO[1]);
          }
        }
      }
    });
  }

  private extractBio(data: BoxerData) {
    const $ = this.$;
    
    const bio = $('.profileBio, .bio, [class*="bio"]').text().trim();
    if (bio && bio.length > 10) {
      data.bio = bio.substring(0, 1000); // Limit bio length for display
    }
  }

  private extractTitles(data: BoxerData) {
    const $ = this.$;
    const titles: string[] = [];
    
    // Look for title icons or championship text
    $('.titleIcon, .title, [class*="champion"], [class*="title"]').each((_, elem) => {
      const title = $(elem).text().trim();
      if (title && title.length > 3 && !title.includes('click here')) {
        titles.push(title);
      }
    });
    
    // Look in tables for title information
    $('td:contains("title"), td:contains("champion")').each((_, elem) => {
      const text = $(elem).text().trim();
      if (text.length > 5 && text.length < 200) {
        titles.push(text);
      }
    });
    
    if (titles.length > 0) {
      data.titles = [...new Set(titles)].slice(0, 5); // Remove duplicates and limit
    }
  }
}

async function extract100Boxers() {
  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  const outputFile = 'extracted_100_boxers.json';
  
  try {
    console.log('🥊 Extracting data from 100 boxer HTML files...\n');
    
    const files = await fs.readdir(htmlDir);
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f.startsWith('en_box-pro'))
      .slice(0, 100); // Get first 100 files
    
    console.log(`📊 Processing ${htmlFiles.length} HTML files...\n`);
    
    const extractedBoxers: BoxerData[] = [];
    let successCount = 0;
    let errorCount = 0;
    let loginPageCount = 0;
    
    for (let i = 0; i < htmlFiles.length; i++) {
      const filename = htmlFiles[i];
      
      try {
        const match = filename.match(/box-pro_(\d+)\.html$/);
        if (!match) {
          console.log(`⚠️  Skipping ${filename} - invalid format`);
          errorCount++;
          continue;
        }
        
        const boxrecId = match[1];
        const htmlPath = path.join(htmlDir, filename);
        const html = await fs.readFile(htmlPath, 'utf-8');
        
        // Check if it's a login page
        if (html.includes('Please login to continue') || html.includes('Login to BoxRec')) {
          loginPageCount++;
          continue;
        }
        
        const parser = new BoxRecCompleteParser(html);
        const data = parser.parse(boxrecId);
        
        // Skip if name indicates login page
        if (data.fullName.toLowerCase().includes('login') || 
            data.fullName.toLowerCase().includes('please')) {
          loginPageCount++;
          continue;
        }
        
        extractedBoxers.push(data);
        successCount++;
        
        // Show progress every 10 boxers
        if (successCount % 10 === 0) {
          console.log(`✅ Processed ${successCount} boxers...`);
        }
        
      } catch (error) {
        console.error(`❌ Error processing ${filename}:`, error);
        errorCount++;
      }
    }
    
    console.log('\n📈 Extraction Summary:');
    console.log(`✅ Successfully extracted: ${successCount} boxers`);
    console.log(`🔒 Login pages skipped: ${loginPageCount}`);
    console.log(`❌ Errors: ${errorCount}`);
    
    // Save to JSON file
    await fs.writeFile(
      outputFile, 
      JSON.stringify(extractedBoxers, null, 2),
      'utf-8'
    );
    
    console.log(`\n💾 Data saved to: ${outputFile}`);
    
    // Display sample of extracted data
    console.log('\n📋 Sample of extracted boxers:\n');
    
    extractedBoxers.slice(0, 5).forEach(boxer => {
      console.log(`${'-'.repeat(60)}`);
      console.log(`🥊 ${boxer.fullName}`);
      console.log(`   ID: ${boxer.boxrecId}`);
      console.log(`   Record: ${boxer.proWins || 0}-${boxer.proLosses || 0}-${boxer.proDraws || 0} (${boxer.proWinsKO || 0} KOs)`);
      if (boxer.nationality) console.log(`   Nationality: ${boxer.nationality}`);
      if (boxer.division) console.log(`   Division: ${boxer.division}`);
      if (boxer.stance) console.log(`   Stance: ${boxer.stance}`);
      if (boxer.height) console.log(`   Height: ${boxer.height}`);
      if (boxer.titles && boxer.titles.length > 0) {
        console.log(`   Titles: ${boxer.titles.length} championship(s)`);
      }
    });
    
    // Show statistics
    console.log(`\n📊 Data Quality Statistics:`);
    
    const hasRecord = extractedBoxers.filter(b => b.proWins !== undefined).length;
    const hasNationality = extractedBoxers.filter(b => b.nationality).length;
    const hasDivision = extractedBoxers.filter(b => b.division).length;
    const hasStance = extractedBoxers.filter(b => b.stance).length;
    const hasHeight = extractedBoxers.filter(b => b.height).length;
    const hasBirthPlace = extractedBoxers.filter(b => b.birthPlace).length;
    const hasTitles = extractedBoxers.filter(b => b.titles && b.titles.length > 0).length;
    const hasAvatar = extractedBoxers.filter(b => b.avatarImage).length;
    
    console.log(`   Has record: ${hasRecord}/${successCount} (${(hasRecord/successCount*100).toFixed(1)}%)`);
    console.log(`   Has nationality: ${hasNationality}/${successCount} (${(hasNationality/successCount*100).toFixed(1)}%)`);
    console.log(`   Has division: ${hasDivision}/${successCount} (${(hasDivision/successCount*100).toFixed(1)}%)`);
    console.log(`   Has stance: ${hasStance}/${successCount} (${(hasStance/successCount*100).toFixed(1)}%)`);
    console.log(`   Has height: ${hasHeight}/${successCount} (${(hasHeight/successCount*100).toFixed(1)}%)`);
    console.log(`   Has birth place: ${hasBirthPlace}/${successCount} (${(hasBirthPlace/successCount*100).toFixed(1)}%)`);
    console.log(`   Has titles: ${hasTitles}/${successCount} (${(hasTitles/successCount*100).toFixed(1)}%)`);
    console.log(`   Has avatar: ${hasAvatar}/${successCount} (${(hasAvatar/successCount*100).toFixed(1)}%)`);
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

// Run the extraction
extract100Boxers().catch(console.error);