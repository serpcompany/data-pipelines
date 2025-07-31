#!/usr/bin/env tsx

import * as cheerio from 'cheerio';
import * as fs from 'fs/promises';
import * as path from 'path';

interface ExtractedData {
  // Basic info
  fullName?: string;
  birthName?: string;
  nickname?: string;
  boxrecId?: string;
  
  // Physical attributes
  gender?: string;
  height?: string;
  reach?: string;
  stance?: string;
  
  // Birth/Location info
  dateOfBirth?: string;
  birthPlace?: string;
  residence?: string;
  nationality?: string;
  
  // Career info
  proStatus?: string;
  proDebutDate?: string;
  division?: string;
  
  // Record
  proWins?: number;
  proWinsKO?: number;
  proLosses?: number;
  proLossesKO?: number;
  proDraws?: number;
  proNoContests?: number;
  totalRounds?: number;
  
  // Team
  promoter?: string;
  manager?: string;
  trainer?: string;
  gym?: string;
  
  // Media
  avatarImage?: string;
  bio?: string;
  
  // Amateur record
  amateurWins?: number;
  amateurLosses?: number;
  amateurDraws?: number;
  
  // Titles
  titles?: string[];
  
  // Bouts
  boutsCount?: number;
  lastBoutDate?: string;
  
  // Additional
  rating?: number;
  ranking?: number;
  
  // Debug - what sections we found
  foundSections?: string[];
}

class ComprehensiveBoxRecParser {
  private $: cheerio.CheerioAPI;
  private debug: boolean;

  constructor(html: string, debug = false) {
    this.$ = cheerio.load(html);
    this.debug = debug;
  }

  extractAll(): ExtractedData {
    const $ = this.$;
    const data: ExtractedData = {};
    const foundSections: string[] = [];

    // Extract name from title
    const titleText = $('title').text().trim();
    data.fullName = titleText.replace('BoxRec:', '').replace('- BoxRec', '').trim();
    if (data.fullName) foundSections.push('title');

    // Extract from meta tags
    $('meta').each((_, elem) => {
      const $meta = $(elem);
      const property = $meta.attr('property');
      const content = $meta.attr('content');
      
      if (property === 'og:image' && content) {
        data.avatarImage = content;
        foundSections.push('meta:image');
      }
    });

    // Extract from profileTable sections
    $('.profileTable').each((_, table) => {
      const $table = $(table);
      foundSections.push('profileTable');
      
      // Look for row labels and values
      $table.find('tr').each((_, row) => {
        const $row = $(row);
        const labelCell = $row.find('td.rowLabel, td:contains(":")').first();
        const valueCell = labelCell.next('td');
        
        if (labelCell.length && valueCell.length) {
          const label = labelCell.text().replace(':', '').trim().toLowerCase();
          const value = valueCell.text().trim();
          
          if (this.debug) console.log(`Found: ${label} = ${value}`);
          
          this.mapLabelToField(label, value, data);
        }
      });
    });

    // Extract record from WLD table
    const $wldTable = $('.profileWLD, .profileTableWLD');
    if ($wldTable.length) {
      foundSections.push('WLD table');
      
      // Extract wins
      const wins = $wldTable.find('.bgW, td:contains("W")').first().text().match(/\d+/);
      if (wins) data.proWins = parseInt(wins[0]);
      
      // Extract losses  
      const losses = $wldTable.find('.bgL, td:contains("L")').first().text().match(/\d+/);
      if (losses) data.proLosses = parseInt(losses[0]);
      
      // Extract draws
      const draws = $wldTable.find('.bgD, td:contains("D")').first().text().match(/\d+/);
      if (draws) data.proDraws = parseInt(draws[0]);
      
      // Extract KOs
      const koText = $wldTable.text();
      const winsKO = koText.match(/(\d+)\s*KOs?\s*(?:wins|W)/i);
      if (winsKO) data.proWinsKO = parseInt(winsKO[1]);
      
      const lossesKO = koText.match(/(\d+)\s*KOs?\s*(?:losses|L)/i);
      if (lossesKO) data.proLossesKO = parseInt(lossesKO[1]);
    }

    // Extract from info sections
    $('.info, .profileInfo').each((_, elem) => {
      const $info = $(elem);
      const text = $info.text();
      foundSections.push('info section');
      
      // Extract various patterns
      const height = text.match(/(\d+)\s*(?:cm|′|ft)/i);
      if (height) data.height = height[0];
      
      const reach = text.match(/reach[:\s]+(\d+\s*(?:cm|″|in))/i);
      if (reach) data.reach = reach[1];
    });

    // Extract bio
    const bio = $('.profileBio, .bio, div[id*="bio"]').text().trim();
    if (bio && bio.length > 10) {
      data.bio = bio;
      foundSections.push('bio');
    }

    // Extract from tables with specific headers
    $('table').each((_, table) => {
      const $table = $(table);
      const headers = $table.find('th').map((_, th) => $(th).text().trim()).get();
      
      if (headers.length) {
        foundSections.push(`table with headers: ${headers.slice(0, 3).join(', ')}`);
      }
    });

    // Extract titles
    const titles: string[] = [];
    $('.titleIcon, .title, [class*="champion"]').each((_, elem) => {
      const title = $(elem).text().trim();
      if (title && title.length > 3) {
        titles.push(title);
      }
    });
    if (titles.length) {
      data.titles = titles;
      foundSections.push('titles');
    }

    // Look for amateur record
    $('td:contains("amateur"), div:contains("amateur")').each((_, elem) => {
      const text = $(elem).parent().text();
      const amateur = text.match(/(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?/);
      if (amateur) {
        data.amateurWins = parseInt(amateur[1]);
        data.amateurLosses = parseInt(amateur[2]);
        if (amateur[3]) data.amateurDraws = parseInt(amateur[3]);
        foundSections.push('amateur record');
      }
    });

    // Extract from any data attributes
    $('*').each((_, elem) => {
      const $elem = $(elem);
      const attrs = elem.attribs;
      if (attrs) {
        Object.keys(attrs).forEach(key => {
          if (key.startsWith('data-') && attrs[key]) {
            foundSections.push(`data attribute: ${key}`);
          }
        });
      }
    });

    data.foundSections = [...new Set(foundSections)];
    return data;
  }

  private mapLabelToField(label: string, value: string, data: ExtractedData) {
    // Map common labels to fields
    const mappings: Record<string, keyof ExtractedData> = {
      'born': 'dateOfBirth',
      'birth date': 'dateOfBirth',
      'date of birth': 'dateOfBirth',
      'birth name': 'birthName',
      'real name': 'birthName',
      'nickname': 'nickname',
      'alias': 'nickname',
      'birth place': 'birthPlace',
      'birthplace': 'birthPlace',
      'residence': 'residence',
      'nationality': 'nationality',
      'height': 'height',
      'reach': 'reach',
      'stance': 'stance',
      'orthodox': 'stance',
      'southpaw': 'stance',
      'division': 'division',
      'weight': 'division',
      'status': 'proStatus',
      'debut': 'proDebutDate',
      'pro debut': 'proDebutDate',
      'promoter': 'promoter',
      'manager': 'manager',
      'trainer': 'trainer',
      'gym': 'gym',
      'sex': 'gender',
      'gender': 'gender',
      'rating': 'rating',
      'ranking': 'ranking',
    };

    const field = mappings[label];
    if (field && value) {
      // Special handling for stance
      if (field === 'stance' && !value.toLowerCase().includes('orthodox') && !value.toLowerCase().includes('southpaw')) {
        // If the label is stance but value is not a stance, skip
        return;
      }
      
      (data as any)[field] = value;
    }
    
    // Handle standalone stance values
    if ((label === 'orthodox' || label === 'southpaw') && value) {
      data.stance = label;
    }
  }
}

async function analyzeHtmlFiles() {
  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  
  try {
    const files = await fs.readdir(htmlDir);
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f.startsWith('en_box-pro'))
      .slice(0, 5); // Analyze first 5 files
    
    console.log(`\n📊 Analyzing ${htmlFiles.length} HTML files for available fields...\n`);

    for (const filename of htmlFiles) {
      console.log(`\n${'='.repeat(60)}`);
      console.log(`📄 File: ${filename}`);
      console.log(`${'='.repeat(60)}\n`);
      
      const htmlPath = path.join(htmlDir, filename);
      const html = await fs.readFile(htmlPath, 'utf-8');
      
      const parser = new ComprehensiveBoxRecParser(html, false);
      const data = parser.extractAll();
      
      // Print extracted data
      console.log('📋 Extracted Data:');
      Object.entries(data).forEach(([key, value]) => {
        if (key === 'foundSections') return;
        if (value !== undefined && value !== null && value !== '') {
          console.log(`  ${key}: ${JSON.stringify(value)}`);
        }
      });
      
      console.log('\n🔍 Found Sections:');
      data.foundSections?.forEach(section => {
        console.log(`  - ${section}`);
      });
    }

    // Now let's look at the actual HTML structure of one file
    console.log('\n\n📝 Detailed HTML Structure Analysis:');
    console.log('Looking for specific patterns in first file...\n');
    
    const firstFile = htmlFiles[0];
    const htmlPath = path.join(htmlDir, firstFile);
    const html = await fs.readFile(htmlPath, 'utf-8');
    const $ = cheerio.load(html);
    
    // Find all unique class names
    const classNames = new Set<string>();
    $('[class]').each((_, elem) => {
      const classes = $(elem).attr('class')?.split(' ') || [];
      classes.forEach(c => classNames.add(c));
    });
    
    console.log('🏷️  Unique CSS classes found:');
    const relevantClasses = Array.from(classNames)
      .filter(c => c.includes('prof') || c.includes('box') || c.includes('row') || 
                   c.includes('td') || c.includes('info') || c.includes('bio') ||
                   c.includes('record') || c.includes('stat'))
      .sort();
    
    relevantClasses.forEach(c => console.log(`  .${c}`));
    
    console.log('\n🏷️  Table structures:');
    $('table').each((i, table) => {
      const $table = $(table);
      const className = $table.attr('class') || 'no-class';
      const rows = $table.find('tr').length;
      console.log(`  Table ${i + 1}: class="${className}", rows=${rows}`);
      
      // Show first row structure
      const firstRow = $table.find('tr').first();
      const cells = firstRow.find('td, th').map((_, cell) => {
        const $cell = $(cell);
        return `${cell.tagName}(${$cell.attr('class') || ''}): "${$cell.text().trim().substring(0, 20)}..."`;
      }).get();
      
      if (cells.length) {
        console.log(`    First row: ${cells.join(' | ')}`);
      }
    });

  } catch (error) {
    console.error('❌ Error:', error);
  }
}

// Run the analysis
analyzeHtmlFiles().catch(console.error);