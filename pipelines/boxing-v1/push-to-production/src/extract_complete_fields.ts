#!/usr/bin/env tsx

import * as cheerio from 'cheerio';
import * as fs from 'fs/promises';
import * as path from 'path';
import { v4 as uuidv4 } from 'uuid';

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

interface CompleteBoxerData {
  // Required ID field
  id: string;
  
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
  weight?: string;  // MISSING - need to extract
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
  
  // Fights - with ALL details
  fights?: FightRecord[];
  
  // Metadata
  created_at?: string;
  updated_at?: string;
}

class CompleteFieldExtractor {
  private $: cheerio.CheerioAPI;
  private html: string;

  constructor(html: string) {
    this.$ = cheerio.load(html);
    this.html = html;
  }

  parse(boxrecId: string): CompleteBoxerData {
    const $ = this.$;
    
    const data: CompleteBoxerData = {
      id: uuidv4(), // Generate UUID for id field
      boxrec_id: boxrecId,
      boxrec_url: `https://boxrec.com/en/box-pro/${boxrecId}`,
      slug: this.generateSlug(boxrecId),
      full_name: this.extractName(),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };

    // Extract all data sections with enhanced methods
    this.extractAllBasicInfo(data);
    this.extractAllPhysicalAttributes(data);
    this.extractAllLocationInfo(data);
    this.extractAllMedia(data);
    this.extractAllTeamInfo(data);
    this.extractAllProfessionalRecord(data);
    this.extractAllAmateurRecord(data);
    this.extractAllFightDetails(data);
    this.extractAllBioSections(data);
    
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

  private extractAllBasicInfo(data: CompleteBoxerData) {
    const $ = this.$;
    
    // Enhanced row label extraction
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = ($label.find('b').text().trim() || $label.text().trim()).toLowerCase().replace(':', '');
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText) {
        case 'birth name':
        case 'real name':
        case 'aka':
          data.birth_name = value;
          break;
        case 'nickname':
        case 'alias':
        case 'also known as':
          data.nickname = value;
          break;
        case 'sex':
        case 'gender':
          data.gender = value.toLowerCase();
          break;
        case 'born':
        case 'date of birth':
        case 'birth date':
          data.date_of_birth = this.formatDate(value);
          break;
      }
    });

    // Look in other places for birth name/nickname
    const fullText = this.html;
    
    // Birth name patterns
    const birthNameMatch = fullText.match(/birth\s*name[:\s]+([^<\n]+)/i) ||
                          fullText.match(/real\s*name[:\s]+([^<\n]+)/i) ||
                          fullText.match(/born\s+as[:\s]+([^<\n]+)/i);
    if (birthNameMatch && !data.birth_name) {
      data.birth_name = birthNameMatch[1].trim();
    }

    // Nickname patterns
    const nicknameMatch = fullText.match(/nickname[:\s]+([^<\n]+)/i) ||
                         fullText.match(/known\s+as[:\s]+([^<\n]+)/i) ||
                         fullText.match(/\"([^\"]+)\"/);
    if (nicknameMatch && !data.nickname) {
      data.nickname = nicknameMatch[1].trim();
    }
  }

  private extractAllPhysicalAttributes(data: CompleteBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = ($label.find('b').text().trim() || $label.text().trim()).toLowerCase().replace(':', '');
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText) {
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
        case 'weight lbs':
        case 'last weight':
        case 'fighting weight':
          data.weight = value;
          break;
      }
    });
    
    // Look for weight in different places
    const weightPatterns = [
      /(\d+)\s*lbs?\b/i,
      /(\d+)\s*pounds?\b/i,
      /weight[:\s]*(\d+)\s*lbs?/i,
      /(\d+\.?\d*)\s*kg/i
    ];
    
    for (const pattern of weightPatterns) {
      if (!data.weight) {
        const match = this.html.match(pattern);
        if (match) {
          data.weight = match[0];
          break;
        }
      }
    }

    // Handle stance detection from cells
    $('td:contains("orthodox"), td:contains("southpaw")').each((_, elem) => {
      const text = $(elem).text().trim().toLowerCase();
      if ((text === 'orthodox' || text === 'southpaw') && !data.stance) {
        data.stance = text;
      }
    });
  }

  private extractAllLocationInfo(data: CompleteBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = ($label.find('b').text().trim() || $label.text().trim()).toLowerCase().replace(':', '');
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText) {
        case 'birth place':
        case 'birthplace':
        case 'born in':
        case 'place of birth':
          data.birth_place = value;
          break;
        case 'residence':
        case 'lives in':
        case 'resides':
          data.residence = value;
          break;
        case 'nationality':
        case 'country':
          data.nationality = value;
          break;
      }
    });
  }

  private extractAllMedia(data: CompleteBoxerData) {
    const $ = this.$;
    
    // Extract profile photo with priority
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
    
    // Extract wiki URL
    const wikiLink = $('a[href*="wiki"]').first().attr('href');
    if (wikiLink) {
      data.boxrec_wiki_url = wikiLink.startsWith('/') ? 
        `https://boxrec.com${wikiLink}` : wikiLink;
    }
    
    // Extract comprehensive bio
    const bio = $('.profileBio, .bio, [class*="bio"]').text().trim();
    if (bio && bio.length > 10) {
      data.bio = bio;
    }
  }

  private extractAllTeamInfo(data: CompleteBoxerData) {
    const $ = this.$;
    
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = ($label.find('b').text().trim() || $label.text().trim()).toLowerCase().replace(':', '');
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText) {
        case 'promoter':
        case 'promoted by':
          data.promoter = value;
          break;
        case 'trainer':
        case 'trained by':
          data.trainer = value;
          break;
        case 'manager':
        case 'managed by':
          data.manager = value;
          break;
        case 'gym':
        case 'training gym':
        case 'trains at':
          data.gym = value;
          break;
      }
    });
  }

  private extractAllProfessionalRecord(data: CompleteBoxerData) {
    const $ = this.$;
    
    // Enhanced WLD table extraction
    const $wldTable = $('.profileWLD');
    if ($wldTable.length) {
      const $row = $wldTable.find('tr').first();
      const cells = $row.find('td');
      
      if (cells.length >= 3) {
        data.pro_wins = parseInt(cells.eq(0).text().trim()) || 0;
        data.pro_losses = parseInt(cells.eq(1).text().trim()) || 0;
        data.pro_draws = parseInt(cells.eq(2).text().trim()) || 0;
      }
      
      // Enhanced KO extraction
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
    
    // Extract other professional info with more patterns
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = ($label.find('b').text().trim() || $label.text().trim()).toLowerCase().replace(':', '');
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText) {
        case 'division':
        case 'weight class':
        case 'fights at':
          data.pro_division = value;
          break;
        case 'status':
        case 'current status':
          data.pro_status = value.toLowerCase();
          break;
        case 'debut':
        case 'pro debut':
        case 'first fight':
          data.pro_debut_date = this.formatDate(value);
          break;
        case 'bouts':
        case 'total bouts':
        case 'fights':
          data.pro_total_bouts = parseInt(value) || 0;
          break;
        case 'rounds':
        case 'total rounds':
          data.pro_total_rounds = parseInt(value) || 0;
          break;
      }
    });
  }

  private extractAllAmateurRecord(data: CompleteBoxerData) {
    const $ = this.$;
    
    // Enhanced amateur record extraction
    $('.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const labelText = ($label.find('b').text().trim() || $label.text().trim()).toLowerCase().replace(':', '');
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (!labelText || !value) return;
      
      switch(labelText) {
        case 'amateur record':
        case 'amateur':
        case 'amateur career':
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
        case 'amateur first fight':
          data.amateur_debut_date = this.formatDate(value);
          break;
        case 'amateur division':
        case 'amateur weight class':
          data.amateur_division = value;
          break;
      }
    });
    
    // Look for Olympic/amateur info in text
    $('td:contains("Olympic"), td:contains("Olympics"), td:contains("amateur")').each((_, elem) => {
      const text = $(elem).text();
      
      // Enhanced amateur record patterns
      const amateurMatch = text.match(/amateur.*?(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?/i) ||
                          text.match(/(\d+)\s*-\s*(\d+)(?:\s*-\s*(\d+))?\s*amateur/i);
      
      if (amateurMatch && !data.amateur_wins) {
        data.amateur_wins = parseInt(amateurMatch[1]) || 0;
        data.amateur_losses = parseInt(amateurMatch[2]) || 0;
        data.amateur_draws = parseInt(amateurMatch[3]) || 0;
        data.amateur_total_bouts = (data.amateur_wins || 0) + (data.amateur_losses || 0) + (data.amateur_draws || 0);
        data.amateur_status = 'retired';
        
        // Extract amateur KO info
        const koMatch = text.match(/(\d+)\s*kos?/i);
        if (koMatch) {
          data.amateur_wins_by_knockout = parseInt(koMatch[1]) || 0;
        }
      }
      
      // Olympic medal indicates amateur career
      if (text.toLowerCase().includes('olympic') && 
          (text.toLowerCase().includes('bronze') || text.toLowerCase().includes('gold') || text.toLowerCase().includes('silver'))) {
        if (!data.amateur_status) data.amateur_status = 'retired';
        if (!data.amateur_division) data.amateur_division = 'various';
      }
    });
  }

  private extractAllFightDetails(data: CompleteBoxerData) {
    const $ = this.$;
    const fights: FightRecord[] = [];
    
    // Find the main fights table (dataTable)
    $('.dataTable tbody tr').each((i, row) => {
      const $row = $(row);
      const cells = $row.find('td');
      
      if (cells.length >= 6) {
        const dateCell = cells.eq(0).text().trim();
        const opponentCell = cells.eq(2);
        const opponentLink = opponentCell.find('a');
        const opponentName = opponentLink.length ? opponentLink.text().trim() : opponentCell.text().trim();
        
        // Extract opponent record from the w-l-d cell
        const recordCell = cells.eq(3);
        const wSpan = recordCell.find('.textWon').text().trim();
        const lSpan = recordCell.find('.textLost').text().trim();
        const dSpan = recordCell.find('.textDraw').text().trim();
        const opponentRecord = `${wSpan}-${lSpan}-${dSpan}`;
        
        // Extract venue from location cell
        const venueCell = cells.eq(5);
        const venueText = venueCell.text().trim();
        
        // Extract result
        const resultCell = cells.eq(6);
        const resultDiv = resultCell.find('.boutResult');
        const result = resultDiv.text().trim();
        
        // Extract event link
        const eventLink = $row.find('a[href*="/en/event/"]').attr('href');
        
        if (dateCell && opponentName && result) {
          const fight: FightRecord = {
            bout_date: this.formatDate(dateCell),
            opponent_name: opponentName,
            opponent_record: opponentRecord !== '--' ? opponentRecord : undefined,
            venue_name: venueText || undefined,
            result: this.parseResult(result),
            num_rounds_scheduled: 12, // Default
            title_fight: venueText.toLowerCase().includes('title') || 
                         $row.text().toLowerCase().includes('title'),
            event_page_link: eventLink ? `https://boxrec.com${eventLink}` : undefined
          };
          
          // Try to extract more details from the row
          const rowText = $row.text();
          
          // Look for referee info (usually in event pages, but sometimes in row)
          const refMatch = rowText.match(/ref[:\s]*([^,\n]+)/i);
          if (refMatch) {
            fight.referee_name = refMatch[1].trim();
          }
          
          // Look for round info
          const roundMatch = rowText.match(/round\s*(\d+)/i) || rowText.match(/R(\d+)/i);
          if (roundMatch) {
            fight.result_round = parseInt(roundMatch[1]);
          }
          
          // Determine result method from context
          if (result.toLowerCase().includes('ko')) {
            fight.result_method = 'ko';
          } else if (result.toLowerCase().includes('tko')) {
            fight.result_method = 'tko';
          } else if (result.toLowerCase().includes('ud') || result.toLowerCase().includes('decision')) {
            fight.result_method = 'decision';
          }
          
          fights.push(fight);
        }
      }
    });
    
    if (fights.length > 0) {
      data.fights = fights.slice(0, 15); // Most recent 15 fights
    }
  }

  private extractAllBioSections(data: CompleteBoxerData) {
    // Enhanced bio section extraction
    if (data.bio && data.bio.length > 50) {
      data.bioSections = {
        professionalCareer: {
          title: "Professional Career",
          content: data.bio
        }
      };
      
      // Look for specific bio sections in the HTML
      const bioText = data.bio;
      
      // Try to identify different sections
      if (bioText.toLowerCase().includes('early') || bioText.toLowerCase().includes('childhood')) {
        const earlyMatch = bioText.match(/(.*?(?:early|childhood|youth).*?)(?=\n\n|\.|$)/is);
        if (earlyMatch) {
          data.bioSections.earlyLife = {
            title: "Early Life",
            content: earlyMatch[1].trim()
          };
        }
      }
      
      if (bioText.toLowerCase().includes('style') || bioText.toLowerCase().includes('technique')) {
        const styleMatch = bioText.match(/(.*?(?:style|technique|fighting).*?)(?=\n\n|\.|$)/is);
        if (styleMatch) {
          data.bioSections.boxingStyle = {
            title: "Boxing Style",
            content: styleMatch[1].trim()
          };
        }
      }
    }
  }

  private formatDate(dateStr: string): string | undefined {
    if (!dateStr) return undefined;
    
    // Clean up the date string
    let cleaned = dateStr.replace(/[^\w\s-\/]/g, '').trim();
    
    // Try various date formats
    const patterns = [
      /(\w+)\s+(\d{2})/,  // "Dec 81" -> "1981-12-XX"
      /(\d{1,2})\/(\d{1,2})\/(\d{2,4})/,  // MM/DD/YY or MM/DD/YYYY
      /(\d{4})-(\d{2})-(\d{2})/,  // YYYY-MM-DD
      /(\d{1,2})\s+(\w+)\s+(\d{4})/,  // DD Month YYYY
    ];
    
    const monthMap: Record<string, string> = {
      'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04',
      'may': '05', 'jun': '06', 'jul': '07', 'aug': '08',
      'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    };
    
    for (const pattern of patterns) {
      const match = cleaned.match(pattern);
      if (match) {
        if (pattern.source.includes('w+.*d{2}')) {
          // "Dec 81" format
          const month = monthMap[match[1].toLowerCase().substring(0, 3)];
          const year = match[2].length === 2 ? 
            (parseInt(match[2]) > 50 ? `19${match[2]}` : `20${match[2]}`) : 
            match[2];
          if (month) return `${year}-${month}-01`;
        }
        break;
      }
    }
    
    return cleaned || undefined;
  }

  private parseResult(resultStr: string): string | undefined {
    if (!resultStr) return undefined;
    const lower = resultStr.toLowerCase();
    if (lower.includes('w') || lower.includes('win')) return 'win';
    if (lower.includes('l') || lower.includes('loss')) return 'loss';
    if (lower.includes('d') || lower.includes('draw')) return 'draw';
    return resultStr;
  }
}

async function extractCompleteFields() {
  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  const outputFile = 'complete_boxer_fields.json';
  
  try {
    console.log('🥊 Extracting COMPLETE boxer data with ALL fields...\n');
    
    const files = await fs.readdir(htmlDir);
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f.startsWith('en_box-pro')); // Process ALL files
    
    console.log(`📊 Processing ${htmlFiles.length} HTML files...\n`);
    
    const extractedBoxers: CompleteBoxerData[] = [];
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
        
        const parser = new CompleteFieldExtractor(html);
        const data = parser.parse(boxrecId);
        
        extractedBoxers.push(data);
        successCount++;
        
        // Show progress every 1000 boxers
        if (successCount % 1000 === 0) {
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
    
    // Field coverage analysis
    console.log('\n📊 Field Coverage Analysis:');
    
    const fieldCoverage = {
      id: extractedBoxers.filter(b => b.id).length,
      weight: extractedBoxers.filter(b => b.weight).length,
      birth_name: extractedBoxers.filter(b => b.birth_name).length,
      nickname: extractedBoxers.filter(b => b.nickname).length,
      opponent_record: extractedBoxers.filter(b => b.fights?.some(f => f.opponent_record)).length,
      venue_name: extractedBoxers.filter(b => b.fights?.some(f => f.venue_name)).length,
      referee_name: extractedBoxers.filter(b => b.fights?.some(f => f.referee_name)).length,
      amateur_wins: extractedBoxers.filter(b => b.amateur_wins !== undefined).length,
      bioSections: extractedBoxers.filter(b => b.bioSections && Object.keys(b.bioSections).length > 0).length,
    };
    
    Object.entries(fieldCoverage).forEach(([field, count]) => {
      const percentage = ((count / successCount) * 100).toFixed(1);
      console.log(`   ${field}: ${count}/${successCount} (${percentage}%)`);
    });
    
    // Show sample with all fields
    console.log('\n📋 Sample complete data:\n');
    const sample = extractedBoxers[0];
    if (sample) {
      console.log(`🥊 ${sample.full_name} (ID: ${sample.id})`);
      console.log(`   BoxRec ID: ${sample.boxrec_id}`);
      console.log(`   Weight: ${sample.weight || 'N/A'}`);
      console.log(`   Birth Name: ${sample.birth_name || 'N/A'}`);
      console.log(`   Nickname: ${sample.nickname || 'N/A'}`);
      console.log(`   Record: ${sample.pro_wins}-${sample.pro_losses}-${sample.pro_draws || 0}`);
      console.log(`   Amateur Record: ${sample.amateur_wins || 0}-${sample.amateur_losses || 0}-${sample.amateur_draws || 0}`);
      console.log(`   Fights: ${sample.fights?.length || 0} detailed fights`);
      
      if (sample.fights && sample.fights[0]) {
        const fight = sample.fights[0];
        console.log(`   Sample Fight: vs ${fight.opponent_name} (${fight.opponent_record}) at ${fight.venue_name}`);
      }
    }
    
  } catch (error) {
    console.error('❌ Fatal error:', error);
  }
}

// Run the complete field extraction
extractCompleteFields().catch(console.error);