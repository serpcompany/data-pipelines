#!/usr/bin/env tsx

import { drizzle } from 'drizzle-orm/postgres-js';
import postgres from 'postgres';
import * as dotenv from 'dotenv';
import { sql } from 'drizzle-orm';
import * as cheerio from 'cheerio';
import { v4 as uuidv4 } from 'uuid';
import * as fs from 'fs/promises';
import * as path from 'path';

// Load environment
dotenv.config({ path: '../.env' });

interface BoxerRecord {
  wins: number;
  winsByKO: number;
  losses: number;
  lossesByKO: number;
  draws: number;
}

interface ParsedBoxer {
  id: string;
  boxrecId: string;
  boxrecUrl: string;
  slug: string;
  fullName: string;
  birthName?: string;
  nickname?: string;
  gender?: string;
  avatarImage?: string;
  residence?: string;
  birthPlace?: string;
  dateOfBirth?: string;
  nationality?: string;
  height?: string;
  reach?: string;
  weight?: string;
  stance?: string;
  bio?: string;
  proRecord?: BoxerRecord;
  proDivision?: string;
  proStatus?: string;
  proDebutDate?: string;
  htmlFile?: string;
}

class BoxRecHTMLParser {
  private $: cheerio.CheerioAPI;

  constructor(html: string) {
    this.$ = cheerio.load(html);
  }

  parse(boxrecId: string, boxrecUrl: string): ParsedBoxer {
    const $ = this.$;
    
    // Extract name from title tag (more reliable than h1)
    const titleText = $('title').text().trim();
    const fullName = titleText.replace('BoxRec:', '').trim() || 'Unknown';
    
    // Generate slug if not provided
    const slug = fullName.toLowerCase()
      .replace(/[^a-z0-9]+/g, '-')
      .replace(/^-|-$/g, '');

    // Extract image
    const avatarImage = $('.photoBorder').attr('src') || 
                       $('.profileTablePhoto img').attr('src') ||
                       $('img[alt*="' + fullName + '"]').first().attr('src');

    // Extract basic info from table rows
    const info: Record<string, string> = {};
    
    // Extract info from rowLabel/value pairs
    $('td.rowLabel').each((_, elem) => {
      const $label = $(elem);
      const label = $label.find('b').text().trim().toLowerCase() || 
                   $label.text().trim().toLowerCase();
      const $valueTd = $label.next('td');
      const value = $valueTd.text().trim();
      
      if (label && value && !value.includes('star-icon')) {
        info[label] = value;
      }
    });

    // Extract record from profileWLD table structure
    const wins = $('.profileWLD .bgW').text().trim() || '0';
    const losses = $('.profileWLD .bgL').text().trim() || '0';
    const draws = $('.profileWLD .bgD').text().trim() || '0';
    
    // Extract KOs
    const winsKOText = $('.profileWLD .textWon').text() || '';
    const lossesKOText = $('.profileWLD .textLost').text() || '';
    
    const winsKOMatch = winsKOText.match(/(\d+)\s*KOs?/i);
    const lossesKOMatch = lossesKOText.match(/(\d+)\s*KOs?/i);
    
    const proRecord: BoxerRecord = {
      wins: parseInt(wins) || 0,
      losses: parseInt(losses) || 0,
      draws: parseInt(draws) || 0,
      winsByKO: winsKOMatch ? parseInt(winsKOMatch[1]) : 0,
      lossesByKO: lossesKOMatch ? parseInt(lossesKOMatch[1]) : 0,
    };

    // Extract bio
    const bio = $('.profileBio').text().trim() || 
               $('div.bio').text().trim() || 
               undefined;

    return {
      id: uuidv4(),
      boxrecId,
      boxrecUrl,
      slug,
      fullName,
      birthName: info['birth name'] || undefined,
      nickname: info['alias'] || info['nickname'] || undefined,
      gender: info['sex'] || this.inferGender(fullName),
      avatarImage: avatarImage || undefined,
      residence: info['residence'] || undefined,
      birthPlace: info['birth place'] || info['birthplace'] || undefined,
      dateOfBirth: info['born'] || info['date of birth'] || undefined,
      nationality: info['nationality'] || undefined,
      height: info['height'] || undefined,
      reach: info['reach'] || undefined,
      weight: info['weight'] || undefined,
      stance: info['stance']?.toLowerCase() || undefined,
      bio,
      proRecord,
      proDivision: info['division'] || undefined,
      proStatus: info['status']?.toLowerCase() || undefined,
      proDebutDate: info['debut'] || undefined,
    };
  }


  private inferGender(name: string): string {
    // Simple inference - would need improvement for production
    // Check for common female boxing indicators
    const femaleIndicators = ['amanda', 'katie', 'claressa', 'laila'];
    const nameLower = name.toLowerCase();
    
    if (femaleIndicators.some(indicator => nameLower.includes(indicator))) {
      return 'female';
    }
    
    return 'male'; // Default assumption
  }
}

async function parseHtmlFilesToDb() {
  console.log('🔄 Parsing HTML files to database...\n');

  const connectionString = `postgresql://${process.env.POSTGRES_USER}:${process.env.POSTGRES_PASSWORD}@${process.env.POSTGRES_HOST}:${process.env.POSTGRES_PORT}/${process.env.POSTGRES_DEFAULT_DB}`;
  
  const client = postgres(connectionString);
  const db = drizzle(client);

  const htmlDir = '../boxrec_scraper/data/raw/boxrec_html';
  
  try {
    // Get list of HTML files - only English box-pro files for now
    const files = await fs.readdir(htmlDir);
    const htmlFiles = files
      .filter(f => f.endsWith('.html') && f.startsWith('en_box-pro'))
      .slice(0, 10); // Start with 10 English files
    
    console.log(`📊 Found ${files.length} files, processing first ${htmlFiles.length} HTML files\n`);

    let successCount = 0;
    let errorCount = 0;
    let skippedCount = 0;

    for (const filename of htmlFiles) {
      try {
        // Parse filename to get boxer ID
        // Format: en_box-pro_628407.html
        const match = filename.match(/box-pro_(\d+)\.html$/);
        if (!match) {
          console.log(`⚠️  Skipping ${filename} - doesn't match expected format`);
          skippedCount++;
          continue;
        }

        const boxrecId = match[1];
        const boxrecUrl = `https://boxrec.com/en/box-pro/${boxrecId}`;
        
        // Check if already processed
        const existing = await db.execute(sql`
          SELECT id FROM "data-pipelines-staging".boxers 
          WHERE boxrec_id = ${boxrecId}
        `);
        
        if (existing.rows && existing.rows.length > 0) {
          console.log(`⏭️  Skipping ${boxrecId} - already in database`);
          skippedCount++;
          continue;
        }

        // Read and parse HTML
        const htmlPath = path.join(htmlDir, filename);
        const html = await fs.readFile(htmlPath, 'utf-8');
        
        console.log(`Parsing ${filename}...`);
        
        const parser = new BoxRecHTMLParser(html);
        const parsed = parser.parse(boxrecId, boxrecUrl);
        parsed.htmlFile = html;

        // Log parsed data to debug
        console.log(`Parsed data for ${boxrecId}:`, {
          fullName: parsed.fullName,
          slug: parsed.slug,
          hasRecord: !!parsed.proRecord,
          recordWins: parsed.proRecord?.wins
        });

        // Skip login pages
        if (parsed.fullName.toLowerCase().includes('login') || 
            parsed.fullName.toLowerCase().includes('please')) {
          console.log(`⚠️  Skipping ${filename} - appears to be a login page`);
          skippedCount++;
          continue;
        }

        // Insert into database
        await db.execute(sql`
          INSERT INTO "data-pipelines-staging".boxers (
            id,
            boxrec_id,
            boxrec_url,
            slug,
            full_name,
            birth_name,
            nickname,
            gender,
            avatar_image,
            residence,
            birth_place,
            date_of_birth,
            nationality,
            height,
            reach,
            weight,
            stance,
            bio,
            pro_wins,
            pro_wins_by_knockout,
            pro_losses,
            pro_losses_by_knockout,
            pro_draws,
            pro_division,
            pro_status,
            pro_debut_date,
            pro_total_bouts,
            html_file,
            html_parsed_at,
            created_at,
            updated_at
          ) VALUES (
            ${parsed.id},
            ${parsed.boxrecId},
            ${parsed.boxrecUrl},
            ${parsed.slug},
            ${parsed.fullName},
            ${parsed.birthName},
            ${parsed.nickname},
            ${parsed.gender},
            ${parsed.avatarImage},
            ${parsed.residence},
            ${parsed.birthPlace},
            ${parsed.dateOfBirth},
            ${parsed.nationality},
            ${parsed.height},
            ${parsed.reach},
            ${parsed.weight},
            ${parsed.stance},
            ${parsed.bio},
            ${parsed.proRecord?.wins || 0},
            ${parsed.proRecord?.winsByKO || 0},
            ${parsed.proRecord?.losses || 0},
            ${parsed.proRecord?.lossesByKO || 0},
            ${parsed.proRecord?.draws || 0},
            ${parsed.proDivision},
            ${parsed.proStatus},
            ${parsed.proDebutDate},
            ${(parsed.proRecord?.wins || 0) + (parsed.proRecord?.losses || 0) + (parsed.proRecord?.draws || 0)},
            ${parsed.htmlFile},
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP,
            CURRENT_TIMESTAMP
          )
        `);

        console.log(`✅ Inserted: ${parsed.fullName} (${parsed.proRecord?.wins}-${parsed.proRecord?.losses}-${parsed.proRecord?.draws})`);
        successCount++;

      } catch (error) {
        console.error(`❌ Error processing ${filename}:`, error);
        errorCount++;
      }
    }

    console.log(`\n📈 Parsing complete:`);
    console.log(`✅ Success: ${successCount}`);
    console.log(`⏭️  Skipped: ${skippedCount}`);
    console.log(`❌ Errors: ${errorCount}`);

    // Show sample of parsed data
    const sample = await db.execute(sql`
      SELECT 
        full_name,
        pro_wins,
        pro_losses,
        pro_draws,
        nationality,
        pro_division
      FROM "data-pipelines-staging".boxers
      WHERE html_parsed_at IS NOT NULL
      ORDER BY created_at DESC
      LIMIT 5
    `);

    console.log('\n📋 Sample parsed boxers:');
    if (sample.rows && sample.rows.length > 0) {
      sample.rows.forEach(boxer => {
        console.log(`- ${boxer.full_name}: ${boxer.pro_wins}-${boxer.pro_losses}-${boxer.pro_draws}, ${boxer.nationality || 'N/A'}, ${boxer.pro_division || 'N/A'}`);
      });
    } else {
      console.log('No boxers parsed yet.');
    }

  } catch (error) {
    console.error('❌ Error:', error);
    throw error;
  } finally {
    await client.end();
  }
}

// Run the parser
parseHtmlFilesToDb().catch(console.error);