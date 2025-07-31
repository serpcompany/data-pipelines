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
  
  // Bouts List
  boutsList?: Array<{
    date?: string;
    opponent?: string;
    result?: string;
    method?: string;
    rounds?: string;
    venue?: string;
  }>;
  
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
    this.extractBoutsList(data);
    
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
    
    // Extract image from profile photo first (prioritize actual profile photo)
    const profileImg = $('.profileTablePhoto img.photoBorder, img.photoBorder').first().attr('src');
    if (profileImg) {
      // Convert relative URLs to absolute URLs
      if (profileImg.startsWith('/')) {
        data.avatarImage = `https://boxrec.com${profileImg}`;
      } else {
        data.avatarImage = profileImg;
      }
    }
    
    // Fallback to OpenGraph image if no profile photo found
    if (!data.avatarImage) {
      $('meta').each((_, elem) => {
        const $meta = $(elem);
        const property = $meta.attr('property');
        const content = $meta.attr('content');
        
        if (property === 'og:image' && content) {
          data.avatarImage = content;
        }
      });
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
    
    // Alternative: Extract KOs from the raw labels (more reliable)
    if (data.rawLabels && data.rawLabels['kos']) {
      // The KOs field contains percentage, we need to calculate actual numbers
      const totalBouts = data.bouts || 0;
      const koPercentage = parseFloat(data.rawLabels['kos']) / 100;
      const totalKOs = Math.round(totalBouts * koPercentage);
      
      // If we have wins but no KO count, estimate it
      if (data.proWins && !data.proWinsKO && totalKOs > 0) {
        // Assume most KOs are wins (rough estimate)
        data.proWinsKO = totalKOs;
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
      data.bio = bio.substring(0, 5000); // Limit bio length
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
      data.titles = [...new Set(titles)]; // Remove duplicates
    }
  }

  private extractBoutsList(data: BoxerData) {
    const $ = this.$;
    const bouts: typeof data.boutsList = [];
    
    // Find the bouts table (usually has class dataTable)
    $('.dataTable tr, #dataTable tr').each((i, row) => {
      if (i === 0) return; // Skip header
      
      const $row = $(row);
      const cells = $row.find('td').map((_, td) => $(td).text().trim()).get();
      
      if (cells.length >= 6) {
        bouts.push({
          date: cells[0],
          opponent: cells[2] || cells[3], // Sometimes in different columns
          result: cells[6] || cells[5],
          method: cells[7],
          rounds: cells[8],
          venue: cells[9] || cells[10]
        });
      }
    });
    
    // Only store if we found bouts
    if (bouts.length > 0) {
      data.boutsList = bouts.slice(0, 10); // Store first 10 bouts for now
    }
  }
}

async function testParser() {
  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  
  try {
    const files = await fs.readdir(htmlDir);
    const testFiles = files
      .filter(f => f.endsWith('.html') && f.startsWith('en_box-pro'))
      .slice(0, 3); // Test with 3 files
    
    console.log(`\n🧪 Testing complete parser on ${testFiles.length} files...\n`);

    for (const filename of testFiles) {
      const match = filename.match(/box-pro_(\d+)\.html$/);
      if (!match) continue;
      
      const boxrecId = match[1];
      const htmlPath = path.join(htmlDir, filename);
      const html = await fs.readFile(htmlPath, 'utf-8');
      
      console.log(`\n${'='.repeat(80)}`);
      console.log(`📄 Parsing: ${filename}`);
      console.log(`${'='.repeat(80)}\n`);
      
      const parser = new BoxRecCompleteParser(html);
      const data = parser.parse(boxrecId);
      
      // Display parsed data
      console.log(`🥊 Boxer: ${data.fullName}`);
      console.log(`📌 BoxRec ID: ${data.boxrecId}`);
      console.log(`🔗 URL: ${data.boxrecUrl}`);
      
      if (data.birthName) console.log(`📝 Birth Name: ${data.birthName}`);
      if (data.nickname) console.log(`💬 Nickname: ${data.nickname}`);
      if (data.gender) console.log(`⚧️  Gender: ${data.gender}`);
      
      console.log(`\n📊 Professional Record:`);
      console.log(`   Wins: ${data.proWins || 0} (${data.proWinsKO || 0} KOs)`);
      console.log(`   Losses: ${data.proLosses || 0} (${data.proLossesKO || 0} KOs)`);
      console.log(`   Draws: ${data.proDraws || 0}`);
      
      if (data.division) console.log(`\n🏆 Division: ${data.division}`);
      if (data.status) console.log(`📈 Status: ${data.status}`);
      if (data.debut) console.log(`📅 Debut: ${data.debut}`);
      if (data.bouts) console.log(`🥊 Total Bouts: ${data.bouts}`);
      if (data.rounds) console.log(`⏱️  Total Rounds: ${data.rounds}`);
      
      console.log(`\n👤 Personal Info:`);
      if (data.dateOfBirth) console.log(`   Born: ${data.dateOfBirth}`);
      if (data.age) console.log(`   Age: ${data.age}`);
      if (data.birthPlace) console.log(`   Birth Place: ${data.birthPlace}`);
      if (data.nationality) console.log(`   Nationality: ${data.nationality}`);
      if (data.residence) console.log(`   Residence: ${data.residence}`);
      
      console.log(`\n📏 Physical:`);
      if (data.height) console.log(`   Height: ${data.height}`);
      if (data.reach) console.log(`   Reach: ${data.reach}`);
      if (data.stance) console.log(`   Stance: ${data.stance}`);
      
      if (data.promoter || data.manager || data.trainer) {
        console.log(`\n👥 Team:`);
        if (data.promoter) console.log(`   Promoter: ${data.promoter}`);
        if (data.manager) console.log(`   Manager: ${data.manager}`);
        if (data.trainer) console.log(`   Trainer: ${data.trainer}`);
      }
      
      if (data.titles && data.titles.length > 0) {
        console.log(`\n🏅 Titles:`);
        data.titles.forEach(title => console.log(`   - ${title}`));
      }
      
      if (data.boutsList && data.boutsList.length > 0) {
        console.log(`\n📋 Recent Bouts (showing first 3):`);
        data.boutsList.slice(0, 3).forEach(bout => {
          console.log(`   ${bout.date} vs ${bout.opponent} - ${bout.result}`);
        });
      }
      
      if (data.avatarImage) {
        console.log(`\n🖼️  Avatar: ${data.avatarImage}`);
      }
      
      if (data.bio) {
        console.log(`\n📝 Bio: ${data.bio.substring(0, 200)}...`);
      }
      
      console.log(`\n🏷️  All Raw Labels Found:`);
      Object.entries(data.rawLabels || {}).forEach(([label, value]) => {
        console.log(`   ${label}: ${value.substring(0, 50)}${value.length > 50 ? '...' : ''}`);
      });
    }

  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Run the test
testParser().catch(console.error);