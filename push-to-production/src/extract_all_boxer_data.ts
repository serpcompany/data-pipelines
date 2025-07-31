#!/usr/bin/env tsx

import * as cheerio from 'cheerio';
import * as fs from 'fs/promises';
import * as path from 'path';

interface FightRecord {
  bout_date?: string;
  opponent_name?: string;
  opponent_weight?: string;
  opponent_record?: string;
  venue_name?: string;
  referee_name?: string;
  judge_1_name?: string;
  judge_1_score?: string;
  judge_2_name?: string;
  judge_2_score?: string;
  judge_3_name?: string;
  judge_3_score?: string;
  num_rounds_scheduled?: number;
  result?: string;
  result_method?: string;
  result_round?: number;
  event_page_link?: string;
  bout_page_link?: string;
  scorecards_page_link?: string;
  title_fight?: boolean;
}

interface ComprehensiveBoxerData {
  // IDs and URLs
  boxrec_id: string;
  boxrec_url: string;
  boxrec_wiki_url?: string;
  slug: string;
  
  // Basic Info
  full_name: string;
  birth_name?: string;
  nickname?: string;
  gender?: string;
  
  // Physical
  height?: string;
  reach?: string;
  weight?: string;
  stance?: string;
  
  // Birth/Location
  date_of_birth?: string;
  birth_place?: string;
  residence?: string;
  nationality?: string;
  
  // Media
  image_url?: string;
  bio?: string;
  bioSections?: {
    earlyLife?: { title: string; content: string };
    professionalCareer?: { title: string; content: string };
    notableFights?: { title: string; content: string };
    boxingStyle?: { title: string; content: string };
    legacy?: { title: string; content: string };
    personalLife?: { title: string; content: string };
  };
  
  // Team
  promoter?: string;
  trainer?: string;
  manager?: string;
  gym?: string;
  
  // Professional Career
  pro_debut_date?: string;
  pro_division?: string;
  pro_wins?: number;
  pro_wins_by_knockout?: number;
  pro_losses?: number;
  pro_losses_by_knockout?: number;
  pro_draws?: number;
  pro_status?: string;
  pro_total_bouts?: number;
  pro_total_rounds?: number;
  
  // Amateur Career
  amateur_debut_date?: string;
  amateur_division?: string;
  amateur_wins?: number;
  amateur_wins_by_knockout?: number;
  amateur_losses?: number;
  amateur_losses_by_knockout?: number;
  amateur_draws?: number;
  amateur_status?: string;
  amateur_total_bouts?: number;
  amateur_total_rounds?: number;
  
  // Fights
  fights?: FightRecord[];
  
  // Metadata
  created_at?: string;
  updated_at?: string;
}

class ComprehensiveBoxRecParser {
  private $: cheerio.CheerioAPI;

  constructor(html: string) {
    this.$ = cheerio.load(html);
  }

  parse(boxrecId: string): ComprehensiveBoxerData {
    const $ = this.$;
    
    const data: ComprehensiveBoxerData = {
      boxrec_id: boxrecId,
      boxrec_url: `https://boxrec.com/en/box-pro/${boxrecId}`,
      slug: this.generateSlug(boxrecId),
      full_name: this.extractName(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // Extract all data sections
    this.extractBasicInfo(data);
    this.extractPhysicalAttributes(data);
    this.extractLocationInfo(data);
    this.extractMedia(data);
    this.extractTeamInfo(data);
    this.extractProfessionalRecord(data);
    this.extractAmateurRecord(data);
    this.extractFights(data);
    this.extractBioSections(data);
    
    return data;
  }

  private extractName(): string {
    const $ = this.$;
    const titleText = $('title').text().trim();
    return titleText.replace('BoxRec:', '').replace('- BoxRec', '').trim() || 'Unknown';
  }

  private generateSlug(boxrecId: string): string {
    const name = this.extractName();
    return name.toLowerCase()
      .replace(/[^a-z0-9\s-]/g, '')
      .replace(/\s+/g, '-')
      .replace(/-+/g, '-')
      .trim() + '-' + boxrecId;
  }

  private extractBasicInfo(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = $label.find('b').text().trim() || $label.text().trim();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText.toLowerCase().replace(':', '')) {
        case 'birth name':
        case 'real name':
          data.birth_name = value;
          break;
        case 'nickname':
        case 'alias':
          data.nickname = value;
          break;
        case 'sex':
        case 'gender':
          data.gender = value.toLowerCase();
          break;
        case 'born':
        case 'date of birth':
          data.date_of_birth = this.parseDateOfBirth(value);
          break;
      }
    });
  }

  private extractPhysicalAttributes(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = $label.find('b').text().trim() || $label.text().trim();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText.toLowerCase().replace(':', '')) {
        case 'height':
          data.height = value;
          break;
        case 'reach':
          data.reach = value;
          break;
        case 'stance':
          data.stance = value.toLowerCase();
          break;
        case 'weight':
          data.weight = value;
          break;
      }
    });
    
    // Handle stance detection from cells
    $('td:contains("orthodox"), td:contains("southpaw")').each((_, elem) => {
      const text = $(elem).text().trim().toLowerCase();
      if ((text === 'orthodox' || text === 'southpaw') && !data.stance) {
        data.stance = text;
      }
    });
  }

  private extractLocationInfo(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = $label.find('b').text().trim() || $label.text().trim();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText.toLowerCase().replace(':', '')) {
        case 'birth place':
        case 'birthplace':
          data.birth_place = value;
          break;
        case 'residence':
          data.residence = value;
          break;
        case 'nationality':
          data.nationality = value;
          break;
      }
    });
  }

  private extractMedia(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    // Extract profile photo
    const profileImg = $('.profileTablePhoto img.photoBorder, img.photoBorder').first().attr('src');
    if (profileImg) {
      data.image_url = profileImg.startsWith('/') ? 
        `https://boxrec.com${profileImg}` : profileImg;
    }
    
    // Fallback to OpenGraph image
    if (!data.image_url) {
      $('meta').each((_, elem) => {
        const $meta = $(elem);
        const property = $meta.attr('property');
        const content = $meta.attr('content');
        
        if (property === 'og:image' && content) {
          data.image_url = content;
        }
      });
    }
    
    // Extract wiki URL if available
    const wikiLink = $('a[href*="wiki"]').first().attr('href');
    if (wikiLink) {
      data.boxrec_wiki_url = wikiLink.startsWith('/') ? 
        `https://boxrec.com${wikiLink}` : wikiLink;
    }
    
    // Extract basic bio
    const bio = $('.profileBio, .bio, [class*="bio"]').text().trim();
    if (bio && bio.length > 10) {
      data.bio = bio;
    }
  }

  private extractTeamInfo(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = $label.find('b').text().trim() || $label.text().trim();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText.toLowerCase().replace(':', '')) {
        case 'promoter':
          data.promoter = value;
          break;
        case 'trainer':
          data.trainer = value;
          break;
        case 'manager':
          data.manager = value;
          break;
        case 'gym':
          data.gym = value;
          break;
      }
    });
  }

  private extractProfessionalRecord(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    // Extract from WLD table
    const $wldTable = $('.profileWLD');
    if ($wldTable.length) {
      const $row = $wldTable.find('tr').first();
      const cells = $row.find('td');
      
      if (cells.length >= 3) {
        data.pro_wins = parseInt(cells.eq(0).text().trim()) || 0;
        data.pro_losses = parseInt(cells.eq(1).text().trim()) || 0;
        data.pro_draws = parseInt(cells.eq(2).text().trim()) || 0;
      }
      
      // Extract KO information
      const $koRow = $wldTable.find('tr').eq(1);
      if ($koRow.length) {
        const koText = $koRow.text();
        const koMatches = koText.match(/(\d+)\s*KOs?/g);
        if (koMatches && koMatches.length > 0) {
          data.pro_wins_by_knockout = parseInt(koMatches[0].match(/(\d+)/)?.[1] || '0');
          if (koMatches.length > 1) {
            data.pro_losses_by_knockout = parseInt(koMatches[1].match(/(\d+)/)?.[1] || '0');
          }
        }
      }
    }
    
    // Extract other professional info
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = $label.find('b').text().trim() || $label.text().trim();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText.toLowerCase().replace(':', '')) {
        case 'division':
          data.pro_division = value;
          break;
        case 'status':
          data.pro_status = value.toLowerCase();
          break;
        case 'debut':
        case 'pro debut':
          data.pro_debut_date = this.parseDate(value);
          break;
        case 'bouts':
          data.pro_total_bouts = parseInt(value) || 0;
          break;
        case 'rounds':
          data.pro_total_rounds = parseInt(value) || 0;
          break;
      }
    });
  }

  private extractAmateurRecord(data: ComprehensiveBoxerData) {
    const $ = this.$;
    
    // Look for amateur record in row labels first
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = $label.find('b').text().trim() || $label.text().trim();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText.toLowerCase().replace(':', '')) {
        case 'amateur record':
        case 'amateur':
          const recordMatch = value.match(/(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?/);
          if (recordMatch) {
            data.amateur_wins = parseInt(recordMatch[1]) || 0;
            data.amateur_losses = parseInt(recordMatch[2]) || 0;
            data.amateur_draws = parseInt(recordMatch[3]) || 0;
            data.amateur_total_bouts = (data.amateur_wins || 0) + (data.amateur_losses || 0) + (data.amateur_draws || 0);
            data.amateur_status = 'retired';
          }
          break;
        case 'amateur debut':
          data.amateur_debut_date = this.parseDate(value);
          break;
        case 'amateur division':
          data.amateur_division = value;
          break;
      }
    });
    
    // Look for amateur record in text content
    $('td:contains("amateur"), div:contains("amateur")').each((_, elem) => {
      const text = $(elem).text();
      
      // Look for patterns like "Amateur record: 84-8" or "84-8 amateur"
      const amateurMatch = text.match(/amateur.*?(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?/i) ||
                          text.match(/(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?\s*amateur/i);
      
      if (amateurMatch && !data.amateur_wins) {
        data.amateur_wins = parseInt(amateurMatch[1]) || 0;
        data.amateur_losses = parseInt(amateurMatch[2]) || 0;
        data.amateur_draws = parseInt(amateurMatch[3]) || 0;
        data.amateur_total_bouts = (data.amateur_wins || 0) + (data.amateur_losses || 0) + (data.amateur_draws || 0);
        data.amateur_status = 'retired';
        
        // Try to extract KO info for amateur
        const koMatch = text.match(/(\d+)\s*kos?/i);
        if (koMatch) {
          data.amateur_wins_by_knockout = parseInt(koMatch[1]) || 0;
        }
      }
    });
    
    // Look for Olympic information which indicates amateur career
    $('td:contains("Olympic"), td:contains("Olympics")').each((_, elem) => {
      const text = $(elem).text();
      if (text.toLowerCase().includes('bronze') || text.toLowerCase().includes('gold') || text.toLowerCase().includes('silver')) {
        if (!data.amateur_status) data.amateur_status = 'retired';
        if (!data.amateur_division) data.amateur_division = 'various';
      }
    });
  }

  private extractFights(data: ComprehensiveBoxerData) {
    const $ = this.$;
    const fights: FightRecord[] = [];
    
    // Find the bouts table (more comprehensive search)
    $('table').each((_, table) => {
      const $table = $(table);
      const headers = $table.find('th, td').first().parent().find('th, td').map((_, cell) => $(cell).text().toLowerCase()).get();
      
      // Check if this looks like a fights table
      if (headers.some(h => h.includes('date') || h.includes('opponent') || h.includes('result'))) {
        $table.find('tr').each((i, row) => {
          if (i === 0) return; // Skip header
          
          const $row = $(row);
          const cells = $row.find('td').map((_, td) => $(td).text().trim()).get();
          
          if (cells.length >= 4) {
            const dateCell = cells[0] || '';
            const opponentCell = cells[2] || cells[1] || '';
            const resultCell = cells[6] || cells[5] || cells[4] || cells[3] || '';
            const venueCell = cells[9] || cells[8] || cells[7] || '';
            
            // Only add if we have meaningful data
            if (dateCell && opponentCell && (resultCell.includes('W') || resultCell.includes('L') || resultCell.includes('D'))) {
              const fight: FightRecord = {
                bout_date: this.parseDate(dateCell),
                opponent_name: this.cleanOpponentName(opponentCell),
                result: this.parseResult(resultCell),
                result_method: this.parseResultMethod(cells[7] || cells[4]),
                result_round: this.parseRound(cells[8] || cells[5]),
                venue_name: venueCell || undefined,
                num_rounds_scheduled: this.parseScheduledRounds(cells.join(' ')),
                title_fight: (cells.join(' ')).toLowerCase().includes('title')
              };
              
              // Extract event and bout links
              const eventLink = $row.find('a[href*="event"]').first().attr('href');
              if (eventLink) {
                fight.event_page_link = eventLink.startsWith('/') ? 
                  `https://boxrec.com${eventLink}` : eventLink;
              }
              
              const boutLink = $row.find('a[href*="bout"]').first().attr('href');
              if (boutLink) {
                fight.bout_page_link = boutLink.startsWith('/') ? 
                  `https://boxrec.com${boutLink}` : boutLink;
                fight.scorecards_page_link = fight.bout_page_link + '/scorecards';
              }
              
              fights.push(fight);
            }
          }
        });
      }
    });
    
    if (fights.length > 0) {
      data.fights = fights.slice(0, 15); // Limit to most recent 15 fights
    }
  }

  private extractBioSections(data: ComprehensiveBoxerData) {
    // This would require more detailed HTML parsing
    // For now, we'll use the basic bio we already extracted
    if (data.bio) {
      data.bioSections = {
        professionalCareer: {
          title: "Professional Career",
          content: data.bio
        }
      };
    }
  }

  private parseDateOfBirth(dateStr: string): string | undefined {
    // Parse various date formats from BoxRec
    const cleaned = dateStr.replace(/[^\d-\/\s]/g, '').trim();
    if (cleaned.match(/^\d{4}-\d{2}-\d{2}$/)) {
      return cleaned;
    }
    // Add more date parsing logic as needed
    return cleaned || undefined;
  }

  private parseDate(dateStr: string): string | undefined {
    if (!dateStr) return undefined;
    const cleaned = dateStr.replace(/[^\d-\/\s]/g, '').trim();
    return cleaned || undefined;
  }

  private parseResult(resultStr: string): string | undefined {
    if (!resultStr) return undefined;
    const lower = resultStr.toLowerCase();
    if (lower.includes('w')) return 'win';
    if (lower.includes('l')) return 'loss';
    if (lower.includes('d')) return 'draw';
    return resultStr;
  }

  private parseResultMethod(methodStr: string): string | undefined {
    if (!methodStr) return undefined;
    const lower = methodStr.toLowerCase();
    if (lower.includes('ko')) return 'ko';
    if (lower.includes('tko')) return 'tko';
    if (lower.includes('decision')) return 'decision';
    if (lower.includes('ud')) return 'decision';
    if (lower.includes('md')) return 'decision';
    if (lower.includes('sd')) return 'decision';
    return methodStr;
  }

  private cleanOpponentName(name: string): string {
    return name.replace(/\n/g, ' ').replace(/\s+/g, ' ').trim();
  }

  private parseRound(roundStr: string): number | undefined {
    if (!roundStr) return undefined;
    const match = roundStr.match(/(\d+)/);
    return match ? parseInt(match[1]) : undefined;
  }

  private parseScheduledRounds(text: string): number | undefined {
    const match = text.match(/(\d+)\s*rounds?\s*scheduled/i);
    return match ? parseInt(match[1]) : 12; // Default to 12 if not specified
  }
}

async function extractComprehensiveBoxerData() {
  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  const outputFile = 'comprehensive_boxer_data.json';
  
  try {
    console.log('🥊 Extracting comprehensive boxer data from HTML files...\n');
    
    const files = await fs.readdir(htmlDir);
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f.startsWith('en_box-pro'))
      .slice(0, 100); // Process exactly 100 files
    
    console.log(`📊 Processing ${htmlFiles.length} HTML files...\n`);
    
    const extractedBoxers: ComprehensiveBoxerData[] = [];
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
        if (html.includes('Please login to continue') || 
            html.includes('Login to BoxRec') ||
            html.includes('<title>BoxRec: Login</title>')) {
          loginPageCount++;
          continue;
        }
        
        const parser = new ComprehensiveBoxRecParser(html);
        const data = parser.parse(boxrecId);
        
        extractedBoxers.push(data);
        successCount++;
        
        // Show progress every 50 boxers
        if (successCount % 50 === 0) {
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
    
    // Show sample data
    console.log('\n📋 Sample comprehensive data:\n');
    const sample = extractedBoxers[0];
    if (sample) {
      console.log(`🥊 ${sample.full_name} (ID: ${sample.boxrec_id})`);
      console.log(`   Record: ${sample.pro_wins}-${sample.pro_losses}-${sample.pro_draws || 0} (${sample.pro_wins_by_knockout || 0} KOs)`);
      console.log(`   Nationality: ${sample.nationality}`);
      console.log(`   Division: ${sample.pro_division}`);
      console.log(`   Fights data: ${sample.fights?.length || 0} fights`);
      console.log(`   Bio sections: ${Object.keys(sample.bioSections || {}).length} sections`);
    }
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

// Run the extraction
extractComprehensiveBoxerData().catch(console.error);